from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import User
from schemas.user import UserCreate
from schemas.enums import KDFEnum
from utils.security_utils import get_password_hash
from services.hsm import local_hsm
import os


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed_pw = get_password_hash(user.password)

    # 1. Generate user master key
    user_master_key = os.urandom(32)

    # 2. Generate a KMS key ID if not exists
    kms_key_id = f"user_hsm_{user.username}"

    local_hsm.generate_hsm_key(kms_key_id)


    # 3. Encrypt master key with local HSM
    encrypted_master_key = local_hsm.encrypt_master_key(user_master_key, kms_key_id)

    # 4. Create user record
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw,
        encrypted_master_key=encrypted_master_key,
        kms_key_id=kms_key_id,
        kdf=KDFEnum.PBKDF2,
        key_version=1
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user



async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """
    Fetches a user by their unique ID.

    Args:
        db (AsyncSession): Async SQLAlchemy session.
        user_id (int): The ID of the user to retrieve.

    Returns:
        User | None: The User ORM instance if found, otherwise None.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Fetches a user by their unique email address.

    Args:
        db (AsyncSession): Async SQLAlchemy session.
        email (str): Email address of the user.

    Returns:
        User | None: The User ORM instance if found, otherwise None.
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    """
    Fetches all users with pagination.

    Args:
        db (AsyncSession): Async SQLAlchemy session.
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.

    Returns:
        list[User]: List of User ORM instances.
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


async def delete_user(db: AsyncSession, user_id: int) -> User | None:
    """
    Deletes a user by their unique ID.

    Args:
        db (AsyncSession): Async SQLAlchemy session.
        user_id (int): The ID of the user to delete.

    Returns:
        User | None: The deleted User ORM instance if it existed, otherwise None.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()
    if db_user:
        await db.delete(db_user)
        await db.commit()
    return db_user
