from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.user import UserRole

class UserBase(BaseModel):
    username: str
    is_active: bool = True
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)