from typing import Dict, Any, List
from google.adk.agents import Agent
from app.agents.base_agent import BaseAgent
from app.agents.glasses_agent import GlassesAgent
from app.config.settings import Settings

class OrchestratorAgent(BaseAgent):
    """Agent điều phối các agent con"""
    
    def __init__(self):
        config = Settings.get_agent_config("orchestrator")
        super().__init__(
            name="orchestrator",
            model=config["model"],
            description=config["description"],
            instruction=config["instruction"]
        )
        self.glasses_agent = GlassesAgent()
        self.agent = None
    
    async def _create_agent(self) -> Agent:
        """Tạo agent orchestrator với các sub-agent"""
        # Đảm bảo GlassesAgent đã được khởi tạo
        await self.glasses_agent._create_agent()
        
        # Tạo orchestrator agent
        self.agent = Agent(
            name=self.name,
            model=self.model,
            description=self.description,
            instruction=self.instruction,
            sub_agents=[self.glasses_agent.agent]
        )
        
        return self.agent
    
    async def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """Xử lý truy vấn và chọn agent phù hợp"""
        if not self.agent:
            await self._create_agent()
            
        # Phân tích truy vấn để xác định có phải yêu cầu tìm kiếm kính mắt không
        is_glasses_query = any(keyword in query.lower() for keyword in [
            "kính", "glasses", "mắt kính", "eyeglasses", "sunglasses",
            "kính mát", "kính cận", "kính viễn", "kính áp tròng"
        ])
        
        if is_glasses_query:
            # Xử lý yêu cầu tìm kiếm kính mắt
            return await self.glasses_agent.process(query, **kwargs)
        else:
            return {
                "query": query,
                "error": "Tôi chỉ có thể giúp bạn tìm kiếm kính mắt. Vui lòng mô tả loại kính bạn cần tìm.",
                "agent": self.name
            } 