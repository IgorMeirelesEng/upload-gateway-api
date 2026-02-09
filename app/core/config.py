import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "ECG Upload Service"
    API_V1_STR: str = "/api/v1"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str 

    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    SFTP_HOST: str
    SFTP_PORT: int = 22
    SFTP_USERNAME: str
    SFTP_KEY_PATH: str
    SFTP_REMOTE_PATH: str

    FIRST_SUPERUSER: str = "admin"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"

    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    SECRET_KEY: str = "secretkeyecguploads"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 HORAS

    API_KEY: str = "ecguploads"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True

settings = Settings()