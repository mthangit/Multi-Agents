import os
import json
import base64
import asyncio
import logging
from typing import Dict, List, Optional, Any

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from common.types import (
    Task, 
    TaskState, 
    TaskSendParams, 
    TaskStatusUpdateEvent, 
    TaskArtifactUpdateEvent,
    Message,
    TextPart,
    DataPart,
    FilePart,
    TaskStatus,
    Artifact
)

from ..agent import SearchAgent

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Search Agent API",
    description="API cho agent tìm kiếm sản phẩm kính mắt",
    version="1.0.0"
)

# CORS middleware cho phép truy cập từ frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo SearchAgent
api_key = os.environ.get("GOOGLE_API_KEY")
search_agent = SearchAgent(api_key=api_key, streaming=True)

# Route cho agent card theo định dạng A2A
@app.get("/.well-known/agent.json")
@app.post("/.well-known/agent.json")
async def get_agent_card():
    """Trả về Agent Card theo định dạng A2A."""
    from .card import get_agent_card
    return get_agent_card().model_dump()

# Route chính cho A2A API
@app.post("/")
async def handle_task(request: Request):
    """Xử lý request JSON-RPC từ host agent."""
    try:
        # Parse request data
        data = await request.json()
        logger.info(f"Nhận request A2A: {data.get('method')}")
        
        # Kiểm tra phương thức JSON-RPC
        method = data.get("method")
        
        # Streaming endpoint
        if method == "tasks/sendSubscribe":
            return StreamingResponse(
                stream_response(data),
                media_type="text/event-stream"
            )
        
        # Non-streaming endpoint
        elif method == "tasks/send":
            return await handle_send_task(data)
        
        # Phương thức không được hỗ trợ
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method {method} not supported"
                    }
                }
            )
    except Exception as e:
        logger.error(f"Lỗi xử lý request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": data.get("id") if isinstance(data, dict) else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
        )

async def handle_send_task(data: Dict) -> JSONResponse:
    """Xử lý yêu cầu tìm kiếm non-streaming."""
    # Trích xuất thông tin từ request
    params = data.get("params", {})
    task_id = params.get("id")
    message = params.get("message", {})
    
    # Trích xuất thông tin từ message parts
    query_text, image_data, analysis_result = extract_message_parts(message)
    
    # Xử lý yêu cầu tìm kiếm
    result = await search_agent.process_request(
        query_text=query_text, 
        image_data=image_data,
        analysis_result=analysis_result
    )
    
    # Tạo response
    response_message = Message(
        role="agent",
        parts=[DataPart(data=result)],
        metadata=message.get("metadata", {})
    )
    
    task = Task(
        id=task_id,
        sessionId=params.get("sessionId"),
        status=TaskStatus(
            state=TaskState.COMPLETED,
            message=response_message
        ),
        history=[message, response_message]
    )
    
    # Trả về kết quả JSON-RPC
    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": task.model_dump()
        }
    )

