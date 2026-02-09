import os
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

api_key_header = APIKeyHeader(name="access_token", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == settings.API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Credenciais inválidas"
    )

def verify_ssh_key_permissions():
    key_path = settings.SFTP_KEY_PATH
    if not os.path.isfile(key_path):
        print(f"ERRO! Chave SSH não encontrada: {key_path}")
        return False
    
    if not os.access(key_path, os.R_OK):
        print(f"ERRO! Chave SSH não tem permissão de leitura: {key_path}")
        return False
    return True