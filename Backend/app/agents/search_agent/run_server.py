#!/usr/bin/env python
"""
Script khởi động server API cho Search Agent
"""

import os
import logging
import base64
import uvicorn
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import SearchAgent

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
    import argparse
    
    parser = argparse.ArgumentParser(description="Khởi động Search Agent API server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host để lắng nghe")
    parser.add_argument("--port", type=int, default=8001, help="Port để lắng nghe")
    parser.add_argument("--reload", action="store_true", help="Bật chế độ tự động reload")
    
    args = parser.parse_args()
    
    # Lưu thông tin host và port vào môi trường
    os.environ["SEARCH_AGENT_HOST"] = args.host
    os.environ["SEARCH_AGENT_PORT"] = str(args.port)
    
    # Khởi động server với tham số từ dòng lệnh
    uvicorn.run(
        "app.agents.search_agent.run_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    ) 