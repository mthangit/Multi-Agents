from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from src.chatbot.simplified_bot import SimplifiedChatbot
from typing import Optional, AsyncIterator
import uuid
import json

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Khởi tạo chatbot đã được đơn giản hóa
chatbot = SimplifiedChatbot()

class ChatRequest(BaseModel):
    message: str = Field(..., description="Tin nhắn từ người dùng")
    session_id: Optional[str] = Field(None, description="ID phiên hội thoại (nếu có)")
    stream: bool = Field(False, description="Có phải là yêu cầu streaming không")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Câu trả lời của chatbot")
    session_id: str = Field(..., description="ID phiên hội thoại")

# This model is for the chunks sent during streaming
class StreamResponse(BaseModel):
    is_task_complete: bool
    require_user_input: bool
    content: str

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint xử lý tin nhắn chat từ người dùng.
    Hỗ trợ cả chế độ streaming và non-streaming.
    """
    session_id = request.session_id or str(uuid.uuid4())

    if request.stream:
        # The stream method now returns a StreamingResponse directly
        return stream_chat(request, session_id)
    else:
        try:
            # Xử lý tin nhắn theo cách thông thường (non-streaming)
            response_content = chatbot.process_message(request.message, session_id)
            
            # Trả về kết quả
            return ChatResponse(
                response=response_content,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi xử lý tin nhắn: {str(e)}")


def stream_chat(request: ChatRequest, session_id: str) -> StreamingResponse:
    """
    Streaming endpoint cho chat.
    """
    async def generate() -> AsyncIterator[str]:
        try:
            # Sử dụng phương thức stream mới từ SimplifiedChatbot
            async for chunk in chatbot.stream(request.message, session_id):
                # The chunk is now a dict from the simplified bot's stream method
                response_chunk = StreamResponse(**chunk)
                yield f"data: {response_chunk.json()}\n\n"
            
        except Exception as e:
            # Gửi error message khi có exception
            error_chunk = StreamResponse(
                is_task_complete=True,
                require_user_input=False,
                content=f"Lỗi: {str(e)}"
            )
            yield f"data: {error_chunk.json()}\n\n"
            
    # Trả về Server-Sent Events response
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    ) 