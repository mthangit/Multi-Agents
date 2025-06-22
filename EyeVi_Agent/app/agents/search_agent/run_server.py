#!/usr/bin/env python
"""
Script khởi động server API cho Search Agent
Hỗ trợ cả FastAPI mode và A2A mode
"""

import os
import logging
import base64
import uvicorn
import httpx
import sys
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Thêm thư mục app vào sys.path để có thể import từ các module khác
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if app_dir not in sys.path:
    sys.path.append(app_dir)

# A2A imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

# Import từ module app
from agent.agent import SearchAgent
from a2a_wrapper.a2a_agent_executor import SearchAgentExecutor

# Load environment variables
load_dotenv()

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Khởi tạo FastAPI app
app = FastAPI(title="Search Agent API")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo SearchAgent
search_agent = SearchAgent()

# Models
class AnalysisResult(BaseModel):
    """Kết quả phân tích khuôn mặt từ host agent."""
    face_detected: bool = False
    face_shape: Optional[str] = None
    recommended_frame_shapes: Optional[List[str]] = None
    skin_tone: Optional[str] = None
    glasses_detected: Optional[bool] = None
    glasses_observed: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None

class SearchRequest(BaseModel):
    """Yêu cầu tìm kiếm sản phẩm."""
    query: Optional[str] = None
    analysis_result: Optional[AnalysisResult] = None

@app.get("/")
async def root():
    """Endpoint kiểm tra trạng thái."""
    return {"status": "online", "service": "search_agent"}

@app.post("/search")
async def search(
    query: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    analysis_result: Optional[str] = Form(None)
):
    """
    Endpoint tìm kiếm sản phẩm.
    
    Args:
        query: Câu truy vấn tìm kiếm
        image: File hình ảnh (nếu có)
        analysis_result: Kết quả phân tích khuôn mặt dạng JSON string (nếu có)
        
    Returns:
        Kết quả tìm kiếm sản phẩm
    """
    try:
        # Kiểm tra đầu vào
        if not query and not image:
            raise HTTPException(
                status_code=400,
                detail="Phải cung cấp ít nhất một trong hai: query hoặc image"
            )
        
        # Đọc dữ liệu hình ảnh nếu có
        image_data = None
        if image:
            image_data = await image.read()
        
        # Parse analysis_result nếu có
        parsed_analysis = None
        if analysis_result:
            import json
            try:
                parsed_analysis = json.loads(analysis_result)
            except json.JSONDecodeError:
                logger.warning("Không thể parse analysis_result, bỏ qua")
        
        # Gọi search agent để tìm kiếm
        result = await search_agent.search(
            query=query,
            image_data=image_data,
            analysis_result=parsed_analysis
        )
        
        return result
        
    except HTTPException as e:
        # Re-raise FastAPI exceptions
        raise
    except Exception as e:
        logger.error(f"Lỗi khi xử lý yêu cầu tìm kiếm: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý yêu cầu tìm kiếm: {str(e)}"
        )

@app.post("/search/text")
async def search_text(request: SearchRequest):
    """
    Endpoint tìm kiếm sản phẩm bằng text.
    
    Args:
        request: Yêu cầu tìm kiếm
        
    Returns:
        Kết quả tìm kiếm sản phẩm
    """
    try:
        # Kiểm tra đầu vào
        if not request.query:
            raise HTTPException(
                status_code=400,
                detail="Phải cung cấp query"
            )
        
        # Chuyển đổi analysis_result nếu có
        analysis_result = None
        if request.analysis_result:
            analysis_result = request.analysis_result.dict()
        
        # Gọi search agent để tìm kiếm
        result = await search_agent.search(
            query=request.query,
            analysis_result=analysis_result
        )
        
        return result
        
    except HTTPException as e:
        # Re-raise FastAPI exceptions
        raise
    except Exception as e:
        logger.error(f"Lỗi khi xử lý yêu cầu tìm kiếm text: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý yêu cầu tìm kiếm text: {str(e)}"
        )


