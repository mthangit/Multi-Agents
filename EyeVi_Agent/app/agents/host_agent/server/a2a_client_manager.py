"""
A2A Client Manager - Quản lý các A2A clients cho các agent khác nhau
"""

import asyncio
import logging
import httpx
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4

import aioredis
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import SendMessageRequest, SendStreamingMessageRequest, MessageSendParams

logger = logging.getLogger(__name__)

class FileInfo:
    """Class để represent file information"""
    def __init__(self, name: str, mime_type: str, data: str):
        self.name = name
        self.mime_type = mime_type
        self.data = data  # base64 encoded

class ChatHistory:
    """Quản lý lịch sử chat cho mỗi session"""
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def add_message(self, role: str, content: str, agent_used: Optional[str] = None, user_id: Optional[str] = None):
        """Thêm message vào lịch sử"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "message_id": uuid4().hex
        }
        if agent_used:
            message["agent_used"] = agent_used
        if user_id:
            message["user_id"] = user_id
            
        self.messages.append(message)
        self.last_updated = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy các message gần đây"""
        return self.messages[-limit:] if self.messages else []
    
    def get_context_string(self, limit: int = 5) -> str:
        """Tạo context string từ lịch sử chat"""
        recent_messages = self.get_recent_messages(limit)
        context_parts = []
        
        for msg in recent_messages:
            role_display = "User" if msg["role"] == "user" else "Assistant"
            if msg.get("agent_used"):
                role_display += f" ({msg['agent_used']})"
            context_parts.append(f"{role_display}: {msg['content']}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize ChatHistory thành dict để lưu vào Redis"""
        return {
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatHistory':
        """Deserialize từ dict trong Redis"""
        chat_history = cls()
        chat_history.messages = data.get("messages", [])
        chat_history.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        chat_history.last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        return chat_history

class A2AAgentClient:
    """Wrapper class cho một A2A client cụ thể"""
    
    def __init__(self, agent_name: str, base_url: str):
        self.agent_name = agent_name
        self.base_url = base_url
        self.httpx_client = None
        self.a2a_client = None
        self.agent_card = None
        self.is_initialized = False
        self.last_health_check = None
        self.is_healthy = False

    async def initialize(self):
        """Khởi tạo A2A client"""
        if self.is_initialized:
            return True
            
        try:
            logger.info(f"🔄 Khởi tạo A2A client cho {self.agent_name} tại {self.base_url}")
            
            # Tạo httpx client
            self.httpx_client = httpx.AsyncClient(timeout=30.0)
            
            # Khởi tạo A2ACardResolver để fetch agent card
            resolver = A2ACardResolver(
                httpx_client=self.httpx_client,
                base_url=self.base_url
            )
            
            # Fetch agent card
            self.agent_card = await resolver.get_agent_card()
            
            # Khởi tạo A2A client với agent card
            self.a2a_client = A2AClient(
                httpx_client=self.httpx_client,
                agent_card=self.agent_card
            )
            
            self.is_initialized = True
            self.is_healthy = True
            self.last_health_check = datetime.now()
            
            logger.info(f"✅ {self.agent_name} A2A client khởi tạo thành công")
            logger.info(f"   - Name: {self.agent_card.name}")
            logger.info(f"   - Description: {self.agent_card.description}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi khởi tạo A2A client cho {self.agent_name}: {e}")
            self.is_healthy = False
            return False

    async def send_message(self, message: str, context: Optional[str] = None, files: Optional[List[Any]] = None, user_id: Optional[str] = None) -> str:
        """Gửi message tới agent qua A2A, có thể kèm files"""
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                raise Exception(f"Không thể khởi tạo A2A client cho {self.agent_name}")
        
        try:
            # Chuẩn bị message với context nếu có
            full_message = message
            if context:
                full_message = f"Context từ cuộc hội thoại trước:\n{context}\n\nCâu hỏi hiện tại:\n{message}"
            
            # Chỉ thêm thông tin user_id vào message khi gọi tới Order Agent
            if user_id and self.agent_name == "Order Agent":
                full_message = f"User ID: {user_id}\n\n{full_message}"
            
            # Chuẩn bị parts cho message
            parts = []
            
            # Thêm phần text
            if full_message:
                parts.append({
                    'kind': 'text', 
                    'text': full_message
                })
            
            # Thêm files nếu có
            if files:
                for file_info in files:
                    parts.append({
                        'kind': 'file',
                        'file': {
                            'name': file_info.name,
                            'mimeType': file_info.mime_type,
                            'bytes': file_info.data  # base64 encoded
                        }
                    })
                    logger.info(f"📎 Thêm file vào message: {file_info.name} ({file_info.mime_type})")
            
            # Chuẩn bị message payload theo A2A format
            send_message_payload: Dict[str, Any] = {
                'message': {
                    'role': 'user',
                    'parts': parts,
                    'messageId': uuid4().hex,
                },
            }
            
            # Chỉ thêm user_id vào metadata khi gọi tới Order Agent
            if user_id and self.agent_name == "Order Agent":
                send_message_payload['message']['metadata'] = {'user_id': user_id}
            
            if files:
                logger.info(f"📤 Gửi message với {len(files)} files tới {self.agent_name}: {message[:100]}...")
            else:
                if user_id and self.agent_name == "Order Agent":
                    logger.info(f"📤 Gửi message tới {self.agent_name} với User ID {user_id}: {message[:100]}...")
                else:
                    logger.info(f"📤 Gửi message tới {self.agent_name} qua A2A: {message[:100]}...")
            
            # Tạo request
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            # Gửi message
            response = await self.a2a_client.send_message(
                request=request, 
                http_kwargs={"timeout": None}
            )
            
            # Parse response
            response_data = response.model_dump(mode='json', exclude_none=True)
            
            # Extract content từ response
            content = ""
            if 'result' in response_data:
                result = response_data['result']
                if 'parts' in result:
                    for part in result['parts']:
                        if part.get('kind') == 'text':
                            content += part.get('text', '')
            
            if not content:
                content = "Không có response từ agent"
            
            logger.info(f"📥 Nhận response từ {self.agent_name}: {content[:100]}...")
            return content
            
        except Exception as e:
            error_msg = f"Lỗi khi gửi message tới {self.agent_name}: {str(e)}"
            logger.error(error_msg)
            self.is_healthy = False
            raise Exception(error_msg)

    async def health_check(self) -> bool:
        """Kiểm tra health của agent"""
        try:
            if not self.httpx_client:
                return False
                
            # Kiểm tra endpoint /.well-known/agent.json
            response = await self.httpx_client.get(
                f"{self.base_url}/.well-known/agent.json",
                timeout=5.0
            )
            
            self.is_healthy = response.status_code == 200
            self.last_health_check = datetime.now()
            
            return self.is_healthy
            
        except Exception as e:
            logger.warning(f"⚠️ Health check failed cho {self.agent_name}: {e}")
            self.is_healthy = False
            return False

    async def close(self):
        """Đóng connections"""
        try:
            if self.httpx_client:
                await self.httpx_client.aclose()
            logger.info(f"✅ Đã đóng A2A client cho {self.agent_name}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi đóng A2A client cho {self.agent_name}: {e}")

class A2AClientManager:
    """Quản lý tất cả A2A clients cho các agents khác nhau"""
    
    def __init__(self):
        self.agents: Dict[str, A2AAgentClient] = {}
        self.redis_client: Optional[aioredis.Redis] = None
        self.chat_histories: Dict[str, ChatHistory] = {}  # Fallback cho backward compatibility
        
        # Cấu hình Redis
        self.redis_config = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "password": os.getenv("REDIS_PASSWORD") or None,
            "db": int(os.getenv("REDIS_DB", "0"))
        }
        
        # Cấu hình các agents từ environment variables
        self.agents_config = {
            "Advisor Agent": {
                "url": os.getenv("ADVISOR_AGENT_URL", "http://localhost:10001"),
                "enabled": True
            },
            "Search Agent": {
                "url": os.getenv("SEARCH_AGENT_URL", "http://localhost:10002"),
                "enabled": True
            },
            "Order Agent": {
                "url": os.getenv("ORDER_AGENT_URL", "http://localhost:10003"),
                "enabled": True
            }
        }

    async def initialize(self):
        """Khởi tạo tất cả A2A clients và Redis connection"""
        logger.info("🚀 Khởi tạo A2A Client Manager...")
        
        # Khởi tạo Redis connection
        try:
            self.redis_client = aioredis.from_url(
                f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}",
                password=self.redis_config['password'],
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis connection khởi tạo thành công")
        except Exception as e:
            logger.error(f"❌ Lỗi khi khởi tạo Redis connection: {e}")
            logger.warning("⚠️ Sẽ sử dụng in-memory storage cho chat history")
            self.redis_client = None
        
        for agent_name, config in self.agents_config.items():
            if config["enabled"]:
                self.agents[agent_name] = A2AAgentClient(
                    agent_name=agent_name,
                    base_url=config["url"]
                )
                
                # Thử khởi tạo ngay (không chặn nếu agent không available)
                try:
                    await self.agents[agent_name].initialize()
                except Exception as e:
                    logger.warning(f"⚠️ Không thể khởi tạo {agent_name}: {e}")
        
        logger.info(f"✅ A2A Client Manager đã khởi tạo với {len(self.agents)} agents")

    async def send_message_to_agent(
        self, 
        agent_name: str, 
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        files: Optional[List[Any]] = None
    ) -> str:
        """Gửi message tới agent cụ thể, có thể kèm files"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' không tồn tại")
        
        agent_client = self.agents[agent_name]
        
        # Lấy context từ chat history (sử dụng Redis nếu có user_id)
        context = None
        if session_id:
            if user_id and self.redis_client:
                chat_history = await self._load_chat_history_from_redis(user_id, session_id)
                if chat_history:
                    context = chat_history.get_context_string()
            elif session_id in self.chat_histories:
                context = self.chat_histories[session_id].get_context_string()
        
        # Gửi message với files và user_id
        response = await agent_client.send_message(message, context, files, user_id)
        
        # Lưu vào chat history
        if session_id:
            # Tạo message content bao gồm thông tin về files
            message_content = message
            if files:
                file_names = [f.name for f in files]
                message_content += f" [Đính kèm: {', '.join(file_names)}]"
            
            if user_id and self.redis_client:
                # Sử dụng Redis
                chat_history = await self._ensure_chat_history_with_redis(user_id, session_id)
                chat_history.add_message("user", message_content, user_id=user_id)
                chat_history.add_message("assistant", response, agent_name)
                await self._save_chat_history_to_redis(user_id, session_id, chat_history)
            else:
                # Fallback to in-memory
                self._ensure_chat_history(session_id)
                self.chat_histories[session_id].add_message("user", message_content, user_id=user_id)
                self.chat_histories[session_id].add_message("assistant", response, agent_name)
        
        return response

    def _ensure_chat_history(self, session_id: str):
        """Đảm bảo chat history tồn tại cho session"""
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = ChatHistory()

    def _get_redis_key(self, user_id: str, session_id: str) -> str:
        """Tạo Redis key cho chat history"""
        return f"chat_history:{user_id}:{session_id}"
    
    def _get_user_sessions_pattern(self, user_id: str) -> str:
        """Tạo pattern để tìm tất cả sessions của user"""
        return f"chat_history:{user_id}:*"
    
    async def _save_chat_history_to_redis(self, user_id: str, session_id: str, chat_history: ChatHistory):
        """Lưu chat history vào Redis"""
        if not self.redis_client:
            return
        
        try:
            redis_key = self._get_redis_key(user_id, session_id)
            data = json.dumps(chat_history.to_dict())
            await self.redis_client.set(redis_key, data, ex=86400*7)  # Expire sau 7 ngày
            logger.debug(f"💾 Lưu chat history vào Redis: {redis_key}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi lưu chat history vào Redis: {e}")
    
    async def _load_chat_history_from_redis(self, user_id: str, session_id: str) -> Optional[ChatHistory]:
        """Tải chat history từ Redis"""
        if not self.redis_client:
            return None
        
        try:
            redis_key = self._get_redis_key(user_id, session_id)
            data = await self.redis_client.get(redis_key)
            if data:
                chat_data = json.loads(data)
                return ChatHistory.from_dict(chat_data)
            return None
        except Exception as e:
            logger.error(f"❌ Lỗi khi tải chat history từ Redis: {e}")
            return None
    
    async def _ensure_chat_history_with_redis(self, user_id: str, session_id: str) -> ChatHistory:
        """Đảm bảo chat history tồn tại (sử dụng Redis nếu có)"""
        if self.redis_client and user_id:
            # Thử tải từ Redis trước
            chat_history = await self._load_chat_history_from_redis(user_id, session_id)
            if chat_history:
                return chat_history
            
            # Tạo mới nếu không tìm thấy
            chat_history = ChatHistory()
            await self._save_chat_history_to_redis(user_id, session_id, chat_history)
            return chat_history
        else:
            # Fallback to in-memory
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = ChatHistory()
            return self.chat_histories[session_id]

    async def get_available_agents(self) -> List[str]:
        """Lấy danh sách agents khả dụng"""
        available = []
        for agent_name, agent_client in self.agents.items():
            if agent_client.is_healthy:
                available.append(agent_name)
            else:
                # Thử health check lần nữa
                is_healthy = await agent_client.health_check()
                if is_healthy:
                    available.append(agent_name)
        
        return available

    async def health_check_all(self) -> Dict[str, Any]:
        """Health check tất cả agents"""
        results = {}
        
        for agent_name, agent_client in self.agents.items():
            is_healthy = await agent_client.health_check()
            results[agent_name] = {
                "healthy": is_healthy,
                "url": agent_client.base_url,
                "initialized": agent_client.is_initialized,
                "last_check": agent_client.last_health_check.isoformat() if agent_client.last_health_check else None
            }
        
        return results

    async def get_chat_history(self, user_id: str, session_id: str) -> Optional[ChatHistory]:
        """Lấy chat history cho session (ưu tiên Redis nếu có user_id)"""
        if user_id and self.redis_client:
            return await self._load_chat_history_from_redis(user_id, session_id)
        else:
            return self.chat_histories.get(session_id)
    
    def get_chat_history_fallback(self, session_id: str) -> Optional[ChatHistory]:
        """Lấy chat history từ memory (cho backward compatibility)"""
        return self.chat_histories.get(session_id)

    async def clear_chat_history(self, user_id: str, session_id: str):
        """Xóa chat history cho session"""
        if user_id and self.redis_client:
            try:
                redis_key = self._get_redis_key(user_id, session_id)
                await self.redis_client.delete(redis_key)
                logger.info(f"🗑️ Đã xóa chat history từ Redis: {redis_key}")
            except Exception as e:
                logger.error(f"❌ Lỗi khi xóa chat history từ Redis: {e}")
        
        # Cũng xóa từ memory nếu có
        if session_id in self.chat_histories:
            del self.chat_histories[session_id]
    
    def clear_chat_history_fallback(self, session_id: str):
        """Xóa chat history từ memory (cho backward compatibility)"""
        if session_id in self.chat_histories:
            del self.chat_histories[session_id]
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Lấy danh sách tất cả sessions của user từ Redis"""
        if not user_id or not self.redis_client:
            return []
        
        try:
            pattern = self._get_user_sessions_pattern(user_id)
            keys = await self.redis_client.keys(pattern)
            # Extract session_id từ keys
            sessions = []
            for key in keys:
                # Format: chat_history:user_id:session_id
                parts = key.split(":")
                if len(parts) >= 3:
                    session_id = ":".join(parts[2:])  # Handle session_id có thể chứa ":"
                    sessions.append(session_id)
            return sessions
        except Exception as e:
            logger.error(f"❌ Lỗi khi lấy user sessions từ Redis: {e}")
            return []

    async def cleanup(self):
        """Cleanup tất cả resources"""
        logger.info("🔄 Cleanup A2A Client Manager...")
        
        for agent_name, agent_client in self.agents.items():
            await agent_client.close()
        
        # Đóng Redis connection
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("✅ Redis connection đã đóng")
            except Exception as e:
                logger.error(f"❌ Lỗi khi đóng Redis connection: {e}")
        
        # Clear chat histories (optional)
        self.chat_histories.clear()
        
        logger.info("✅ A2A Client Manager cleanup hoàn tất") 