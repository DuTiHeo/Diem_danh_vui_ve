from fastapi import APIRouter
from app.api.endpoints import auth, courses, sessions, attendance, buildings, system

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(buildings.router, prefix="/buildings", tags=["buildings"])
api_router.include_router(system.router, prefix="/system", tags=["system"])

