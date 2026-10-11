from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.api import deps
from app.db.session import get_db
from app.models.users import User, UserRole
from app.models.students import Student
from app.models.attendance import QRToken, AttendanceSession, SessionStatus, AttendanceRecord, AttendanceStatus, AttendanceMethod
from app.models.buildings import Building
from app.models.courses import Course, Enrollment
from app.schemas.api_models import AttendanceRequestQR, AttendanceRequestPIN, AttendanceStatusResponse, ManualOverrideRequest
from app.services.geo_service import is_within_geofence
from app.services.websocket_manager import manager

router = APIRouter()

async def validate_pin_and_geo(db: AsyncSession, pin_code: str, lat: float, lon: float, acc: float) -> tuple[QRToken, AttendanceSession]:
    res_t = await db.execute(select(QRToken).where(QRToken.pin_code == pin_code))
    token = res_t.scalar_one_or_none()
    
    if not token:
        raise HTTPException(status_code=404, detail="Mã PIN không tồn tại")
    if token.is_revoked or token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Mã PIN đã hết hạn. Vui lòng nhìn màn chiếu lấy mã mới!")
        
    res_s = await db.execute(select(AttendanceSession).where(AttendanceSession.id == token.session_id))
    session = res_s.scalar_one_or_none()
    
    if not session or session.status != SessionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Buổi điểm danh này đang đóng")

    # Kiểm tra Geo
    if session.building_id:
        res_b = await db.execute(select(Building).where(Building.id == session.building_id))
        building = res_b.scalar_one_or_none()
        if building:
            valid, dist = is_within_geofence(lat, lon, building.latitude, building.longitude, building.radius_meters, acc)
            if not valid:
                raise HTTPException(status_code=400, detail=f"Vị trí quá xa (Cách {int(dist)}m). Hãy di chuyển lại gần giảng đường {building.code}")
    
    return token, session

@router.post("/qr", response_model=AttendanceStatusResponse)
async def submit_attendance_qr(
    req: AttendanceRequestQR,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Chỉ sinh viên mới được quét QR")
        
    token, session = await validate_pin_and_geo(db, req.pin_code, req.latitude, req.longitude, req.accuracy)
    
    # Tìm student ID
    res_st = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = res_st.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Hồ sơ sinh viên không tồn tại")
        
    # Check enrollment
    res_en = await db.execute(select(Enrollment).where(Enrollment.course_id == session.course_id, Enrollment.student_id == student.id))
    if not res_en.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Bạn không có trong danh sách lớp này")
        
    # Ktra duplicate
    res_r = await db.execute(select(AttendanceRecord).where(AttendanceRecord.session_id == session.id, AttendanceRecord.student_id == student.id))
    record = res_r.scalar_one_or_none()
    
    if record and record.status == AttendanceStatus.ATTENDED:
        raise HTTPException(status_code=400, detail="Bạn đã điểm danh thành công trước đó")
        
    if not record:
        record = AttendanceRecord(
            session_id=session.id,
            student_id=student.id,
        )
        db.add(record)
        
    record.status = AttendanceStatus.ATTENDED
    record.marked_at = datetime.utcnow()
    record.method = AttendanceMethod.QR
    record.latitude = req.latitude
    record.longitude = req.longitude
    
    await db.commit()
    
    # Báo WS
    await manager.broadcast_to_session(str(session.id), {
        "event": "ATTENDANCE_MARKED",
        "student_id": str(student.id),
        "marked_at": record.marked_at.isoformat()
    })
    
    return AttendanceStatusResponse(success=True, message="Điểm danh thành công", student_name=student.full_name)


@router.post("/pin", response_model=AttendanceStatusResponse)
async def submit_attendance_pin(
    req: AttendanceRequestPIN,
    db: AsyncSession = Depends(get_db)
):
    # Dành cho Public (không login)
    token, session = await validate_pin_and_geo(db, req.pin_code, req.latitude, req.longitude, req.accuracy)
    
    res_st = await db.execute(select(Student).where(Student.student_code == req.student_code))
    student = res_st.scalar_one_or_none()
    
    if not student or student.full_name.lower() != req.full_name.strip().lower():
        raise HTTPException(status_code=400, detail="Mã SV hoặc Họ tên không chính xác")
        
    # Check enrollment
    res_en = await db.execute(select(Enrollment).where(Enrollment.course_id == session.course_id, Enrollment.student_id == student.id))
    if not res_en.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Sinh viên không có trong danh sách lớp")
        
    # Ktra duplicate
    res_r = await db.execute(select(AttendanceRecord).where(AttendanceRecord.session_id == session.id, AttendanceRecord.student_id == student.id))
    record = res_r.scalar_one_or_none()
    
    if record and record.status == AttendanceStatus.ATTENDED:
        raise HTTPException(status_code=400, detail="Bạn đã điểm danh thành công trước đó")
        
    if not record:
        record = AttendanceRecord(session_id=session.id, student_id=student.id)
        db.add(record)
        
    record.status = AttendanceStatus.ATTENDED
    record.marked_at = datetime.utcnow()
    record.method = AttendanceMethod.PIN_ANONYMOUS
    record.latitude = req.latitude
    record.longitude = req.longitude
    
    await db.commit()
    
    await manager.broadcast_to_session(str(session.id), {
        "event": "ATTENDANCE_MARKED",
        "student_id": str(student.id),
        "marked_at": record.marked_at.isoformat()
    })
    
    return AttendanceStatusResponse(success=True, message="Điểm danh PIN thành công", student_name=student.full_name)

@router.post("/manual")
async def manual_override(
    req: ManualOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    res_r = await db.execute(select(AttendanceRecord).where(AttendanceRecord.session_id == req.session_id, AttendanceRecord.student_id == req.student_id))
    record = res_r.scalar_one_or_none()
    
    if not record:
        record = AttendanceRecord(session_id=req.session_id, student_id=req.student_id)
        db.add(record)
        
    record.status = AttendanceStatus[req.status]
    record.marked_at = datetime.utcnow()
    record.method = AttendanceMethod.MANUAL
    record.updated_by_lecturer_id = current_user.id
    
    await db.commit()
    
    await manager.broadcast_to_session(req.session_id, {
        "event": "ATTENDANCE_MANUAL_OVERRIDE",
        "student_id": req.student_id,
        "status": req.status
    })
    
    return {"success": True}

