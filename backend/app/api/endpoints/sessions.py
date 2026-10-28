from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from app.api import deps
from app.db.session import get_db
from app.models.users import User
from app.models.courses import Course, Enrollment
from app.models.students import Student
from app.models.buildings import Building
from app.models.attendance import AttendanceSession, SessionStatus, QRToken, AttendanceRecord, AttendanceStatus
from app.schemas.api_models import SessionResponse, QRResponse, OpenSessionRequest
from app.services.qr_service import generate_pin_and_hash, get_expiration_time
from app.services.websocket_manager import manager

router = APIRouter()

@router.post("/{course_id}/open", response_model=QRResponse)
async def open_session(
    course_id: str,
    req: OpenSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    # Ktra course
    res_c = await db.execute(select(Course).where(Course.id == course_id, Course.lecturer_id == current_user.id))
    course = res_c.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Không tìm thấy môn học")

    building_id = req.building_id or (str(course.building_id) if course.building_id else None)

    # Tạo Session nếu chưa có
    res_s = await db.execute(select(AttendanceSession).where(
        AttendanceSession.course_id == course_id, 
        AttendanceSession.session_number == req.session_number
    ))
    session = res_s.scalar_one_or_none()
    
    if not session:
        session = AttendanceSession(
            course_id=course_id,
            session_number=req.session_number,
            building_id=building_id,
            status=SessionStatus.OPEN,
            started_at=datetime.utcnow()
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
    elif session.status == SessionStatus.CLOSED:
        # Re-open if requested
        session.status = SessionStatus.OPEN
        session.started_at = datetime.utcnow()
        if building_id:
            session.building_id = building_id
        await db.commit()
    else:
        session.status = SessionStatus.OPEN
        if building_id:
            session.building_id = building_id
        await db.commit()

    # Hủy token cũ nếu có
    await db.execute(
        update(QRToken)
        .where(QRToken.session_id == session.id)
        .values(is_revoked=True)
    )
    
    # Sinh token mới
    pin_code, token_hash = generate_pin_and_hash()
    duration = req.duration_seconds if req.duration_seconds > 0 else 60
    qr_token = QRToken(
        session_id=session.id,
        token_hash=token_hash,
        pin_code=pin_code,
        expires_at=get_expiration_time(duration)
    )
    db.add(qr_token)
    await db.commit()

    return QRResponse(
        session_id=str(session.id),
        pin_code=pin_code,
        expires_in_seconds=duration
    )

@router.get("/{session_id}")
async def get_session_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    res_s = await db.execute(select(AttendanceSession).where(AttendanceSession.id == session_id))
    session = res_s.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên điểm danh")

    # Course info
    res_c = await db.execute(select(Course).where(Course.id == session.course_id))
    course = res_c.scalar_one_or_none()

    # Building info
    building_data = None
    if session.building_id:
        res_b = await db.execute(select(Building).where(Building.id == session.building_id))
        b = res_b.scalar_one_or_none()
        if b:
            building_data = {
                "id": str(b.id),
                "code": b.code,
                "name": b.name,
                "latitude": b.latitude,
                "longitude": b.longitude,
                "radius_meters": b.radius_meters
            }

    # Active QR Token
    res_t = await db.execute(
        select(QRToken)
        .where(QRToken.session_id == session.id, QRToken.is_revoked == False)
        .order_by(QRToken.created_at.desc())
    )
    token = res_t.scalars().first()
    
    pin_code = token.pin_code if token else None
    remaining_seconds = 0
    if token and token.expires_at:
        diff = (token.expires_at - datetime.utcnow()).total_seconds()
        remaining_seconds = max(0, int(diff))

    # Students & attendance records
    query_st = (
        select(Student, Enrollment.ordinal_number)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .where(Enrollment.course_id == session.course_id)
        .order_by(Enrollment.ordinal_number)
    )
    res_st = await db.execute(query_st)
    students_raw = res_st.all()

    res_rec = await db.execute(select(AttendanceRecord).where(AttendanceRecord.session_id == session.id))
    records_by_student = {str(r.student_id): r for r in res_rec.scalars().all()}

    student_list = []
    attended_count = 0
    for st, ordinal in students_raw:
        st_id = str(st.id)
        rec = records_by_student.get(st_id)
        status = rec.status.value if rec else ("ABSENT" if session.status == SessionStatus.CLOSED else "PENDING")
        if status == "ATTENDED":
            attended_count += 1
            
        student_list.append({
            "id": st_id,
            "ordinal": ordinal,
            "student_code": st.student_code,
            "name": st.full_name,
            "status": status,
            "time": rec.marked_at.strftime("%H:%M:%S") if (rec and rec.marked_at) else None,
            "method": rec.method.value if (rec and rec.method) else None,
            "distance_meters": rec.distance_meters if rec else None
        })

    return {
        "id": str(session.id),
        "course_id": str(course.id) if course else None,
        "course_name": course.course_name if course else "Môn học",
        "room_name": course.room_name if course else "Chưa rõ phòng",
        "session_number": session.session_number,
        "status": session.status.value,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "pin_code": pin_code,
        "remaining_seconds": remaining_seconds,
        "building": building_data,
        "total_students": len(student_list),
        "attended_count": attended_count,
        "students": student_list
    }

@router.post("/{session_id}/refresh-qr", response_model=QRResponse)
async def refresh_qr(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    res_s = await db.execute(select(AttendanceSession).where(AttendanceSession.id == session_id))
    session = res_s.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên điểm danh")
    if session.status != SessionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Phiên điểm danh không mở")

    # Revoke old tokens
    await db.execute(
        update(QRToken)
        .where(QRToken.session_id == session.id)
        .values(is_revoked=True)
    )

    pin_code, token_hash = generate_pin_and_hash()
    qr_token = QRToken(
        session_id=session.id,
        token_hash=token_hash,
        pin_code=pin_code,
        expires_at=get_expiration_time(60)
    )
    db.add(qr_token)
    await db.commit()

    # Broadcast to projector
    await manager.broadcast_to_session(str(session.id), {
        "event": "QR_REFRESHED",
        "pin_code": pin_code,
        "expires_in_seconds": 60
    })

    return QRResponse(
        session_id=str(session.id),
        pin_code=pin_code,
        expires_in_seconds=60
    )

@router.get("/qr/{pin_code}")
async def get_session_by_pin(
    pin_code: str,
    db: AsyncSession = Depends(get_db)
):
    res_t = await db.execute(select(QRToken).where(QRToken.pin_code == pin_code))
    token = res_t.scalar_one_or_none()
    if not token or token.is_revoked or token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=404, detail="Mã PIN không hợp lệ hoặc đã hết hạn")

    res_s = await db.execute(select(AttendanceSession).where(AttendanceSession.id == token.session_id))
    session = res_s.scalar_one_or_none()
    if not session or session.status != SessionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Phiên điểm danh đã đóng")

    res_c = await db.execute(select(Course).where(Course.id == session.course_id))
    course = res_c.scalar_one_or_none()

    building_name = None
    if session.building_id:
        res_b = await db.execute(select(Building).where(Building.id == session.building_id))
        b = res_b.scalar_one_or_none()
        if b:
            building_name = b.name

    diff = (token.expires_at - datetime.utcnow()).total_seconds()

    return {
        "session_id": str(session.id),
        "pin_code": pin_code,
        "course_name": course.course_name if course else "Môn học",
        "session_number": session.session_number,
        "room_name": course.room_name if course else "",
        "building_name": building_name,
        "expires_in_seconds": max(0, int(diff))
    }

@router.post("/{session_id}/close")
async def close_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_lecturer)
):
    res_s = await db.execute(select(AttendanceSession).where(AttendanceSession.id == session_id))
    session = res_s.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy session")
        
    session.status = SessionStatus.CLOSED
    session.ended_at = datetime.utcnow()
    
    # Hủy QR
    await db.execute(
        update(QRToken)
        .where(QRToken.session_id == session.id)
        .values(is_revoked=True)
    )
    
    # Những SV chưa có record -> Vắng
    res_e = await db.execute(select(Enrollment).where(Enrollment.course_id == session.course_id))
    enrollments = res_e.scalars().all()
    
    res_r = await db.execute(select(AttendanceRecord).where(AttendanceRecord.session_id == session.id))
    records = {str(r.student_id): r for r in res_r.scalars().all()}
    
    for e in enrollments:
        if str(e.student_id) not in records:
            db.add(AttendanceRecord(
                session_id=session.id,
                student_id=e.student_id,
                status=AttendanceStatus.ABSENT,
                marked_at=datetime.utcnow()
            ))
            
    await db.commit()
    
    # Báo WS
    await manager.broadcast_to_session(str(session.id), {"event": "SESSION_CLOSED"})
    return {"message": "Session closed"}

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Lecturer ping/pong or settings
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