async def stream_response(data: Dict):
    """Stream response từ search agent về cho host agent."""
    # Trích xuất thông tin từ request
    params = data.get("params", {})
    task_id = params.get("id")
    session_id = params.get("sessionId")
    message = params.get("message", {})
    
    # Trích xuất thông tin từ message parts
    query_text, image_data, analysis_result = extract_message_parts(message)
    
    # Tạo ID cho response
    response_id = data.get("id")
    
    # Phát event SUBMITTED
    yield format_sse_event({
        "jsonrpc": "2.0",
        "id": response_id,
        "result": TaskStatusUpdateEvent(
            id=task_id,
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                message=None
            ),
            final=False
        ).model_dump()
    })
    
    # Phát event WORKING
    yield format_sse_event({
        "jsonrpc": "2.0",
        "id": response_id,
        "result": TaskStatusUpdateEvent(
            id=task_id,
            status=TaskStatus(
                state=TaskState.WORKING,
                message=None
            ),
            final=False
        ).model_dump()
    })
    
    # Tạo kênh truyền streaming
    queue = asyncio.Queue()
    
    # Callback handler để bắt streaming events
    class QueueCallbackHandler:
        def on_llm_new_token(self, token, **kwargs):
            # Bỏ qua token trống
            if token.strip():
                queue.put_nowait(token)
    
    # Xử lý yêu cầu tìm kiếm (async)
    task = asyncio.create_task(
        search_agent.process_request(
            query_text=query_text,
            image_data=image_data,
            analysis_result=analysis_result,
            callbacks=[QueueCallbackHandler()]
        )
    )
    
    # Phát các token streaming trong quá trình xử lý
    try:
        # Stream các token trung gian
        counter = 0
        accumulated_text = ""
        while not task.done() or not queue.empty():
            try:
                # Lấy token từ queue với timeout
                token = await asyncio.wait_for(queue.get(), timeout=0.1)
                accumulated_text += token
                counter += 1
                
                # Gửi event mỗi 5 token hoặc khi có dấu câu
                if counter >= 5 or any(p in token for p in ".!?。"):
                    # Tạo artifact event
                    artifact_event = TaskArtifactUpdateEvent(
                        id=task_id,
                        artifact=Artifact(
                            name="partial_result",
                            parts=[TextPart(text=accumulated_text)],
                            index=counter,
                            append=True,
                            lastChunk=False
                        )
                    )
                    
                    # Phát event
                    yield format_sse_event({
                        "jsonrpc": "2.0",
                        "id": response_id,
                        "result": artifact_event.model_dump()
                    })
                    
                    # Reset counter và accumulated text
                    counter = 0
                    accumulated_text = ""
            except asyncio.TimeoutError:
                # Timeout đọc queue, kiểm tra nếu task đã hoàn thành
                if task.done():
                    break
        
        # Đợi task hoàn thành
        result = await task
        
        # Phát event cuối cùng với kết quả
        response_message = Message(
            role="agent",
            parts=[DataPart(data=result)],
            metadata=message.get("metadata", {})
        )
        
        # Phát event COMPLETED
        yield format_sse_event({
            "jsonrpc": "2.0",
            "id": response_id,
            "result": TaskStatusUpdateEvent(
                id=task_id,
                status=TaskStatus(
                    state=TaskState.COMPLETED,
                    message=response_message
                ),
                final=True
            ).model_dump()
        })
    except Exception as e:
        logger.error(f"Lỗi khi stream response: {str(e)}")
        # Phát event FAILED nếu có lỗi
        yield format_sse_event({
            "jsonrpc": "2.0",
            "id": response_id,
            "result": TaskStatusUpdateEvent(
                id=task_id,
                status=TaskStatus(
                    state=TaskState.FAILED,
                    message=Message(
                        role="agent",
                        parts=[TextPart(text=f"Lỗi: {str(e)}")],
                        metadata=message.get("metadata", {})
                    )
                ),
                final=True
            ).model_dump()
        })

def extract_message_parts(message: Dict) -> tuple:
    """Trích xuất query text, image data và analysis result từ message parts."""
    query_text = None
    image_data = None
    analysis_result = None
    
    for part in message.get("parts", []):
        if part.get("type") == "text":
            query_text = part.get("text")
        elif part.get("type") == "file" and part.get("file", {}).get("mimeType", "").startswith("image/"):
            try:
                # Decode base64 image data
                file_bytes = part.get("file", {}).get("bytes", "")
                if file_bytes:
                    image_data = base64.b64decode(file_bytes)
            except Exception as e:
                logger.error(f"Lỗi khi decode image data: {str(e)}")
        elif part.get("type") == "data":
            analysis_result = part.get("data")
    
    return query_text, image_data, analysis_result

def format_sse_event(data: Dict) -> str:
    """Format dữ liệu thành SSE event."""
    return f"data: {json.dumps(data)}\n\n"

if __name__ == "__main__":
    import uvicorn
    
    # Khởi động server
    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port) 