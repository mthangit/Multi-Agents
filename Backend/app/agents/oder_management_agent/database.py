"""
Database connection module for the shopping agent
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from shopping_agent.config.settings import DB_CONFIG

# Format connection string
DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a thread-local session that can be safely shared across threads
db_session = scoped_session(SessionLocal)

# Base class for all models
Base = declarative_base()
Base.query = db_session.query_property()

def get_db_session():
    """
    Get a database session.
    Usage pattern:
    
    session = get_db_session()
    try:
        # Use session here
        result = session.query(Model).all()
        return result
    finally:
        session.close()
    """
    session = SessionLocal()
    return session

def init_db():
    """Initialize database tables"""
    # Import all models here so they are registered with Base
    # Example: from shopping_agent.models import some_model
    
    # Create tables
    Base.metadata.create_all(bind=engine) 