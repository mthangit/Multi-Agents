"""
Database tool wrapper for shopping agent tools
"""
import functools
from typing import Callable, Any, TypeVar, cast

from google.adk.tools import Tool
from sqlalchemy.orm import Session

from shopping_agent.database import get_db_session

F = TypeVar('F', bound=Callable[..., Any])

def with_db_session(func: F) -> F:
    """
    Decorator để tự động cung cấp session DB cho tool function
    
    Sử dụng:
    @with_db_session
    def my_tool_function(db: Session, param1: str, ...) -> dict:
        # db là session SQLAlchemy được tự động truyền vào
        ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = get_db_session()
        try:
            # Thêm session vào đầu danh sách tham số
            result = func(session, *args, **kwargs)
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    return cast(F, wrapper)

def create_db_tool(name: str, description: str, func: Callable) -> Tool:
    """
    Tạo một ADK Tool có kết nối đến database
    
    Args:
        name: Tên của tool
        description: Mô tả của tool
        func: Hàm xử lý của tool (đã được wrap với @with_db_session)
        
    Returns:
        Tool: ADK Tool object
    """
    return Tool(name=name, description=description, function=func) 