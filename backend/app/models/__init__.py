from .base import Base
from .users import User, UserRole
from .students import Student
from .buildings import Building
from .courses import Course, Enrollment
from .attendance import AttendanceSession, QRToken, AttendanceRecord, AuditLog, SessionStatus, AttendanceStatus, AttendanceMethod

# This __init__.py ensures all models are loaded before Alembic reads Base.metadata

