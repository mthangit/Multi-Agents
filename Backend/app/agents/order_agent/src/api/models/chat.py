from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ChatRequest(BaseModel):
    message: str = Field(..., description="Tin nhắn từ người dùng")
    session_id: Optional[str] = Field(None, description="ID phiên hội thoại (nếu có)")
    stream: bool = Field(False, description="Bật streaming response")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Câu trả lời của chatbot")
    session_id: str = Field(..., description="ID phiên hội thoại")

class ChatResponseChunk(BaseModel):
    chunk: str = Field(..., description="Một phần của câu trả lời")
    session_id: str = Field(..., description="ID phiên hội thoại")
    done: bool = Field(False, description="Xác định đây có phải chunk cuối cùng")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Siêu dữ liệu kèm theo chunk") 