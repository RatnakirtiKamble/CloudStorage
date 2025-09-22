from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from .enums import UploadDownloadStatusEnum


class UploadBase(BaseModel):
    status: UploadDownloadStatusEnum = UploadDownloadStatusEnum.IN_PROGRESS
    offload_used: bool = False
    notes: Optional[str] = None


class UploadCreate(UploadBase):
    pass


class UploadResponse(UploadBase):
    id: int
    file_id: int
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True
