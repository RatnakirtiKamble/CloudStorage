from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from .enums import UploadDownloadStatusEnum


class DownloadBase(BaseModel):
    status: UploadDownloadStatusEnum = UploadDownloadStatusEnum.IN_PROGRESS
    offload_used: bool = False
    notes: Optional[str] = None


class DownloadCreate(DownloadBase):
    pass


class DownloadResponse(DownloadBase):
    id: int
    file_id: int
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True
