from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Configure Connection Pool per Chapter 6.1 SYSTEM_DESIGN.md
_engine_kwargs = {"echo": False}
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(
        pool_size=settings.DB_POOL_SIZE,          # 20 connections per backend instance
        max_overflow=settings.DB_MAX_OVERFLOW,    # +30 burst connections at peak
        pool_timeout=settings.DB_POOL_TIMEOUT,    # 10s wait timeout
        pool_recycle=settings.DB_POOL_RECYCLE,    # 1800s (30 mins) recycle
        pool_pre_ping=True,                       # Verify connection health before checkout
    )

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
