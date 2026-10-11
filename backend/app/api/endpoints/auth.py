import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.models.users import User, UserRole
from app.models.students import Student
from app.schemas.auth import MockLoginRequest, Token, UserResponse
from app.core.security import create_access_token
from app.api import deps

router = APIRouter()

@router.post("/mock-login", response_model=Token)
async def mock_login(
    req: MockLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Giả lập đăng nhập, tạo user nếu chưa có và cấp token.
    Chỉ chạy khi DEV_MOCK_AUTH = True.
    """
    if not settings.DEV_MOCK_AUTH:
        raise HTTPException(status_code=403, detail="Mock auth is disabled")

    # Check if user exists
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=req.email,
            full_name=req.full_name or req.email.split("@")[0],
            role=req.role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # If student, also create/link student profile
        if req.role == UserRole.STUDENT and req.email.endswith("@st.neu.edu.vn"):
            student_code = req.email.split("@")[0][:8]
            result_st = await db.execute(select(Student).where(Student.student_code == student_code))
            student = result_st.scalar_one_or_none()
            
            if not student:
                student = Student(
                    student_code=student_code,
                    full_name=user.full_name,
                    user_id=user.id
                )
                db.add(student)
            else:
                student.user_id = user.id
            await db.commit()

    access_token = create_access_token(subject=user.id, role=user.role.value)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get current user profile.
    """
    # Cast uuid to string
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role
    )

