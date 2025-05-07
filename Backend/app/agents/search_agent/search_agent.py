from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.tools import google_search

from ...common.base_agent import BaseAgent
from ...config.settings import Settings

class SearchAgent(BaseAgent):
    """Agent chuyên xử lý tìm kiếm thông tin"""
    
    def __init__(self):
        config = Settings.get_agent_config("search_agent")
        super().__init__(
            name="search_agent",
            model=config["model"],
            description=config["description"],
            instruction=config["instruction"]
        )
        
    def _create_agent(self) -> Agent:
        """Tạo instance của Agent với google_search tool"""
        return Agent(
            name=self.name,
            model=self.model,
            description=self.description,
            instruction=self.instruction,
            tools=[google_search]
        )
        
    def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Xử lý yêu cầu tìm kiếm
        
        Args:
            query: Câu truy vấn tìm kiếm
            **kwargs: Các tham số bổ sung
            
        Returns:
            Dict chứa kết quả tìm kiếm
        """
        if not self.runner:
            raise RuntimeError("Agent chưa được khởi tạo")
            
        events = self.runner.run_live(
            session_id=self.session_id,
            query=query
        )
        
        response = self._get_final_response(events)
        return {
            "query": query,
            "response": response,
            "agent": self.name
        } 