from typing import Dict, Any, Optional
from google.adk.agents import Agent
from app.agents.base_agent import BaseAgent
from app.tools.glasses_tool import GlassesSearchTool
from app.config.settings import Settings

class GlassesAgent(BaseAgent):
    """Agent xử lý tìm kiếm kính mắt"""
    
    def __init__(self):
        config = Settings.get_agent_config("glasses")
        super().__init__(
            name="glasses_agent",
            model=config["model"],
            description=config["description"],
            instruction=config["instruction"]
        )
        self.search_tool = GlassesSearchTool()
        self.agent = None
    
    async def _create_agent(self) -> Agent:
        """Tạo agent với các công cụ tìm kiếm kính mắt"""
        self.agent = Agent(
            name=self.name,
            model=self.model,
            description=self.description,
            instruction=self.instruction,
            tools=[self.search_tool]
        )
        return self.agent
    
    async def process(self, query: str, image_url: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Xử lý truy vấn tìm kiếm kính mắt"""
        if not self.agent:
            await self._create_agent()
            
        try:
            # Gọi trực tiếp công cụ tìm kiếm
            result = await self.search_tool.execute(
                query=query,
                image_url=image_url,
                **kwargs
            )
            
            if result.get("status") == "success":
                return {
                    "query": query,
                    "results": result.get("results", []),
                    "total": result.get("total", 0),
                    "agent": self.name
                }
            else:
                return {
                    "query": query,
                    "error": result.get("error", "Không tìm thấy kết quả phù hợp"),
                    "agent": self.name
                }
                
        except Exception as e:
            return {
                "query": query,
                "error": str(e),
                "agent": self.name
            } 