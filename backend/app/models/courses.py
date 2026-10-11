import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_code = Column(String(50), nullable=False)
    course_name = Column(String(255), nullable=False)
    class_section = Column(String(50), nullable=True)
    room_name = Column(String(50), nullable=True)
    building_id = Column(UUID(as_uuid=True), ForeignKey("buildings.id"), nullable=True)
    lecturer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    excel_template_path = Column(String(500), nullable=True)
    total_sessions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    ordinal_number = Column(Integer, nullable=False) # STT trong file Excel

