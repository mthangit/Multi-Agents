import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from Backend.app.agents.user_interaction_agent.orchestrator import OrchestratorAgent
from app.config.settings import Settings

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Models để request và response
class SearchRequest(BaseModel):
    query: str
    image_url: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class SearchResponse(BaseModel):
    status: str
    response: Optional[str] = None
    error: Optional[str] = None
    agent: Optional[str] = None

class AgentService:
    """Dịch vụ quản lý và chạy agent"""
    
    def __init__(self):
        self.settings = Settings()
        self.session_service = InMemorySessionService()
        self.orchestrator = OrchestratorAgent()
        self.runners = {}  # Lưu trữ runners theo session_id
        
    async def initialize_agent(self):
        """Khởi tạo agent orchestrator"""
        try:
            # Khởi tạo agent orchestrator
            await self.orchestrator._create_agent()
            logger.info(f"Agent '{self.orchestrator.name}' đã được khởi tạo thành công")
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo agent: {str(e)}")
            raise
    
    def get_or_create_session(self, user_id: str, session_id: str) -> str:
        """Tạo session mới hoặc trả về session đã tồn tại"""
        try:
            # Nếu session chưa tồn tại, tạo mới
            if not self.session_service.get_session(self.settings.APP_NAME, user_id, session_id):
                self.session_service.create_session(
                    app_name=self.settings.APP_NAME,
                    user_id=user_id,
                    session_id=session_id
                )
                logger.info(f"Đã tạo session mới: {session_id} cho user: {user_id}")
            return session_id
        except Exception as e:
            logger.error(f"Lỗi khi tạo session: {str(e)}")
            raise
    
    def get_or_create_runner(self, user_id: str, session_id: str) -> Runner:
        """Tạo runner mới hoặc trả về runner đã tồn tại"""
        runner_key = f"{user_id}:{session_id}"
        
        # Nếu runner chưa tồn tại, tạo mới
        if runner_key not in self.runners:
            self.runners[runner_key] = Runner(
                agent=self.orchestrator.agent,
                app_name=self.settings.APP_NAME,
                session_service=self.session_service
            )
            logger.info(f"Đã tạo runner mới cho session: {session_id}")
        
        return self.runners[runner_key]
    
    async def process_request(self, request: SearchRequest) -> SearchResponse:
        """Xử lý yêu cầu tìm kiếm từ người dùng"""
        try:
            # Lấy user_id và session_id từ request hoặc dùng mặc định
            user_id = request.user_id or self.settings.USER_ID
            session_id = request.session_id or self.settings.SESSION_ID
            
            # Tạo hoặc lấy session
            self.get_or_create_session(user_id, session_id)
            
            # Tạo hoặc lấy runner
            runner = self.get_or_create_runner(user_id, session_id)
            
            # Tạo content từ query
            parts = [types.Part(text=request.query)]
            
            # Nếu có image_url, thêm vào parts
            if request.image_url:
                parts.append(types.Part(inline_data=types.InlineData(
                    mime_type="image/jpeg",
                    data=request.image_url
                )))
            
            content = types.Content(role='user', parts=parts)
            
            # Theo dõi kết quả
            final_response = None
            
            # Chạy agent và lấy kết quả
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                # Lấy kết quả cuối cùng
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                    break
            
            if final_response:
                return SearchResponse(
                    status="success",
                    response=final_response,
                    agent=self.orchestrator.name
                )
            else:
                return SearchResponse(
                    status="error",
                    error="Không nhận được phản hồi từ agent"
                )
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý yêu cầu: {str(e)}")
            return SearchResponse(
                status="error",
                error=str(e)
            )

# Khởi tạo agent service
agent_service = AgentService()

# Khởi tạo FastAPI app
app = FastAPI(title="Glasses Search API")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Khởi tạo agent khi khởi động server"""
    await agent_service.initialize_agent()

@app.get("/")
async def root():
    """Endpoint kiểm tra trạng thái API"""
    return {
        "status": "running",
        "version": "1.0.0",
        "app_name": agent_service.settings.APP_NAME
    }

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Endpoint xử lý yêu cầu tìm kiếm"""
    try:
        response = await agent_service.process_request(request)
        return response
    except Exception as e:
        logger.error(f"Lỗi trong quá trình xử lý: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Hàm chạy trực tiếp khi debug
async def run_example():
    """Chạy một ví dụ để kiểm tra agent"""
    await agent_service.initialize_agent()
    
    request = SearchRequest(query="Tìm cho tôi kính mát màu đen")
    response = await agent_service.process_request(request)
    
    print(f"\n=== Ví dụ yêu cầu ===")
    print(f"Query: {request.query}")
    print(f"\n=== Kết quả ===")
    print(f"Status: {response.status}")
    if response.response:
        print(f"Response: {response.response}")
    if response.error:
        print(f"Error: {response.error}")

if __name__ == "__main__":
    if Settings().DEBUG:
        # Nếu ở chế độ debug, chạy ví dụ
        asyncio.run(run_example())
    else:
        # Khởi động server
        uvicorn.run(
            "app.main:app",
            host=Settings().HOST,
            port=Settings().PORT,
            reload=Settings().DEBUG
        ) 