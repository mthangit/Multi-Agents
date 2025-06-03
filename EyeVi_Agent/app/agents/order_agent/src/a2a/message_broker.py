import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import aioredis
import httpx
from src.api.models.a2a_models import (
    A2AMessage, A2AResponse, MessageType, BroadcastMessage
)
from src.a2a.registry import get_agent_registry
import logging

logger = logging.getLogger(__name__)

class MessageBroker:
    """
    Message Broker để route messages giữa các agents
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.running = False
        
    async def connect(self):
        """Kết nối tới Redis"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Message broker connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect message broker to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Ngắt kết nối Redis"""
        self.running = False
        if self.redis:
            await self.redis.close()
    
    async def start_message_listener(self, agent_id: str):
        """
        Bắt đầu lắng nghe messages cho agent
        """
        self.running = True
        queue_name = f"agent_queue:{agent_id}"
        
        logger.info(f"Starting message listener for agent {agent_id}")
        
        while self.running:
            try:
                # Lắng nghe messages với timeout
                result = await self.redis.blpop(queue_name, timeout=1)
                
                if result:
                    _, message_data = result
                    await self._process_received_message(message_data)
                    
            except Exception as e:
                logger.error(f"Error in message listener: {e}")
                await asyncio.sleep(1)  # Tránh loop quá nhanh khi có lỗi
    
    async def send_message(self, message: A2AMessage) -> Optional[A2AResponse]:
        """
        Gửi message tới agent khác
        """
        try:
            registry = await get_agent_registry()
            
            if message.to_agent_id:
                # Gửi tới agent cụ thể
                target_agent = await registry.get_agent_info(message.to_agent_id)
                if not target_agent:
                    return A2AResponse(
                        message_id=message.message_id,
                        correlation_id=message.correlation_id or str(uuid.uuid4()),
                        success=False,
                        error=f"Target agent {message.to_agent_id} not found"
                    )
                
                return await self._send_to_agent(message, target_agent.endpoint)
            else:
                # Broadcast message
                return await self._broadcast_message(message)
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return A2AResponse(
                message_id=message.message_id,
                correlation_id=message.correlation_id or str(uuid.uuid4()),
                success=False,
                error=str(e)
            )
    
    async def _send_to_agent(self, message: A2AMessage, agent_endpoint: str) -> A2AResponse:
        """
        Gửi message tới endpoint của agent
        """
        try:
            # Nếu là local queue (cùng server)
            if agent_endpoint.startswith("queue://"):
                queue_name = f"agent_queue:{message.to_agent_id}"
                await self.redis.rpush(queue_name, json.dumps(message.dict(), default=str))
                
                # Nếu cần response, đợi response
                if message.message_type == MessageType.REQUEST:
                    return await self._wait_for_response(message)
                else:
                    return A2AResponse(
                        message_id=message.message_id,
                        correlation_id=message.correlation_id or str(uuid.uuid4()),
                        success=True,
                        data={"status": "message_queued"}
                    )
            
            # Nếu là HTTP endpoint
            else:
                async with httpx.AsyncClient(timeout=message.timeout_seconds) as client:
                    response = await client.post(
                        f"{agent_endpoint}/a2a/receive",
                        json=message.dict(default=str)
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        return A2AResponse(**response_data)
                    else:
                        return A2AResponse(
                            message_id=message.message_id,
                            correlation_id=message.correlation_id or str(uuid.uuid4()),
                            success=False,
                            error=f"HTTP {response.status_code}: {response.text}"
                        )
                        
        except Exception as e:
            logger.error(f"Failed to send message to agent: {e}")
            return A2AResponse(
                message_id=message.message_id,
                correlation_id=message.correlation_id or str(uuid.uuid4()),
                success=False,
                error=str(e)
            )
    
    async def _broadcast_message(self, message: A2AMessage) -> A2AResponse:
        """
        Broadcast message tới tất cả agents phù hợp
        """
        try:
            registry = await get_agent_registry()
            
            # Tìm tất cả agents active
            from src.api.models.a2a_models import AgentDiscoveryRequest
            discovery_request = AgentDiscoveryRequest(status="active")
            discovery_result = await registry.discover_agents(discovery_request)
            
            broadcast_count = 0
            errors = []
            
            for agent in discovery_result.agents:
                # Không gửi lại cho chính agent gửi
                if agent.agent_id == message.from_agent_id:
                    continue
                
                try:
                    # Tạo message copy cho mỗi agent
                    agent_message = A2AMessage(
                        message_id=str(uuid.uuid4()),
                        from_agent_id=message.from_agent_id,
                        to_agent_id=agent.agent_id,
                        message_type=message.message_type,
                        capability=message.capability,
                        payload=message.payload,
                        correlation_id=message.correlation_id,
                        timeout_seconds=message.timeout_seconds,
                        metadata=message.metadata
                    )
                    
                    await self._send_to_agent(agent_message, agent.endpoint)
                    broadcast_count += 1
                    
                except Exception as e:
                    errors.append(f"Failed to send to {agent.agent_id}: {str(e)}")
            
            return A2AResponse(
                message_id=message.message_id,
                correlation_id=message.correlation_id or str(uuid.uuid4()),
                success=True,
                data={
                    "broadcast_count": broadcast_count,
                    "errors": errors
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            return A2AResponse(
                message_id=message.message_id,
                correlation_id=message.correlation_id or str(uuid.uuid4()),
                success=False,
                error=str(e)
            )
    
    async def _wait_for_response(self, message: A2AMessage) -> A2AResponse:
        """
        Đợi response cho request message
        """
        try:
            correlation_id = message.correlation_id or str(uuid.uuid4())
            
            # Tạo Future để đợi response
            future = asyncio.Future()
            self.pending_responses[correlation_id] = future
            
            try:
                # Đợi response với timeout
                response = await asyncio.wait_for(future, timeout=message.timeout_seconds)
                return response
            except asyncio.TimeoutError:
                return A2AResponse(
                    message_id=message.message_id,
                    correlation_id=correlation_id,
                    success=False,
                    error="Request timeout"
                )
            finally:
                # Cleanup
                self.pending_responses.pop(correlation_id, None)
                
        except Exception as e:
            logger.error(f"Error waiting for response: {e}")
            return A2AResponse(
                message_id=message.message_id,
                correlation_id=message.correlation_id or str(uuid.uuid4()),
                success=False,
                error=str(e)
            )
    
    async def _process_received_message(self, message_data: str):
        """
        Xử lý message nhận được
        """
        try:
            message_dict = json.loads(message_data)
            
            # Phân biệt message vs response
            if 'correlation_id' in message_dict and message_dict.get('success') is not None:
                # Đây là response
                response = A2AResponse(**message_dict)
                await self._handle_response(response)
            else:
                # Đây là message
                message = A2AMessage(**message_dict)
                await self._handle_message(message)
                
        except Exception as e:
            logger.error(f"Failed to process received message: {e}")
    
    async def _handle_response(self, response: A2AResponse):
        """
        Xử lý response nhận được
        """
        correlation_id = response.correlation_id
        
        if correlation_id in self.pending_responses:
            future = self.pending_responses[correlation_id]
            if not future.done():
                future.set_result(response)
    
    async def _handle_message(self, message: A2AMessage):
        """
        Xử lý message nhận được
        """
        try:
            # Tìm handler cho capability
            if message.capability and message.capability in self.message_handlers:
                handler = self.message_handlers[message.capability]
                response_data = await handler(message.payload)
                
                # Gửi response nếu cần
                if message.message_type == MessageType.REQUEST and message.correlation_id:
                    response = A2AResponse(
                        message_id=message.message_id,
                        correlation_id=message.correlation_id,
                        success=True,
                        data=response_data
                    )
                    await self._send_response(response, message.from_agent_id)
            else:
                logger.warning(f"No handler found for capability: {message.capability}")
                
                # Gửi error response
                if message.message_type == MessageType.REQUEST and message.correlation_id:
                    response = A2AResponse(
                        message_id=message.message_id,
                        correlation_id=message.correlation_id,
                        success=False,
                        error=f"No handler for capability: {message.capability}"
                    )
                    await self._send_response(response, message.from_agent_id)
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
            # Gửi error response
            if message.message_type == MessageType.REQUEST and message.correlation_id:
                response = A2AResponse(
                    message_id=message.message_id,
                    correlation_id=message.correlation_id,
                    success=False,
                    error=str(e)
                )
                await self._send_response(response, message.from_agent_id)
    
    async def _send_response(self, response: A2AResponse, to_agent_id: str):
        """
        Gửi response về cho agent
        """
        try:
            queue_name = f"agent_queue:{to_agent_id}"
            await self.redis.rpush(queue_name, json.dumps(response.dict(), default=str))
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
    
    def register_handler(self, capability: str, handler: Callable):
        """
        Đăng ký handler cho một capability
        """
        self.message_handlers[capability] = handler
        logger.info(f"Registered handler for capability: {capability}")
    
    def unregister_handler(self, capability: str):
        """
        Hủy đăng ký handler
        """
        if capability in self.message_handlers:
            del self.message_handlers[capability]
            logger.info(f"Unregistered handler for capability: {capability}")

# Singleton instance
_message_broker = None

async def get_message_broker() -> MessageBroker:
    """
    Lấy instance của MessageBroker (singleton pattern)
    """
    global _message_broker
    if _message_broker is None:
        _message_broker = MessageBroker()
        await _message_broker.connect()
    return _message_broker 