import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_code = Column(String(20), unique=True, index=True, nullable=False)
    last_name = Column(String(150), nullable=True, default="")
    first_name = Column(String(100), nullable=True, default="")
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(String(50), nullable=True, default="")
    admin_class = Column(String(100), nullable=True, default="")
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
