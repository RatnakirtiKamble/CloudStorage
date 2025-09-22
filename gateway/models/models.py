from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    ForeignKey, BigInteger, Text, UniqueConstraint, LargeBinary, Enum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from schemas.enums import (
    KDFEnum,
    KeyWrapAlgoEnum,
    FileEncAlgoEnum,
    UploadDownloadStatusEnum,
    AuditActionEnum,
    AuditStatusEnum,
)
    
from db.db_connection import Base


# ==========================
# USERS
# ==========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    storage_used = Column(BigInteger, default=0, nullable=False)
    quota_bytes = Column(BigInteger, default= 1024**3)

    encrypted_master_key = Column(LargeBinary, nullable=False)  
    kms_key_id = Column(String(128), nullable=True)  
    kdf = Column(Enum(KDFEnum), default=KDFEnum.PBKDF2, nullable=False)
    key_version = Column(Integer, default=1)

    

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    buckets = relationship("Bucket", back_populates="user", cascade="all, delete-orphan")
    keys = relationship("UserKey", back_populates="user", cascade="all, delete-orphan")


# ==========================
# USER KEY
# =========================
class UserKey(Base):
    __tablename__ = "user_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    access_key = Column(String(40), unique=True, nullable=False)
    secret_hash = Column(String(128), nullable=False)  
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="keys")


# ==========================
# BUCKETS
# ==========================
class Bucket(Base):
    __tablename__ = "buckets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    storage_used = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="buckets")
    files = relationship("File", back_populates="bucket", cascade="all, delete-orphan")


# ==========================
# FILES
# ==========================
class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    bucket_id = Column(Integer, ForeignKey("buckets.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    chunks = Column(Integer, nullable=False)
    chunk_size = Column(BigInteger, nullable=False)

    # Encryption fields
    encrypted_file_key = Column(LargeBinary, nullable=False)  
    key_wrap_algo = Column(Enum(KeyWrapAlgoEnum), default=KeyWrapAlgoEnum.AESGCM_V1, nullable=False)
    file_enc_algo = Column(Enum(FileEncAlgoEnum), default=FileEncAlgoEnum.AES_256_GCM, nullable=False)
    
    file_metadata = Column(JSONB, default=dict)  
    version = Column(Integer, default=1) 

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("bucket_id", "filename", name="uq_bucket_filename"),
    )

    bucket = relationship("Bucket", back_populates="files")
    chunks_rel = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")
    uploads_rel = relationship("Upload", back_populates="file", cascade="all, delete-orphan")
    downloads_rel = relationship("Download", back_populates="file", cascade="all, delete-orphan")


# ==========================
# CHUNKS
# ==========================
class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    idx = Column(Integer, nullable=False)  
    object_key = Column(String(512), nullable=False) 
    size_bytes = Column(BigInteger, nullable=False)
    sha256 = Column(String(64), nullable=False)

    iv = Column(LargeBinary, nullable=False)

    algo_ver = Column(String(32), default="v1")
    stored_at = Column(DateTime(timezone=True), server_default=func.now())

    file = relationship("File", back_populates="chunks_rel")


# ==========================
# UPLOADS
# ==========================
class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(UploadDownloadStatusEnum), default=UploadDownloadStatusEnum.IN_PROGRESS, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    offload_used = Column(Boolean, default=False)
    notes = Column(Text)

    file = relationship("File", back_populates="uploads_rel")


# ==========================
# DOWNLOADS
# ==========================
class Download(Base):
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(UploadDownloadStatusEnum), default=UploadDownloadStatusEnum.IN_PROGRESS, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    offload_used = Column(Boolean, default=False)
    notes = Column(Text)

    file = relationship("File", back_populates="downloads_rel")


# ==========================
# AUDIT LOG
# ==========================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    action = Column(Enum(AuditActionEnum), nullable=False)
    status = Column(Enum(AuditStatusEnum), default=AuditStatusEnum.SUCCESS, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
