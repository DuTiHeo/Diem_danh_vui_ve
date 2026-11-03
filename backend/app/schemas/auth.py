from pydantic import BaseModel, ConfigDict
from app.models.users import UserRole


class MockLoginRequest(BaseModel):
    email: str
    role: UserRole | None = None
    full_name: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: UserRole
    is_active: bool = True
    student_code: str | None = None
    last_name: str | None = None
    first_name: str | None = None
    date_of_birth: str | None = None
    admin_class: str | None = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: UserResponse | None = None
