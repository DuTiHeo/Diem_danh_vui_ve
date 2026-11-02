import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import deferred
from .base import Base


class SubjectFolder(Base):
    __tablename__ = "subject_folders"
    __table_args__ = (
        UniqueConstraint(
            "lecturer_id",
            "folder_name",
            "semester",
            name="uq_lecturer_folder_semester",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lecturer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    folder_name = Column(String(255), nullable=False)
    semester = Column(String(100), nullable=False, default="HK1 2026-2027")
    color_tag = Column(String(50), nullable=True, default="#003366")
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subject_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    course_code = Column(String(100), nullable=False)
    course_name = Column(String(255), nullable=False)
    class_section = Column(String(100), nullable=True)
    room_name = Column(String(100), nullable=True)
    date_range_text = Column(String(255), nullable=True)
    schedule_text = Column(String(500), nullable=True)
    footer_date_text = Column(String(255), nullable=True)
    building_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="SET NULL"),
        nullable=True,
    )
    lecturer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Chapter 5.1 SYSTEM_DESIGN.md: Out-of-line PostgreSQL BYTEA TOAST with deferred loading
    template_binary = deferred(Column(LargeBinary, nullable=True))
    template_filename = Column(String(255), nullable=True)
    total_sessions = Column(Integer, nullable=False, default=15)
    created_at = Column(DateTime, default=datetime.utcnow)


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("course_id", "student_id", name="uq_enrollment_course_student"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ordinal_number = Column(Integer, nullable=False)  # TT trong file Excel gốc (1..N)
    sheet_name = Column(String(100), nullable=True)
    excel_row_index = Column(Integer, nullable=True)
    note = Column(String(500), nullable=True)
