from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    """Định nghĩa các loại agent trong hệ thống"""
    CHATBOT = "chatbot"
    ORDER_PROCESSOR = "order_processor"
    INVENTORY_MANAGER = "inventory_manager"
    PAYMENT_PROCESSOR = "payment_processor"
    NOTIFICATION_AGENT = "notification_agent"
    ANALYTICS_AGENT = "analytics_agent"
    CUSTOM = "custom"

class MessageType(str, Enum):
    """Định nghĩa các loại message giữa các agents"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    ERROR = "error"

class AgentCapability(BaseModel):
    """Định nghĩa khả năng của một agent"""
    name: str = Field(..., description="Tên chức năng")
    description: str = Field(..., description="Mô tả chức năng")
    input_schema: Dict[str, Any] = Field(..., description="Schema đầu vào")
    output_schema: Dict[str, Any] = Field(..., description="Schema đầu ra")
    requires_auth: bool = Field(False, description="Có yêu cầu xác thực không")

class AgentInfo(BaseModel):
    """Thông tin về một agent trong hệ thống"""
    agent_id: str = Field(..., description="ID duy nhất của agent")
    name: str = Field(..., description="Tên agent")
    agent_type: AgentType = Field(..., description="Loại agent")
    version: str = Field("1.0.0", description="Phiên bản agent")
    description: str = Field("", description="Mô tả agent")
    capabilities: List[AgentCapability] = Field([], description="Danh sách khả năng")
    endpoint: str = Field(..., description="Endpoint để giao tiếp với agent")
    status: str = Field("active", description="Trạng thái agent")
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field({}, description="Metadata bổ sung")

class A2AMessage(BaseModel):
    """Message được gửi giữa các agents"""
    message_id: str = Field(..., description="ID duy nhất của message")
    from_agent_id: str = Field(..., description="ID agent gửi")
    to_agent_id: Optional[str] = Field(None, description="ID agent nhận (None nếu broadcast)")
    message_type: MessageType = Field(..., description="Loại message")
    capability: Optional[str] = Field(None, description="Chức năng được yêu cầu")
    payload: Dict[str, Any] = Field(..., description="Nội dung message")
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: Optional[str] = Field(None, description="ID để liên kết request/response")
    timeout_seconds: int = Field(30, description="Thời gian timeout")
    metadata: Dict[str, Any] = Field({}, description="Metadata bổ sung")

class A2AResponse(BaseModel):
    """Response trả về từ A2A message"""
    message_id: str = Field(..., description="ID của message gốc")
    correlation_id: str = Field(..., description="ID liên kết với request")
    success: bool = Field(..., description="Thành công hay không")
    data: Optional[Dict[str, Any]] = Field(None, description="Dữ liệu trả về")
    error: Optional[str] = Field(None, description="Thông báo lỗi nếu có")
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[int] = Field(None, description="Thời gian xử lý (ms)")

class AgentRegistrationRequest(BaseModel):
    """Request đăng ký agent vào hệ thống"""
    agent_info: AgentInfo = Field(..., description="Thông tin agent")
    auth_token: Optional[str] = Field(None, description="Token xác thực")

class AgentDiscoveryRequest(BaseModel):
    """Request tìm kiếm agents trong hệ thống"""
    agent_type: Optional[AgentType] = Field(None, description="Lọc theo loại agent")
    capability: Optional[str] = Field(None, description="Lọc theo khả năng")
    status: Optional[str] = Field("active", description="Lọc theo trạng thái")

class AgentDiscoveryResponse(BaseModel):
    """Response cho discovery request"""
    agents: List[AgentInfo] = Field(..., description="Danh sách agents tìm thấy")
    total_count: int = Field(..., description="Tổng số agents")

class BroadcastMessage(BaseModel):
    """Message broadcast tới tất cả agents"""
    from_agent_id: str = Field(..., description="ID agent gửi")
    message_type: MessageType = Field(MessageType.BROADCAST)
    payload: Dict[str, Any] = Field(..., description="Nội dung broadcast")
    target_agent_types: Optional[List[AgentType]] = Field(None, description="Chỉ gửi tới các loại agent cụ thể")
    exclude_agents: Optional[List[str]] = Field(None, description="Loại trừ các agents cụ thể")

class HeartbeatMessage(BaseModel):
    """Heartbeat message để duy trì trạng thái agent"""
    agent_id: str = Field(..., description="ID agent")
    status: str = Field("active", description="Trạng thái hiện tại")
    load_percentage: Optional[float] = Field(None, description="Tỷ lệ tải hiện tại")
    active_connections: Optional[int] = Field(None, description="Số kết nối đang hoạt động")
    metadata: Dict[str, Any] = Field({}, description="Metadata bổ sung") 