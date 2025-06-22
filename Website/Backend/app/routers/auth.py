from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any
from app.database.database import get_db
from app.schemas import user as user_schema
from app.services import user_service
from app.utils.security import authenticate_user, create_access_token
from datetime import timedelta
from app.config import settings

router = APIRouter(tags=["Authentication"])

logger = logging.getLogger(__name__)


@router.post("/signup", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def signup(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    """
    Đăng ký người dùng mới
    """
    return user_service.create_user(db, user)


@router.post("/login", response_model=Dict[str, Any])
def login(user_data: user_schema.UserLogin, db: Session = Depends(get_db)):
    """
    Đăng nhập người dùng
    """
    return user_service.login_user(db, user_data)


@router.post("/token", response_model=user_schema.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Đăng nhập và lấy token (dùng cho Swagger UI)
    """
    # Chuyển đổi username từ form thành email cho authenticate_user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"} 