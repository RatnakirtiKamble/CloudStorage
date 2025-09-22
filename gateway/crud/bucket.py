from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import Bucket
from schemas.bucket import BucketCreate
import os

async def create_bucket(db: AsyncSession, bucket: BucketCreate, user_id: int) -> Bucket:
    db_bucket = Bucket(
        name=bucket.name,
        user_id=user_id
    )
    db.add(db_bucket)
    await db.commit()
    await db.refresh(db_bucket)
    return db_bucket

async def delete_bucket(db: AsyncSession, bucket_id: int, owner_id: int) -> Bucket | None:
    result = await db.execute(select(Bucket).filter(Bucket.id == bucket_id))
    db_bucket = result.scalars().first()
    if db_bucket:
        await db.delete(db_bucket)
        await db.commit()
    return db_bucket

async def rename_bucket(db: AsyncSession, bucket_id: int, new_name: str) -> Bucket | None:
    result = await db.execute(select(Bucket).filter(Bucket.id == bucket_id))
    db_bucket = result.scalars().first()
    if db_bucket:
        db_bucket.name = new_name
        await db.commit()
        await db.refresh(db_bucket)
    return db_bucket

async def list_buckets(db: AsyncSession, user_id: int) -> list[Bucket]:
    result = await db.execute(select(Bucket).filter(Bucket.user_id == user_id))
    return result.scalars().all()