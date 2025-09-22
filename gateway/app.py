from fastapi import FastAPI
import uvicorn

from routers import auth as auth_router
from routers import bucket as bucket_router

from middleware import auth as auth_middleware

from db.db_connection import engine, Base

from contextlib import asynccontextmanager

# ===== FastAPI App Initialization =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="MiniCloudStorage",
    description="Backend APIs for authentication and data storage with DPU processing.",
    version="1.0.0", 
    lifespan=lifespan
)

app.add_middleware(auth_middleware.JWTMiddleware)

app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(bucket_router.router, prefix="/buckets", tags=["Buckets"])

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
