from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging
from app.database.database import get_db
from app.schemas import user as user_schema
from app.services import user_service

router = APIRouter(tags=["Authentication"])

logger = logging.getLogger(__name__)


@router.post("/signup", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
def signup(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    """
    Đăng ký người dùng mới
    """
    return user_service.create_user(db, user)


@router.post("/login", response_model=dict)
def login(user_data: user_schema.UserLogin, db: Session = Depends(get_db)):
    """
    Đăng nhập người dùng
    """
    return user_service.login_user(db, user_data) 