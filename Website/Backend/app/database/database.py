from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Tạo URL kết nối đến MySQL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# Tạo engine kết nối
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Tạo SessionLocal để tương tác với database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tạo Base class cho các model
Base = declarative_base()


# Dependency để lấy database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 