from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from services.bucket import create_bucket_service, delete_bucket_service, list_bucket_service, rename_bucket_service
from db import get_db
from schemas.bucket import BucketCreate, BucketResponse

router = APIRouter()

@router.post("/", response_model=BucketResponse)
async def create_bucket(bucket: BucketCreate, request: Request, db: AsyncSession = Depends(get_db)):
    user = request.state.user
    return await create_bucket_service(db, bucket, user.id)

@router.delete("/{bucket_id}", response_model=BucketResponse)
async def delete_bucket(bucket_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = request.state.user
    try:
        bucket = await delete_bucket_service(db, bucket_id, user.id)
        if not bucket:
            raise HTTPException(status_code=404, detail="Bucket not found or not owned by user")
        return bucket
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.put("/{bucket_id}")
async def rename_bucket(bucket_id: int, db: AsyncSession = Depends(get_db), new_name: str = None):
    bucket = await rename_bucket_service(db, bucket_id, new_name)
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return bucket

@router.get("/", response_model=list[BucketResponse])
async def list_buckets(request: Request, db: AsyncSession = Depends(get_db)):
    user = request.state.user
    return await list_bucket_service(db, user.id)