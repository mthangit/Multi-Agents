from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from src.chatbot.langgraph_bot import ChatbotGraph
from typing import Optional, AsyncIterator
import uuid
import json

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Khởi tạo chatbot
chatbot = ChatbotGraph()

class ChatRequest(BaseModel):
    message: str = Field(..., description="Tin nhắn từ người dùng")
    session_id: Optional[str] = Field(None, description="ID phiên hội thoại (nếu có)")
    stream: bool = Field(False, description="Có phải là yêu cầu streaming không")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Câu trả lời của chatbot")
    session_id: str = Field(..., description="ID phiên hội thoại")

class ChatResponseChunk(BaseModel):
    chunk: str = Field(..., description="Nội dung của chunk")
    session_id: str = Field(..., description="ID phiên hội thoại")
    done: bool = Field(..., description="Có kết thúc không")
    metadata: Optional[dict] = Field(None, description="Metadata của chunk")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint xử lý tin nhắn chat từ người dùng
    """
    try:
        # Tạo session_id mới nếu chưa có
        session_id = request.session_id or str(uuid.uuid4())
        
        # Kiểm tra nếu yêu cầu streaming
        if request.stream:
            return await stream_chat(request)
        
        # Xử lý tin nhắn theo cách thông thường
        response = chatbot.process_message(request.message, session_id)
        
        # Trả về kết quả
        return ChatResponse(
            response=response,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý tin nhắn: {str(e)}")

async def stream_chat(request: ChatRequest) -> StreamingResponse:
    """
    Streaming endpoint cho chat
    """
    # Tạo session_id mới nếu chưa có
    session_id = request.session_id or str(uuid.uuid4())
    
    async def generate() -> AsyncIterator[str]:
        try:
            # Xử lý message với streaming
            async for chunk in chatbot.process_message_streaming(request.message, session_id):
                # Tạo response chunk
                response_chunk = ChatResponseChunk(
                    chunk=chunk,
                    session_id=session_id,
                    done=False
                )
                # Convert to JSON và stream về client
                yield f"data: {json.dumps(response_chunk.dict())}\n\n"
                
            # Khi kết thúc, gửi done=True
            final_chunk = ChatResponseChunk(
                chunk="",
                session_id=session_id,
                done=True
            )
            yield f"data: {json.dumps(final_chunk.dict())}\n\n"
            
        except Exception as e:
            # Gửi error message khi có exception
            error_chunk = ChatResponseChunk(
                chunk=f"Lỗi: {str(e)}",
                session_id=session_id,
                done=True,
                metadata={"error": True}
            )
            yield f"data: {json.dumps(error_chunk.dict())}\n\n"
    
    # Trả về Server-Sent Events response
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    ) 