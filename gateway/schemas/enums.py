from enum import Enum


class KDFEnum(str, Enum):
    PBKDF2 = "PBKDF2"
    SCRYPT = "SCRYPT"
    ARGON2 = "ARGON2"


class KeyWrapAlgoEnum(str, Enum):
    AESGCM_V1 = "AESGCM-v1"
    AESKW_V1 = "AESKW-v1"


class FileEncAlgoEnum(str, Enum):
    AES_256_GCM = "AES-256-GCM"
    AES_256_CTR = "AES-256-CTR"


class UploadDownloadStatusEnum(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuditActionEnum(str, Enum):
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    KEY_UNWRAP = "key_unwrap"


class AuditStatusEnum(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
