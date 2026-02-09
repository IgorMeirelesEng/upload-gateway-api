from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db # Ajuste conforme seu import real
from app.crud import user as crud_user
from app.schemas.token import Token

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatível com token login, pega username e password do form.
    """
    # O form_data.username vem do frontend
    user = crud_user.get_user_by_username(db, username=form_data.username)

    # Verifica se usuário existe e senha confere
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ou Senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")

    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Cria o JWT
    access_token = security.create_access_token(
        subject=user.username, 
        expires_delta=access_token_expires,
        role=user.role.value # Passa a role para dentro do token também (opcional, mas útil)
    )
    
    # --- CORREÇÃO AQUI: Adicionado o campo 'role' ---
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value # Necessário pois o schema Token exige este campo
    }