# worker/tasks.py
import os, base64
from typing import Dict
from worker.utils.crypto import gpu_transform, aes_gcm_encrypt, hashlib_sha  # as defined earlier
from pathlib import Path

STORAGE_ROOT = os.environ.get("STORAGE_ROOT", "/data/storage")
WORKER_MODE = os.environ.get("WORKER_MODE", "gpu").lower()
WRAP_WITH_AES = os.environ.get("WRAP_WITH_AES", "1") == "1"

def process_chunk_task(file_id: int, idx: int, bucket_id: int, file_key_b64: str, chunk_bytes: bytes) -> Dict:
    """
    RQ task signature. Writes encrypted chunk to shared storage and returns metadata.
    """
    file_key = base64.b64decode(file_key_b64)

    # 1) heavy transform (GPU/CPU)
    if WORKER_MODE == "gpu":
        transformed = gpu_transform(chunk_bytes, key_like=file_key)  # real GPU compute
        payload = transformed
    else:
        # CPU baseline: use plaintext for AES wrap (no transform)
        payload = chunk_bytes

    # 2) wrap with AES-GCM on CPU for secure storage (recommended)
    if WRAP_WITH_AES:
        enc = aes_gcm_encrypt(file_key, payload)  # returns ciphertext, iv, tag, sha256
        ciphertext = enc["ciphertext"]
        iv = enc["iv"]
        tag = enc["tag"]
        sha = enc["sha256"]
    else:
        ciphertext = payload
        iv = b""
        tag = b""
        sha = hashlib_sha(ciphertext)

    # 3) persist to shared PVC
    rel_dir = Path(f"bucket_{bucket_id}") / f"file_{file_id}"
    abs_dir = Path(STORAGE_ROOT) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    rel_path = rel_dir / f"chunk_{idx}.bin"
    abs_path = abs_dir / f"chunk_{idx}.bin"
    with open(abs_path, "wb") as f:
        f.write(ciphertext)

    return {
        "file_id": file_id,
        "idx": idx,
        "object_rel": str(rel_path),
        "iv_b64": base64.b64encode(iv).decode(),
        "tag_b64": base64.b64encode(tag).decode(),
        "sha256": sha,
        "size_bytes": len(ciphertext)
    }
