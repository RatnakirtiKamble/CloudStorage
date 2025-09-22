# gateway/services/upload_service.py
import os
import math
import base64
import aiofiles
import asyncio
from redis import Redis
from rq import Queue, Job
from sqlalchemy.ext.asyncio import AsyncSession
from models import File, Chunk, Upload, AuditLog, AuditActionEnum, AuditStatusEnum, UploadDownloadStatusEnum, KeyWrapAlgoEnum, FileEncAlgoEnum
from gateway.utils.crypto import wrap_file_key_with_root  # or local_hsm
from worker.tasks import process_chunk_task  # for CPU fallback
from typing import List

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 5 * 1024 * 1024))
STORAGE_ROOT = os.environ.get("STORAGE_ROOT", "/data/storage")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")

# RQ client
redis_conn = Redis.from_url(REDIS_URL)
q = Queue("default", connection=redis_conn)


async def create_file_record(db: AsyncSession, bucket_id: int, filename: str, size_bytes: int, encrypted_file_key: bytes):
    new_file = File(
        bucket_id=bucket_id,
        filename=filename,
        size_bytes=size_bytes,
        chunks=math.ceil(size_bytes / CHUNK_SIZE),
        chunk_size=CHUNK_SIZE,
        encrypted_file_key=encrypted_file_key,
        key_wrap_algo=KeyWrapAlgoEnum.AESGCM_V1,
        file_enc_algo=FileEncAlgoEnum.AES_256_GCM,
        file_metadata={},
        version=1
    )
    db.add(new_file)
    await db.flush()
    return new_file


async def handle_file_upload(db: AsyncSession, bucket, user, upload_file, job_timeout: int = 60):
    """
    1. Create file record
    2. Enqueue chunk jobs to Redis (RQ)
    3. Poll for result; on success persist chunk rows
    4. Fallback to CPU processing for failed/timeouts
    """
    content = await upload_file.read()
    size_bytes = len(content)
    file_key = os.urandom(32)
    file_key_b64 = base64.b64encode(file_key).decode()

    # wrap file key using server root/HSM (demo)
    encrypted_file_key = wrap_file_key_with_root(file_key)

    new_file = await create_file_record(db, bucket.id, upload_file.filename, size_bytes, encrypted_file_key)
    await db.commit()
    await db.refresh(new_file)

    upload = Upload(file_id=new_file.id, status=UploadDownloadStatusEnum.IN_PROGRESS)
    db.add(upload)
    await db.commit()
    await db.refresh(upload)

    total_chunks = new_file.chunks
    job_list = []

    # Enqueue jobs synchronously (RQ uses pickle to serialize bytes)
    for idx in range(total_chunks):
        start = idx * CHUNK_SIZE
        end = min(start + CHUNK_SIZE, size_bytes)
        chunk_bytes = content[start:end]
        # enqueue: function path 'worker.tasks.process_chunk_task'
        job = q.enqueue("worker.tasks.process_chunk_task", new_file.id, idx, bucket.id, file_key_b64, chunk_bytes, job_timeout=job_timeout)
        job_list.append(job)

    # Poll for job completion concurrently
    # We'll wait up to job_timeout * 1.5 per job (configurable)
    timeout_total = job_timeout * 1.5
    results = [None] * total_chunks
    start_time = asyncio.get_event_loop().time()

    for i, job in enumerate(job_list):
        # poll until finished or overall timeout
        while True:
            job.refresh()  # update job.meta/status
            if job.is_finished:
                results[i] = job.result
                break
            if job.is_failed:
                results[i] = None
                break
            if (asyncio.get_event_loop().time() - start_time) > timeout_total:
                results[i] = None
                break
            await asyncio.sleep(0.1)

    # Now process results: write chunks & DB rows; fallback CPU for failures
    os.makedirs(os.path.join(STORAGE_ROOT, f"bucket_{bucket.id}", f"file_{new_file.id}"), exist_ok=True)

    success = True
    for idx, res in enumerate(results):
        if res is None:
            # fallback - process locally using same code
            start = idx * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, size_bytes)
            chunk_bytes = content[start:end]
            # process_chunk_task returns same dict structure
            res = process_chunk_task(new_file.id, idx, bucket.id, file_key_b64, chunk_bytes)
            # mark success but note fallback
            success = success and True

        # persist returned metadata
        object_rel = res["object_rel"]
        iv_b64 = res["iv_b64"]
        tag_b64 = res["tag_b64"]
        sha = res["sha256"]
        size_b = res["size_bytes"]

        chunk_row = Chunk(
            file_id=new_file.id,
            idx=idx,
            object_key=object_rel,
            size_bytes=size_b,
            sha256=sha,
            iv=base64.b64decode(iv_b64) if iv_b64 else b""
        )
        db.add(chunk_row)

    upload.status = UploadDownloadStatusEnum.SUCCESS if success else UploadDownloadStatusEnum.FAILED
    upload.offload_used = True
    db.add(upload)

    audit = AuditLog(
        user_id=user.id,
        file_id=new_file.id,
        action=AuditActionEnum.UPLOAD,
        status=AuditStatusEnum.SUCCESS if success else AuditStatusEnum.FAILED,
        notes=f"Uploaded {new_file.filename}, chunks={new_file.chunks}"
    )
    db.add(audit)

    await db.commit()
    await db.refresh(new_file)
    return new_file
