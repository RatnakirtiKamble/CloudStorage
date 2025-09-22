from datetime import datetime
from pydantic import BaseModel
from .enums import KeyWrapAlgoEnum, FileEncAlgoEnum


class FileBase(BaseModel):
    filename: str
    size_bytes: int
    chunks: int
    chunk_size: int


class FileCreate(FileBase):
    encrypted_file_key: bytes
    key_wrap_algo: KeyWrapAlgoEnum = KeyWrapAlgoEnum.AESGCM_V1
    file_enc_algo: FileEncAlgoEnum = FileEncAlgoEnum.AES_256_GCM


class FileResponse(FileBase):
    id: int
    bucket_id: int
    encrypted_file_key: bytes
    key_wrap_algo: KeyWrapAlgoEnum
    file_enc_algo: FileEncAlgoEnum
    version: int
    created_at: datetime

    class Config:
        from_attributes = True
