from db.db_connection import get_db
from crud import create_bucket, delete_bucket, list_buckets, rename_bucket

async def create_bucket_service(db, bucket, user_id):
    return await create_bucket(db, bucket, user_id)

async def delete_bucket_service(db, bucket_id, owner_id):
    buckets = await list_buckets(db, owner_id)
    bucket_ids = [b.id for b in buckets]
    if bucket_id not in bucket_ids:
        return None
    return await delete_bucket(db, bucket_id)

async def list_bucket_service(db, user_id):
    return await list_buckets(db, user_id)

async def rename_bucket_service(db, bucket_id, new_name):
    return await rename_bucket(db, bucket_id, new_name)