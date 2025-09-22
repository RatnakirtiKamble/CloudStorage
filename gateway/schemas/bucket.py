from datetime import datetime
from pydantic import BaseModel


class BucketBase(BaseModel):
    name: str


class BucketCreate(BucketBase):
    pass


class BucketResponse(BucketBase):
    id: int
    user_id: int
    storage_used: int
    created_at: datetime

    class Config:
        from_attributes = True
