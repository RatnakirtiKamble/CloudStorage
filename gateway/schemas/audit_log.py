from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from .enums import AuditActionEnum, AuditStatusEnum


class AuditLogBase(BaseModel):
    action: AuditActionEnum
    status: AuditStatusEnum = AuditStatusEnum.SUCCESS
    notes: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: int
    file_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
