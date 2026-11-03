import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.models.users import User, UserRole

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/mock-login",
    auto_error=False,
)

ALLOWED_NEU_DOMAINS = ("neu.edu.vn", "st.neu.edu.vn")


def is_valid_neu_email(email: str | None) -> bool:
    if not email or "@" not in email:
        return False
    local_part, domain = email.strip().lower().rsplit("@", 1)
    return bool(local_part) and domain in ALLOWED_NEU_DOMAINS


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(reusable_oauth2),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản chưa đăng nhập hoặc phiên làm việc đã hết hạn (EX-01).",
        )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tài khoản chưa đăng nhập hoặc phiên làm việc đã hết hạn (EX-01).",
            )
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValidationError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản chưa đăng nhập hoặc phiên làm việc đã hết hạn (EX-01).",
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản chưa đăng nhập hoặc phiên làm việc đã hết hạn (EX-01).",
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa (EX-01).",
        )
    if not is_valid_neu_email(current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không thuộc tên miền @neu.edu.vn hoặc @st.neu.edu.vn. Vui lòng sử dụng tài khoản Microsoft 365 của trường NEU (EX-01).",
        )
    return current_user


async def get_current_lecturer(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role not in (UserRole.LECTURER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Giảng viên hoặc Quản trị viên mới có quyền thực hiện thao tác này.",
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Quản trị viên (ADMIN) mới có quyền thực hiện thao tác này.",
        )
    return current_user


async def get_current_student(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Sinh viên (STUDENT) mới có quyền thực hiện thao tác này.",
        )
    return current_user
