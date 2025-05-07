from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

class BaseAgent(ABC):
    """Lớp cơ sở cho các agent, định nghĩa giao diện chung"""
    
    def __init__(self, name: str, model: str, description: str, instruction: str):
        """Khởi tạo agent với các thuộc tính cơ bản"""
        self.name = name
        self.model = model
        self.description = description
        self.instruction = instruction
        self.session_service = InMemorySessionService()
        self.runner = None
        self.session_id = f"{name}_session"
    
    async def _create_agent(self) -> Agent:
        """Phương thức tạo và khởi tạo agent, cần được ghi đè"""
        self.agent = Agent(
            name=self.name,
            model=self.model,
            description=self.description,
            instruction=self.instruction
        )
        return self.agent
    
    async def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """Phương thức xử lý yêu cầu, cần được ghi đè"""
        raise NotImplementedError("Phương thức process() cần được ghi đè bởi lớp con")
    
    def before_agent_callback(self, **kwargs) -> None:
        """Callback được gọi trước khi agent xử lý yêu cầu"""
        pass
    
    def after_agent_callback(self, response: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Callback được gọi sau khi agent xử lý yêu cầu"""
        return response
    
    def initialize(self, app_name: str, user_id: str):
        """
        Khởi tạo agent với session và runner
        
        Args:
            app_name: Tên ứng dụng
            user_id: ID người dùng
        """
        self.session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=self.session_id
        )
        self.runner = Runner(
            agent=self._create_agent(),
            app_name=app_name,
            session_service=self.session_service
        )
        
    def _get_final_response(self, events) -> str:
        """
        Lấy phản hồi cuối cùng từ events
        
        Args:
            events: Danh sách events từ runner
            
        Returns:
            Phản hồi cuối cùng
        """
        for event in events:
            if event.is_final_response():
                return event.content.parts[0].text
        return "Không nhận được phản hồi từ agent" 