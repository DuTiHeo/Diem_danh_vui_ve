from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class StudentBase(BaseModel):
    student_code: str
    full_name: str

class CourseCreateResponse(BaseModel):
    id: str
    course_name: str
    room_name: str
    total_students: int
    total_sessions: int

class OpenSessionRequest(BaseModel):
    session_number: int
    building_id: Optional[str] = None
    duration_seconds: int = 60

class SessionResponse(BaseModel):
    id: str
    course_id: str
    session_number: int
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

class QRResponse(BaseModel):
    session_id: str
    pin_code: str
    expires_in_seconds: int

class AttendanceRequestQR(BaseModel):
    pin_code: str
    latitude: float
    longitude: float
    accuracy: float = 0.0

class AttendanceRequestPIN(BaseModel):
    pin_code: str
    student_code: str
    full_name: str
    latitude: float
    longitude: float
    accuracy: float = 0.0

class ManualOverrideRequest(BaseModel):
    session_id: str
    student_id: str
    status: str # ATTENDED or ABSENT

class AttendanceStatusResponse(BaseModel):
    success: bool
    message: str
    student_name: Optional[str] = None

