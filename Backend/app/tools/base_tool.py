from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from google.adk.tools import FunctionTool

class BaseTool(ABC):
    """Base class cho tất cả tools trong hệ thống"""
    
    def __init__(self, name: str, description: str):
        """
        Khởi tạo tool cơ bản
        
        Args:
            name: Tên tool
            description: Mô tả tool
        """
        self.name = name
        self.description = description
        
    @abstractmethod
    def _create_tool(self) -> FunctionTool:
        """
        Tạo instance của Tool
        
        Returns:
            Tool instance
        """
        pass
        
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Thực thi tool
        
        Args:
            **kwargs: Các tham số đầu vào
            
        Returns:
            Kết quả thực thi
        """
        pass
        
    def validate_input(self, **kwargs) -> bool:
        """
        Kiểm tra tính hợp lệ của input
        
        Args:
            **kwargs: Các tham số đầu vào
            
        Returns:
            True nếu input hợp lệ, False nếu không
        """
        return True 