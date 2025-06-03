from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import uuid
from datetime import datetime

from src.api.models.a2a_models import (
    AgentInfo, AgentRegistrationRequest, AgentDiscoveryRequest, 
    AgentDiscoveryResponse, A2AMessage, A2AResponse, 
    BroadcastMessage, HeartbeatMessage, MessageType
)
from src.a2a.registry import get_agent_registry
from src.a2a.message_broker import get_message_broker
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/a2a", tags=["Agent-to-Agent"])

@router.post("/register", response_model=dict)
async def register_agent(request: AgentRegistrationRequest):
    """
    Đăng ký một agent vào hệ thống A2A
    """
    try:
        registry = await get_agent_registry()
        success = await registry.register_agent(request.agent_info)
        
        if success:
            return {
                "success": True,
                "message": f"Agent {request.agent_info.agent_id} registered successfully",
                "agent_id": request.agent_info.agent_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to register agent")
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/unregister/{agent_id}")
async def unregister_agent(agent_id: str):
    """
    Hủy đăng ký một agent khỏi hệ thống
    """
    try:
        registry = await get_agent_registry()
        success = await registry.unregister_agent(agent_id)
        
        if success:
            return {
                "success": True,
                "message": f"Agent {agent_id} unregistered successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
            
    except Exception as e:
        logger.error(f"Unregistration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/discover", response_model=AgentDiscoveryResponse)
async def discover_agents(request: AgentDiscoveryRequest):
    """
    Tìm kiếm các agents trong hệ thống theo điều kiện
    """
    try:
        registry = await get_agent_registry()
        result = await registry.discover_agents(request)
        return result
        
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents", response_model=List[AgentInfo])
async def list_all_agents():
    """
    Lấy danh sách tất cả agents đang hoạt động
    """
    try:
        registry = await get_agent_registry()
        from src.api.models.a2a_models import AgentDiscoveryRequest
        
        request = AgentDiscoveryRequest(status="active")
        result = await registry.discover_agents(request)
        return result.agents
        
    except Exception as e:
        logger.error(f"List agents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}", response_model=AgentInfo)
async def get_agent_info(agent_id: str):
    """
    Lấy thông tin chi tiết của một agent
    """
    try:
        registry = await get_agent_registry()
        agent_info = await registry.get_agent_info(agent_id)
        
        if agent_info:
            return agent_info
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get agent info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send", response_model=A2AResponse)
async def send_message(message: A2AMessage):
    """
    Gửi message tới agent khác
    """
    try:
        # Tạo message ID nếu chưa có
        if not message.message_id:
            message.message_id = str(uuid.uuid4())
        
        # Tạo correlation ID nếu là request
        if message.message_type == MessageType.REQUEST and not message.correlation_id:
            message.correlation_id = str(uuid.uuid4())
        
        broker = await get_message_broker()
        response = await broker.send_message(message)
        
        return response
        
    except Exception as e:
        logger.error(f"Send message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/broadcast", response_model=A2AResponse)
async def broadcast_message(broadcast: BroadcastMessage):
    """
    Broadcast message tới tất cả agents phù hợp
    """
    try:
        # Tạo A2A message từ broadcast request
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            from_agent_id=broadcast.from_agent_id,
            to_agent_id=None,  # None để broadcast
            message_type=broadcast.message_type,
            payload=broadcast.payload,
            metadata={
                "target_agent_types": [t.value for t in broadcast.target_agent_types] if broadcast.target_agent_types else None,
                "exclude_agents": broadcast.exclude_agents
            }
        )
        
        broker = await get_message_broker()
        response = await broker.send_message(message)
        
        return response
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/heartbeat")
async def update_heartbeat(heartbeat: HeartbeatMessage):
    """
    Cập nhật heartbeat của agent
    """
    try:
        registry = await get_agent_registry()
        success = await registry.update_heartbeat(heartbeat)
        
        if success:
            return {
                "success": True,
                "message": "Heartbeat updated successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Heartbeat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/receive", response_model=A2AResponse)
async def receive_message(message: A2AMessage):
    """
    Endpoint để nhận messages từ agents khác (khi dùng HTTP transport)
    """
    try:
        broker = await get_message_broker()
        
        # Xử lý message nhận được
        start_time = datetime.now()
        
        # Tìm handler và xử lý
        if message.capability and message.capability in broker.message_handlers:
            handler = broker.message_handlers[message.capability]
            result = await handler(message.payload)
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return A2AResponse(
                message_id=message.message_id,
                correlation_id=message.correlation_id or str(uuid.uuid4()),
                success=True,
                data=result,
                processing_time_ms=processing_time
            )
        else:
            return A2AResponse(
                message_id=message.message_id,
                correlation_id=message.correlation_id or str(uuid.uuid4()),
                success=False,
                error=f"No handler for capability: {message.capability}"
            )
            
    except Exception as e:
        logger.error(f"Receive message error: {e}")
        return A2AResponse(
            message_id=message.message_id,
            correlation_id=message.correlation_id or str(uuid.uuid4()),
            success=False,
            error=str(e)
        )

@router.get("/health")
async def health_check():
    """
    Health check cho A2A server
    """
    try:
        # Kiểm tra kết nối Redis
        registry = await get_agent_registry()
        broker = await get_message_broker()
        
        # Test kết nối
        await registry.redis.ping()
        await broker.redis.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "registry": "connected",
                "message_broker": "connected"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@router.get("/stats")
async def get_stats():
    """
    Lấy thống kê về hệ thống A2A
    """
    try:
        registry = await get_agent_registry()
        
        # Đếm số agents theo type
        from src.api.models.a2a_models import AgentType, AgentDiscoveryRequest
        
        stats = {
            "total_agents": 0,
            "active_agents": 0,
            "agents_by_type": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Lấy tất cả agents
        all_request = AgentDiscoveryRequest()
        all_result = await registry.discover_agents(all_request)
        stats["total_agents"] = all_result.total_count
        
        # Lấy active agents
        active_request = AgentDiscoveryRequest(status="active")
        active_result = await registry.discover_agents(active_request)
        stats["active_agents"] = active_result.total_count
        
        # Đếm theo type
        for agent_type in AgentType:
            type_request = AgentDiscoveryRequest(agent_type=agent_type, status="active")
            type_result = await registry.discover_agents(type_request)
            stats["agents_by_type"][agent_type.value] = type_result.total_count
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 