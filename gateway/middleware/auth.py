from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_connection import get_db
from crud.user import get_user_by_id
from config import settings

async def get_current_user_from_token(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user = await get_user_by_id(db, int(user_id))
    return user

class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth routes
        if request.url.path in ["/auth/login", "/auth/register", "/auth/whoami"]:
            return await call_next(request)
        
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if auth_header is None or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Authorization header missing"})

        token = auth_header.split(" ")[1]

        async for db in get_db():
            user = await get_current_user_from_token(token, db)
            if not user:
                return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})
            request.state.user = user

        response = await call_next(request)
        return response
