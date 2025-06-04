from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from app.models.models import User
from app.schemas import user as user_schema
from app.utils.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.config import settings

logger = logging.getLogger(__name__)


def create_user(db: Session, user: user_schema.UserCreate):
    """Tạo người dùng mới"""
    # Kiểm tra email đã tồn tại chưa
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Kiểm tra username đã tồn tại chưa
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Tạo người dùng mới
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    """Xác thực người dùng"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def login_user(db: Session, user_data: user_schema.UserLogin):
    """Đăng nhập người dùng"""
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Tạo access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "encodedToken": access_token,
        "foundUser": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }


def get_user_by_id(db: Session, user_id: int):
    """Lấy thông tin người dùng theo ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    """Lấy danh sách người dùng"""
    return db.query(User).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_data: user_schema.UserUpdate):
    """Cập nhật thông tin người dùng"""
    db_user = get_user_by_id(db, user_id)
    
    # Cập nhật thông tin
    if user_data.username is not None:
        db_user.username = user_data.username
    if user_data.email is not None:
        db_user.email = user_data.email
    if user_data.password is not None:
        db_user.hashed_password = get_password_hash(user_data.password)
    if user_data.is_active is not None:
        db_user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(db_user)
    return db_user 