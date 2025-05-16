"""
Core database connection module for shopping agent
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from shopping_agent.config.settings import DB_CONFIG

# Format connection string
DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Create engine - mặc định pool connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a thread-local session that can be safely shared across threads
db_session = scoped_session(SessionLocal)

# Base class for all models
Base = declarative_base()
Base.query = db_session.query_property()

def get_session() -> Session:
    """
    Lấy một session database mới.
    
    Returns:
        Session: SQL Alchemy session
    """
    return SessionLocal()

def get_db():
    """
    Hàm tiện ích để lấy và đảm bảo đóng session.
    
    Yields:
        Session: SQL Alchemy session
        
    Example:
        db = next(get_db())
        try:
            # use db here
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Khởi tạo kết nối database.
    Không tạo bảng mới vì đã có sẵn trong database.
    """
    try:
        # Kiểm tra kết nối - không tạo bảng
        with engine.connect() as conn:
            logging.info("Database connection successful")
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise 