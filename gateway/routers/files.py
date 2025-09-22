from fastapi import APIRouter, Depends, UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_connection import get_db
from services.file import handle_file_upload
from models import File, Bucket

router = APIRouter(prefix="/files", tags=["files"])



@router.post("/{bucket_id}")
async def upload_file(bucket_id: int, file: UploadFile, request: Request, db: AsyncSession = Depends(get_db)):
    current_user = request.state.user
    bucket = await db.get(Bucket, bucket_id)
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    if bucket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    new_file = await handle_file_upload(db, bucket, current_user, file)
    return {"file_id": new_file.id, "filename": new_file.filename}

@router.get("/{file_id}", response_model=dict)
async def get_file_metadata(file_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch file metadata only (not content).
    """
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "file_id": file.id,
        "bucket_id": file.bucket_id,
        "filename": file.filename,
        "size_bytes": file.size_bytes,
        "chunks": file.chunks,
        "version": file.version,
        "created_at": file.created_at,
    }
