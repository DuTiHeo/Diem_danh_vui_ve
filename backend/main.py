from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_router import api_router
from app.core.config import settings
from app.core.redis import get_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Redis connection (or fallback) on startup
    await get_redis()
    yield
    await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Nền tảng điểm danh thông minh đa tầng NEU (QR/PIN 60s + GPS Geofencing + Sóng cận siêu âm 18.1kHz-20.5kHz)",
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "instance_id": settings.BACKEND_INSTANCE_ID,
        "version": settings.VERSION,
        "message": "NEU Attendance Stateless Backend is running!",
    }
