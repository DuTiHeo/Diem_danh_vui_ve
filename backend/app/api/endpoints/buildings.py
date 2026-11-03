import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api import deps
from app.db.session import get_db
from app.models.buildings import Building
from app.models.courses import Course
from app.models.attendance import AttendanceSession
from app.models.users import User

router = APIRouter()

DEFAULT_BUILDINGS = [
    {
        "code": "A1",
        "name": "Giảng đường A1",
        "latitude": 21.000094581220793,
        "longitude": 105.84227593099624,
        "radius_meters": 70,
    },
    {
        "code": "A2",
        "name": "Tòa nhà Thế Kỷ (Nhà A2)",
        "latitude": 21.000058291768326,
        "longitude": 105.84306011591576,
        "radius_meters": 80,
    },
    {
        "code": "B",
        "name": "Giảng đường B",
        "latitude": 20.999749735252724,
        "longitude": 105.84412482073593,
        "radius_meters": 70,
    },
    {
        "code": "C",
        "name": "Giảng đường C",
        "latitude": 20.999111799668633,
        "longitude": 105.84468592549185,
        "radius_meters": 70,
    },
    {
        "code": "D",
        "name": "Giảng đường D",
        "latitude": 20.999314228600127,
        "longitude": 105.84415071163696,
        "radius_meters": 70,
    },
    {
        "code": "D2",
        "name": "Giảng đường D2",
        "latitude": 20.99934101490285,
        "longitude": 105.84381200744511,
        "radius_meters": 70,
    },
]


class BuildingCreateRequest(BaseModel):
    code: str
    name: str
    latitude: float
    longitude: float
    radius_meters: int = 70
    is_active: bool = True


class BuildingUpdateRequest(BaseModel):
    code: str | None = None
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_meters: int | None = None
    is_active: bool | None = None


def _serialize_building(b: Building) -> dict:
    return {
        "id": str(b.id),
        "code": b.code,
        "name": b.name,
        "latitude": b.latitude,
        "longitude": b.longitude,
        "radius_meters": b.radius_meters,
        "is_active": bool(b.is_active),
    }


async def ensure_buildings_seeded(db: AsyncSession):
    result = await db.execute(select(Building))
    existing = result.scalars().all()
    if not existing:
        for b in DEFAULT_BUILDINGS:
            db.add(
                Building(
                    id=uuid.uuid4(),
                    code=b["code"],
                    name=b["name"],
                    latitude=b["latitude"],
                    longitude=b["longitude"],
                    radius_meters=b["radius_meters"],
                    is_active=True,
                )
            )
        await db.commit()
    else:
        existing_by_code = {b.code.upper(): b for b in existing}
        if "D2" not in existing_by_code and len(existing_by_code) == 5:
            d_bldg = existing_by_code.get("D")
            if d_bldg and d_bldg.name == "Giảng đường D - D2":
                d_bldg.name = "Giảng đường D"
                db.add(
                    Building(
                        id=uuid.uuid4(),
                        code="D2",
                        name="Giảng đường D2",
                        latitude=20.99905,
                        longitude=105.84210,
                        radius_meters=70,
                        is_active=True,
                    )
                )
                await db.commit()


@router.get("/")
async def get_buildings(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    await ensure_buildings_seeded(db)
    stmt = select(Building).order_by(Building.code)
    if not include_inactive:
        stmt = stmt.where(Building.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    buildings = result.scalars().all()
    return [_serialize_building(b) for b in buildings]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_building(
    req: BuildingCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    """
    UC19: Quản trị viên thêm mới tòa nhà giảng đường NEU.
    """
    code_clean = req.code.strip().upper()
    if not code_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã tòa nhà không được để trống.",
        )

    res_dup = await db.execute(select(Building).where(Building.code == code_clean))
    if res_dup.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tòa nhà có mã '{code_clean}' đã tồn tại.",
        )

    bldg = Building(
        id=uuid.uuid4(),
        code=code_clean,
        name=req.name.strip(),
        latitude=req.latitude,
        longitude=req.longitude,
        radius_meters=req.radius_meters,
        is_active=req.is_active,
    )
    db.add(bldg)
    await db.commit()
    await db.refresh(bldg)
    return _serialize_building(bldg)


@router.put("/{building_id}")
async def update_building(
    building_id: str,
    req: BuildingUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    """
    UC19: Quản trị viên cập nhật tọa độ tâm (latitude, longitude), bán kính radius_meters hoặc trạng thái is_active.
    """
    try:
        b_uuid = uuid.UUID(str(building_id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Không tìm thấy tòa nhà.")

    res = await db.execute(select(Building).where(Building.id == b_uuid))
    bldg = res.scalar_one_or_none()
    if not bldg:
        raise HTTPException(status_code=404, detail="Không tìm thấy tòa nhà.")

    if req.code is not None:
        new_code = req.code.strip().upper()
        if new_code != bldg.code:
            res_dup = await db.execute(
                select(Building).where(Building.code == new_code)
            )
            if res_dup.scalar_one_or_none():
                raise HTTPException(
                    status_code=400, detail=f"Mã tòa nhà '{new_code}' đã tồn tại."
                )
            bldg.code = new_code

    if req.name is not None:
        bldg.name = req.name.strip()
    if req.latitude is not None:
        bldg.latitude = req.latitude
    if req.longitude is not None:
        bldg.longitude = req.longitude
    if req.radius_meters is not None:
        bldg.radius_meters = req.radius_meters
    if req.is_active is not None:
        bldg.is_active = req.is_active

    await db.commit()
    await db.refresh(bldg)
    return _serialize_building(bldg)


@router.delete("/{building_id}")
async def delete_building(
    building_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    """
    UC19 & EX-16: Chặn xóa cứng tòa nhà đang được gắn với lớp học phần hoặc phiên điểm danh.
    """
    try:
        b_uuid = uuid.UUID(str(building_id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Không tìm thấy tòa nhà.")

    res = await db.execute(select(Building).where(Building.id == b_uuid))
    bldg = res.scalar_one_or_none()
    if not bldg:
        raise HTTPException(status_code=404, detail="Không tìm thấy tòa nhà.")

    res_course_cnt = await db.execute(
        select(func.count(Course.id)).where(Course.building_id == b_uuid)
    )
    course_cnt = res_course_cnt.scalar() or 0

    res_sess_cnt = await db.execute(
        select(func.count(AttendanceSession.id)).where(
            AttendanceSession.building_id == b_uuid
        )
    )
    sess_cnt = res_sess_cnt.scalar() or 0

    if course_cnt > 0 or sess_cnt > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa cứng tòa nhà đang được gắn với lớp học phần hoặc phiên điểm danh. Chỉ cho phép chuyển trạng thái is_active = false hoặc cập nhật tọa độ (EX-16).",
        )

    await db.delete(bldg)
    await db.commit()
    return {
        "success": True,
        "message": f"Đã xóa tòa nhà {bldg.code} thành công.",
    }
