from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api import deps
from app.schemas import user as user_schema
from app.crud import user as crud_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[user_schema.UserResponse])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_superuser), # Só Admin pode listar
) -> Any:
    
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=user_schema.UserResponse)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: user_schema.UserCreate,
    current_user: User = Depends(deps.get_current_active_superuser), # Só Admin pode criar
) -> Any:
    
    user = crud_user.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Este username já existe no sistema.",
        )
    user = crud_user.create_user(db, user_in)
    return user

@router.get("/me", response_model=user_schema.UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
   
    return current_user