"""
Base module for tools providing common functionality
"""
from typing import Dict, Any, List, Callable

from google.adk.tools import Tool

from shopping_agent.utils.tool_decorators import with_db_session, with_error_handling, with_timing


class ToolRegistry:
    """
    Registry for managing tools
    """
    _registry: Dict[str, List[Tool]] = {}
    
    @classmethod
    def register_tools(cls, category: str, tools: List[Tool]) -> None:
        """
        Register tools under a category
        
        Args:
            category: Category name
            tools: List of tools
        """
        if category not in cls._registry:
            cls._registry[category] = []
        
        cls._registry[category].extend(tools)
    
    @classmethod
    def get_tools(cls, category: str = None) -> List[Tool]:
        """
        Get tools by category
        
        Args:
            category: Category name, if None returns all tools
            
        Returns:
            List of tools
        """
        if category:
            return cls._registry.get(category, [])
        
        # Return all tools if no category specified
        all_tools = []
        for tools in cls._registry.values():
            all_tools.extend(tools)
        
        return all_tools


def create_db_tool(name: str, description: str, func: Callable) -> Tool:
    """
    Tạo một tool kết nối với database
    
    Args:
        name: Tên tool
        description: Mô tả tool
        func: Hàm xử lý (không cần decorator @with_db_session)
        
    Returns:
        Tool object đã được trang bị session database
    """
    # Áp dụng decorator với_db_session cho function
    db_func = with_db_session(func)
    
    # Thêm error handling và timing
    db_func = with_error_handling(db_func)
    db_func = with_timing(db_func)
    
    return Tool(name=name, description=description, function=db_func) 