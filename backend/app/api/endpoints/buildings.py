from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.models.buildings import Building

router = APIRouter()

DEFAULT_BUILDINGS = [
    {"code": "A2", "name": "Tòa nhà Thế Kỷ (Nhà A2)", "latitude": 20.99965, "longitude": 105.84315, "radius_meters": 80},
    {"code": "A1", "name": "Giảng đường A1", "latitude": 20.99930, "longitude": 105.84350, "radius_meters": 70},
    {"code": "B", "name": "Giảng đường B", "latitude": 20.99990, "longitude": 105.84270, "radius_meters": 70},
    {"code": "C", "name": "Giảng đường C", "latitude": 21.00010, "longitude": 105.84310, "radius_meters": 70},
    {"code": "D", "name": "Giảng đường D - D2", "latitude": 20.99920, "longitude": 105.84230, "radius_meters": 70},
]

async def ensure_buildings_seeded(db: AsyncSession):
    result = await db.execute(select(Building))
    existing = result.scalars().all()
    if not existing:
        for b in DEFAULT_BUILDINGS:
            db.add(Building(
                id=uuid.uuid4(),
                code=b["code"],
                name=b["name"],
                latitude=b["latitude"],
                longitude=b["longitude"],
                radius_meters=b["radius_meters"]
            ))
        await db.commit()

@router.get("/")
async def get_buildings(db: AsyncSession = Depends(get_db)):
    await ensure_buildings_seeded(db)
    result = await db.execute(select(Building).order_by(Building.code))
    buildings = result.scalars().all()
    return [
        {
            "id": str(b.id),
            "code": b.code,
            "name": b.name,
            "latitude": b.latitude,
            "longitude": b.longitude,
            "radius_meters": b.radius_meters
        }
        for b in buildings
    ]
