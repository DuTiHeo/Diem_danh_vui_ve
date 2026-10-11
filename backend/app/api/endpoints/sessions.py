from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from app.api import deps
from app.db.session import get_db
from app.models.users import User
from app.models.courses import Course, Enrollment
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
            building_id=req.building_id,
            status=SessionStatus.OPEN,
            started_at=datetime.utcnow()
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
    elif session.status == SessionStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Buổi học này đã đóng")
    else:
        session.status = SessionStatus.OPEN
        if req.building_id:
            session.building_id = req.building_id
        await db.commit()

    # Hủy token cũ nếu có
    await db.execute(
        update(QRToken)
        .where(QRToken.session_id == session.id)
        .values(is_revoked=True)
    )
    
    # Sinh token mới
    pin_code, token_hash = generate_pin_and_hash()
    qr_token = QRToken(
        session_id=session.id,
        token_hash=token_hash,
        pin_code=pin_code,
        expires_at=get_expiration_time(req.duration_seconds)
    )
    db.add(qr_token)
    await db.commit()

    return QRResponse(
        session_id=str(session.id),
        pin_code=pin_code,
        expires_in_seconds=req.duration_seconds
    )

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
    # Get all enrollments for course
    res_e = await db.execute(select(Enrollment).where(Enrollment.course_id == session.course_id))
    enrollments = res_e.scalars().all()
    
    # Get current records
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
    await manager.broadcast_to_session(session_id, {"event": "SESSION_CLOSED"})
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