def create_a2a_server(host: str, port: int) -> A2AStarletteApplication:
    """Tạo A2A server cho Search Agent."""
    
    # Define agent capabilities and skills for product search
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
    
    # Define search agent skills
    search_skills = [
        AgentSkill(
            id='text_search',
            name='Tìm kiếm bằng văn bản',
            description='Tìm kiếm sản phẩm mắt kính dựa trên mô tả bằng văn bản sử dụng CLIP embeddings',
            tags=['search', 'text', 'clip', 'nlp'],
            examples=[
                'Tìm kính cận thị cho nam',
                'Kính râm thể thao màu đen',
                'Gọng vuông titan cho khuôn mặt tròn',
                'Kính chống ánh sáng xanh cho dân văn phòng'
            ],
        ),
        AgentSkill(
            id='image_search',
            name='Tìm kiếm bằng hình ảnh',
            description='Tìm kiếm sản phẩm tương tự dựa trên hình ảnh sử dụng CLIP vision encoder',
            tags=['search', 'image', 'clip', 'computer-vision'],
            examples=[
                'Upload ảnh kính để tìm sản phẩm tương tự',
                'Tìm kính giống với hình ảnh đã có',
                'So sánh sản phẩm qua hình ảnh'
            ],
        ),
        AgentSkill(
            id='multimodal_search',
            name='Tìm kiếm đa phương thức',
            description='Kết hợp tìm kiếm bằng văn bản và hình ảnh để có kết quả tối ưu',
            tags=['search', 'multimodal', 'clip', 'hybrid'],
            examples=[
                'Tìm kính màu đỏ + upload ảnh mẫu',
                'Kính cho khuôn mặt vuông + hình ảnh tham khảo',
                'Gọng kim loại như trong ảnh nhưng màu khác'
            ],
        ),
        AgentSkill(
            id='personalized_search',
            name='Tìm kiếm cá nhân hóa',
            description='Tìm kiếm sản phẩm phù hợp dựa trên phân tích khuôn mặt và sở thích cá nhân',
            tags=['search', 'personalized', 'face-analysis', 'recommendation'],
            examples=[
                'Gợi ý kính phù hợp với khuôn mặt tròn',
                'Tìm kính theo phong cách thời trang hiện đại',
                'Kính phù hợp với độ tuổi và nghề nghiệp'
            ],
        )
    ]

    # Create agent card with specialized search capabilities
    agent_card = AgentCard(
        name='Search Agent',
        description='Agent tìm kiếm sản phẩm mắt kính sử dụng công nghệ CLIP multimodal, hỗ trợ tìm kiếm bằng văn bản, hình ảnh và kết hợp đa phương thức với độ chính xác cao',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=['text/plain', 'image/jpeg', 'image/png'],
        defaultOutputModes=['text/plain', 'application/json'],
        capabilities=capabilities,
        skills=search_skills,
    )

    # Initialize HTTP client and components
    httpx_client = httpx.AsyncClient()
    request_handler = DefaultRequestHandler(
        agent_executor=SearchAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_notifier=InMemoryPushNotifier(httpx_client),
    )

    # Create A2A server
    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )


def check_prerequisites():
    """Check if all prerequisites are met for the search agent."""
    # Check API key
    if not os.getenv('GOOGLE_API_KEY'):
        logger.warning('GOOGLE_API_KEY not set, some features may not work')
    
    # Check Qdrant connection
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port = os.getenv('QDRANT_PORT', '6333')
    
    try:
        import requests
        response = requests.get(f'http://{qdrant_host}:{qdrant_port}/health', timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Qdrant connected at {qdrant_host}:{qdrant_port}")
        else:
            logger.warning(f'Qdrant health check failed at {qdrant_host}:{qdrant_port}')
    except Exception as e:
        logger.warning(f'Cannot connect to Qdrant at {qdrant_host}:{qdrant_port}: {e}')


def start_server():
    """Khởi động server."""
    port = int(os.environ.get("SEARCH_AGENT_PORT", "8001"))
    host = os.environ.get("SEARCH_AGENT_HOST", "0.0.0.0")
    
    # Sửa đường dẫn module để phù hợp với cấu trúc thư mục
    uvicorn.run(
        "app.agents.search_agent.run_server:app",
        host=host,
        port=port,
        reload=True
    )

if __name__ == "__main__":
    # Xử lý các tham số dòng lệnh
    logger.info(f"🚀 Starting Search Agent A2A server on localhost:10002")
    logger.info(f"📋 Agent Card: http://localhost:10002/.well-known/agent.json")
    logger.info(f"🔗 A2A Endpoint: http://localhost:10002/")
    logger.info(f"🔍 Ready for product search queries!")
    logger.info(f"🖼️  Supports: Text search, Image search, Multimodal search")
    
    a2a_server = create_a2a_server("localhost", 10002)
    uvicorn.run(a2a_server.build(), host="localhost", port=10002)
    
    # uvicorn.run(
    #         "run_server:app",
    #         host="localhost",
    #         port=8001,
    #         reload=False
    #     ) 
        
        # # Lưu thông tin host và port vào môi trường
        # os.environ["SEARCH_AGENT_HOST"] = "localhost"
        # os.environ["SEARCH_AGENT_PORT"] = str(10002)
        
        # # Khởi động FastAPI server với tham số từ dòng lệnh
        # uvicorn.run(
        #     "app.agents.search_agent.run_server:app",
        #     host="localhost",
        #     port=10002,
        #     reload=False
        # )