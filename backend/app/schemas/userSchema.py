from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.userModel import UserRole

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER

class UserResponse(UserBase):
    id: int
    role: UserRole
    isVerified: bool

    class Config:
        from_attributes = True