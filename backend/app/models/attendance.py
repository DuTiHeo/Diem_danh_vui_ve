import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class SessionStatus(str, enum.Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class AttendanceStatus(str, enum.Enum):
    ATTENDED = "ATTENDED"
    ABSENT = "ABSENT"
    PENDING_APPROVAL = "PENDING_APPROVAL"


class AttendanceMethod(str, enum.Enum):
    QR = "QR"
    PIN_ANONYMOUS = "PIN_ANONYMOUS"
    MANUAL = "MANUAL"
    EXCEL_IMPORT = "EXCEL_IMPORT"


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    __table_args__ = (
        UniqueConstraint("course_id", "session_number", name="uq_session_course_number"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_number = Column(Integer, nullable=False)  # 1..15
    building_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING, nullable=False)
    require_audio = Column(Boolean, default=True, nullable=False)
    audio_tolerance_hz = Column(Integer, default=50, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)


class QRToken(Base):
    __tablename__ = "qr_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(String(255), nullable=False)
    pin_code = Column(String(10), unique=True, index=True, nullable=False)  # 6 digits
    audio_freq_hz = Column(Integer, nullable=False, default=18500)  # 18100..20500 Hz
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(Enum(AttendanceStatus), nullable=False)
    marked_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    gps_accuracy_meters = Column(Float, nullable=True)
    distance_meters = Column(Float, nullable=True)
    detected_freq_hz = Column(Integer, nullable=True)
    audio_verified = Column(Boolean, default=False, nullable=False)
    method = Column(Enum(AttendanceMethod), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    updated_by_lecturer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(255), nullable=False)
    details = Column(String(2000), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
