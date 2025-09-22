from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from db.db_connection import get_db
from schemas.user import UserCreate, UserResponse
from services.auth import (
    create_access_token,
    get_current_user,
    register_user,
    authenticate_user,
)

router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await register_user(db, user)


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/whoami", response_model=UserResponse)
async def whoami(current_user: UserResponse = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout():
    return {"message": "Logout successful (delete token client-side)"}


@router.get("/check_auth")
async def check_auth(user = Depends(get_current_user)):
    return {"status": "ok", "user_id": user.id, "role": user.role}
