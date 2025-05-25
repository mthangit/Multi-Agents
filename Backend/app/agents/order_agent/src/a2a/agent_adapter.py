import asyncio
import uuid
import socket
from typing import Dict, Any, List
from datetime import datetime

from src.api.models.a2a_models import (
    AgentInfo, AgentType, AgentCapability, AgentRegistrationRequest,
    HeartbeatMessage, A2AMessage, MessageType
)
from src.a2a.registry import get_agent_registry
from src.a2a.message_broker import get_message_broker
from src.chatbot.langgraph_bot import ChatbotGraph
import logging

logger = logging.getLogger(__name__)

class ChatbotA2AAdapter:
    """
    Adapter để tích hợp chatbot hiện tại với hệ thống A2A
    """
    
    def __init__(self, chatbot: ChatbotGraph, server_host: str = "localhost", server_port: int = 8000):
        self.chatbot = chatbot
        self.agent_id = f"chatbot_{socket.gethostname()}_{uuid.uuid4().hex[:8]}"
        self.server_host = server_host
        self.server_port = server_port
        self.heartbeat_task = None
        self.message_listener_task = None
        self.registered = False
        
    async def register_agent(self) -> bool:
        """
        Đăng ký agent vào hệ thống A2A
        """
        try:
            # Định nghĩa capabilities của chatbot
            capabilities = [
                AgentCapability(
                    name="chat",
                    description="Xử lý tin nhắn chat từ người dùng",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "Tin nhắn từ người dùng"},
                            "session_id": {"type": "string", "description": "ID phiên hội thoại"}
                        },
                        "required": ["message"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "response": {"type": "string", "description": "Câu trả lời của chatbot"},
                            "session_id": {"type": "string", "description": "ID phiên hội thoại"}
                        }
                    },
                    requires_auth=False
                ),
                AgentCapability(
                    name="process_order",
                    description="Xử lý yêu cầu đặt hàng từ tin nhắn",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "Tin nhắn chứa yêu cầu đặt hàng"},
                            "customer_info": {"type": "object", "description": "Thông tin khách hàng"}
                        },
                        "required": ["message"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string", "description": "ID đơn hàng được tạo"},
                            "status": {"type": "string", "description": "Trạng thái xử lý"},
                            "details": {"type": "object", "description": "Chi tiết đơn hàng"}
                        }
                    },
                    requires_auth=False
                ),
                AgentCapability(
                    name="get_order_status",
                    description="Kiểm tra trạng thái đơn hàng",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string", "description": "ID đơn hàng cần kiểm tra"}
                        },
                        "required": ["order_id"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string"},
                            "status": {"type": "string"},
                            "details": {"type": "object"}
                        }
                    },
                    requires_auth=False
                )
            ]
            
            # Tạo thông tin agent
            agent_info = AgentInfo(
                agent_id=self.agent_id,
                name="Order Management Chatbot",
                agent_type=AgentType.CHATBOT,
                version="1.0.0",
                description="Chatbot xử lý đơn hàng và tương tác khách hàng",
                capabilities=capabilities,
                endpoint=f"queue://{self.agent_id}",  # Sử dụng Redis queue
                status="active",
                metadata={
                    "server_host": self.server_host,
                    "server_port": self.server_port,
                    "registration_time": datetime.now().isoformat()
                }
            )
            
            # Đăng ký vào registry
            registry = await get_agent_registry()
            success = await registry.register_agent(agent_info)
            
            if success:
                self.registered = True
                
                # Đăng ký message handlers
                await self._register_message_handlers()
                
                # Bắt đầu heartbeat
                await self._start_heartbeat()
                
                # Bắt đầu message listener
                await self._start_message_listener()
                
                logger.info(f"Agent {self.agent_id} registered successfully")
                return True
            else:
                logger.error(f"Failed to register agent {self.agent_id}")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    async def unregister_agent(self):
        """
        Hủy đăng ký agent
        """
        try:
            if self.registered:
                # Dừng heartbeat
                if self.heartbeat_task:
                    self.heartbeat_task.cancel()
                
                # Dừng message listener
                if self.message_listener_task:
                    self.message_listener_task.cancel()
                
                # Hủy đăng ký khỏi registry
                registry = await get_agent_registry()
                await registry.unregister_agent(self.agent_id)
                
                self.registered = False
                logger.info(f"Agent {self.agent_id} unregistered successfully")
                
        except Exception as e:
            logger.error(f"Unregistration error: {e}")
    
    async def _register_message_handlers(self):
        """
        Đăng ký các message handlers
        """
        broker = await get_message_broker()
        
        # Handler cho capability "chat"
        broker.register_handler("chat", self._handle_chat_message)
        
        # Handler cho capability "process_order"
        broker.register_handler("process_order", self._handle_process_order)
        
        # Handler cho capability "get_order_status"
        broker.register_handler("get_order_status", self._handle_get_order_status)
        
        logger.info("Message handlers registered")
    
    async def _handle_chat_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý tin nhắn chat
        """
        try:
            message = payload.get("message", "")
            session_id = payload.get("session_id", str(uuid.uuid4()))
            
            # Sử dụng chatbot hiện tại để xử lý
            response = self.chatbot.process_message(message, session_id)
            
            return {
                "response": response,
                "session_id": session_id,
                "processed_by": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            raise
    
    async def _handle_process_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý yêu cầu đặt hàng
        """
        try:
            message = payload.get("message", "")
            customer_info = payload.get("customer_info", {})
            
            # Tạo context cho xử lý đơn hàng
            order_context = f"Xử lý đơn hàng: {message}"
            if customer_info:
                order_context += f"\nThông tin khách hàng: {customer_info}"
            
            # Sử dụng chatbot để xử lý với context đặc biệt
            session_id = f"order_{uuid.uuid4().hex[:8]}"
            response = self.chatbot.process_message(order_context, session_id)
            
            # Tạo mock order ID (trong thực tế sẽ tích hợp với hệ thống order management)
            order_id = f"ORD_{uuid.uuid4().hex[:8].upper()}"
            
            return {
                "order_id": order_id,
                "status": "processing",
                "details": {
                    "message": message,
                    "customer_info": customer_info,
                    "chatbot_response": response,
                    "created_at": datetime.now().isoformat()
                },
                "processed_by": self.agent_id
            }
            
        except Exception as e:
            logger.error(f"Error processing order: {e}")
            raise
    
    async def _handle_get_order_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái đơn hàng
        """
        try:
            order_id = payload.get("order_id", "")
            
            # Mock response (trong thực tế sẽ tích hợp với database)
            # Sử dụng chatbot để tạo response về trạng thái đơn hàng
            query = f"Kiểm tra trạng thái đơn hàng {order_id}"
            session_id = f"status_{uuid.uuid4().hex[:8]}"
            chatbot_response = self.chatbot.process_message(query, session_id)
            
            return {
                "order_id": order_id,
                "status": "shipped",  # Mock status
                "details": {
                    "chatbot_response": chatbot_response,
                    "estimated_delivery": "2-3 ngày",
                    "tracking_number": f"TRK{uuid.uuid4().hex[:8].upper()}",
                    "checked_at": datetime.now().isoformat()
                },
                "processed_by": self.agent_id
            }
            
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            raise
    
    async def _start_heartbeat(self):
        """
        Bắt đầu heartbeat task
        """
        async def heartbeat_loop():
            while self.registered:
                try:
                    registry = await get_agent_registry()
                    heartbeat = HeartbeatMessage(
                        agent_id=self.agent_id,
                        status="active",
                        load_percentage=50.0,  # Mock value
                        active_connections=1,
                        metadata={
                            "last_heartbeat": datetime.now().isoformat()
                        }
                    )
                    
                    await registry.update_heartbeat(heartbeat)
                    await asyncio.sleep(30)  # Heartbeat mỗi 30 giây
                    
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    await asyncio.sleep(5)
        
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    async def _start_message_listener(self):
        """
        Bắt đầu message listener task
        """
        async def listener_loop():
            try:
                broker = await get_message_broker()
                await broker.start_message_listener(self.agent_id)
            except Exception as e:
                logger.error(f"Message listener error: {e}")
        
        self.message_listener_task = asyncio.create_task(listener_loop())
    
    async def send_a2a_message(self, to_agent_id: str, capability: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gửi message tới agent khác
        """
        try:
            message = A2AMessage(
                message_id=str(uuid.uuid4()),
                from_agent_id=self.agent_id,
                to_agent_id=to_agent_id,
                message_type=MessageType.REQUEST,
                capability=capability,
                payload=payload,
                correlation_id=str(uuid.uuid4())
            )
            
            broker = await get_message_broker()
            response = await broker.send_message(message)
            
            return response.dict() if response else {}
            
        except Exception as e:
            logger.error(f"Error sending A2A message: {e}")
            return {"error": str(e)}
    
    async def broadcast_message(self, payload: Dict[str, Any], target_types: List[AgentType] = None):
        """
        Broadcast message tới các agents khác
        """
        try:
            message = A2AMessage(
                message_id=str(uuid.uuid4()),
                from_agent_id=self.agent_id,
                to_agent_id=None,  # Broadcast
                message_type=MessageType.NOTIFICATION,
                payload=payload,
                metadata={
                    "target_agent_types": [t.value for t in target_types] if target_types else None
                }
            )
            
            broker = await get_message_broker()
            response = await broker.send_message(message)
            
            return response.dict() if response else {}
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            return {"error": str(e)} 