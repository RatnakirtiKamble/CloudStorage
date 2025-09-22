from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ASYNC_DATABASE_URL: str = "sqlite:///./test.db"
    SECRET_KEY: str = "default"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SYNC_DATABASE_URL: str = "sqlite:///./test.db"
    ROOT_KEY: str = "default_root_key"

    class Config:
        env_file = "/home/ratnakirti/Work/CloudStorage/gateway/.env"

settings = Settings()

