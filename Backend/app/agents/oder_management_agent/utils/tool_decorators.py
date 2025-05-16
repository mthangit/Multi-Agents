"""
Tool decorators for shopping agent
"""
import functools
import logging
import time
import traceback
from typing import Any, Callable, Dict, TypeVar, cast

from google.adk.tools import Tool
from sqlalchemy.orm import Session

from shopping_agent.core.database import get_session
from shopping_agent.config.settings import TOOL_TIMEOUT

# Type variable for functions
F = TypeVar('F', bound=Callable[..., Any])

def with_db_session(func: F) -> F:
    """
    Decorator để tự động cung cấp session DB cho tool function
    
    Usage:
    @with_db_session
    def my_tool(db: Session, param1: str, ...) -> dict:
        # db là session SQLAlchemy được tự động truyền vào
        ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        db = get_session()
        try:
            # Thêm session vào đầu danh sách tham số
            result = func(db, *args, **kwargs)
            return result
        except Exception as e:
            db.rollback()
            logging.error(f"Database error in {func.__name__}: {e}")
            return {
                "status": "error",
                "message": f"Database error: {str(e)}"
            }
        finally:
            db.close()
    
    return cast(F, wrapper)

def with_error_handling(func: F) -> F:
    """
    Decorator để xử lý lỗi trong tools
    
    Usage:
    @with_error_handling
    def my_tool(...) -> dict:
        ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in tool {func.__name__}: {str(e)}")
            logging.debug(traceback.format_exc())
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }
    
    return cast(F, wrapper)

def with_timing(func: F) -> F:
    """
    Decorator để đo thời gian thực thi của tool
    
    Usage:
    @with_timing
    def my_tool(...) -> dict:
        ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        logging.info(f"Tool {func.__name__} executed in {duration:.2f} seconds")
        return result
    
    return cast(F, wrapper)

def with_timeout(timeout: int = TOOL_TIMEOUT):
    """
    Decorator để giới hạn thời gian thực thi của tool
    
    Usage:
    @with_timeout(5)  # 5 seconds timeout
    def my_tool(...) -> dict:
        ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Đây chỉ là cài đặt giả lập timeout, trong thực tế chúng ta nên sử dụng
            # multiprocessing hoặc threading để xử lý timeout thật
            start_time = time.time()
            result = func(*args, **kwargs)
            
            if time.time() - start_time > timeout:
                logging.warning(f"Tool {func.__name__} exceeded timeout of {timeout} seconds")
                return {
                    "status": "warning",
                    "message": f"Operation took longer than expected ({timeout} seconds)",
                    "data": result
                }
            return result
            
        return cast(F, wrapper)
    return decorator

def create_tool(name: str, description: str, func: Callable) -> Tool:
    """
    Tạo một ADK Tool
    
    Args:
        name: Tên của tool
        description: Mô tả của tool
        func: Hàm xử lý của tool
        
    Returns:
        Tool: ADK Tool object
    """
    return Tool(name=name, description=description, function=func) 