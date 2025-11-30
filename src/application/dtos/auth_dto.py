from pydantic import BaseModel, EmailStr
from typing import Optional
from domain.entities.user import UserRole


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    user: dict
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole

    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.STUDENT


class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None


class DeleteUserResponse(BaseModel):
    message: str
    user_id: str
