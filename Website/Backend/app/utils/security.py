from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database.database import get_db
from app.models.models import User
from app.schemas.user import TokenData

# Cấu hình mã hóa mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cấu hình OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token", auto_error=False)


def verify_password(plain_password, hashed_password):
    """Xác minh mật khẩu"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Tạo mật khẩu đã hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Tạo JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def get_user(db: Session, username: str):
    """Lấy thông tin người dùng từ username"""
    return db.query(User).filter(User.email == username).first()


def get_user_by_email(db: Session, email: str):
    """Lấy thông tin người dùng từ email"""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str):
    """Xác thực người dùng"""
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Lấy thông tin người dùng hiện tại từ token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Kiểm tra người dùng có active không"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """Kiểm tra người dùng có phải admin không"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    Lấy thông tin người dùng hiện tại từ token nếu có
    Nếu không có token, trả về None
    """
    if token is None:
        return None
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            return None
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        return None
    
    user = get_user(db, username=token_data.username)
    if user is None:
        return None
    
    return user 