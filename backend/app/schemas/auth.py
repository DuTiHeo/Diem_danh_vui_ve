from pydantic import BaseModel
from app.models.users import UserRole

class MockLoginRequest(BaseModel):
    email: str
    role: UserRole
    full_name: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: UserRole

    class Config:
        from_attributes = True

