from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from .enums import KDFEnum
import re

class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[@$!%*?&]", value):
            raise ValueError("Password must contain at least one special character (@$!%*?&)")
        return value

class UserResponse(UserBase):
    id: int
    storage_used: int
    kms_key_id: Optional[str]
    kdf: KDFEnum
    key_version: int
    created_at: datetime

    class Config:
        from_attributes = True
