from datetime import datetime
from pydantic import BaseModel


class ChunkBase(BaseModel):
    idx: int
    object_key: str
    size_bytes: int
    sha256: str


class ChunkCreate(ChunkBase):
    iv: bytes


class ChunkResponse(ChunkBase):
    id: int
    file_id: int
    iv: bytes
    algo_ver: str
    stored_at: datetime

    class Config:
        from_attributes = True
