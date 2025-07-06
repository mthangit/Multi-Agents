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
import time

import redis.asyncio as aioredis
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import SendMessageRequest, SendStreamingMessageRequest, MessageSendParams
from .redis_optimizations import OptimizedRedisClient, RedisHealthMonitor

from dotenv import load_dotenv
load_dotenv()

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
    
    def add_message(self, role: str, content: str, clarified_content: str, agent_used: Optional[str] = None, user_id: Optional[str] = None):
        """Thêm message vào lịch sử"""
        message = {
            "role": role,
            "content": content,
            "clarified_content": clarified_content,
            "timestamp": datetime.now().isoformat(),
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
        
        # Retry configuration
        self.max_retries = int(os.getenv("AGENT_MAX_RETRIES", "3"))
        self.retry_delay_base = float(os.getenv("AGENT_RETRY_DELAY_BASE", "1.0"))  # seconds
        self.retry_exponential_base = float(os.getenv("AGENT_RETRY_EXPONENTIAL_BASE", "2.0"))

    async def _retry_with_backoff(self, func, func_name: str, *args, **kwargs):
        """Thực hiện retry với exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.retry_delay_base * (self.retry_exponential_base ** (attempt - 1))
                    logger.info(f"🔄 Thử lại lần {attempt}/{self.max_retries} cho {self.agent_name} ({func_name}) sau {delay:.1f}s...")
                    await asyncio.sleep(delay)
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                if attempt == 0:
                    logger.warning(f"⚠️ Lần thử đầu tiên failed cho {self.agent_name} ({func_name}): {str(e)}")
                else:
                    logger.warning(f"⚠️ Lần thử {attempt}/{self.max_retries} failed cho {self.agent_name} ({func_name}): {str(e)}")
                
                if attempt == self.max_retries:
                    logger.error(f"❌ Đã thử {self.max_retries + 1} lần nhưng vẫn fail cho {self.agent_name} ({func_name})")
                    break
        
        # Nếu tất cả retry đều fail
        self.is_healthy = False
        raise last_exception

    async def initialize(self):
        """Khởi tạo A2A client với retry logic"""
        if self.is_initialized:
            return True
        
        async def _do_initialize():
            logger.info(f"🔗 Đang kết nối tới {self.agent_name} tại domain: {self.base_url}")
            
            # Tạo httpx client
            self.httpx_client = httpx.AsyncClient(timeout=120.0)
            
            try:
                logger.info(f"🌐 Kiểm tra kết nối cơ bản tới {self.base_url}")
                test_response = await self.httpx_client.get(f"{self.base_url}/health", timeout=10.0)
                logger.info(f"✅ Kết nối cơ bản thành công tới {self.base_url} (status: {test_response.status_code})")
            except Exception as e:
                logger.warning(f"⚠️ Kết nối cơ bản tới {self.base_url} gặp vấn đề: {e}")
                # Vẫn tiếp tục thử A2A connection
            
            # Khởi tạo A2ACardResolver để fetch agent card
            logger.info(f"🏷️ Đang fetch agent card từ {self.base_url}/.well-known/agent.json")
            resolver = A2ACardResolver(
                httpx_client=self.httpx_client,
                base_url=self.base_url
            )
            
            # Fetch agent card
            self.agent_card = await resolver.get_agent_card()
            logger.info(f"📋 Đã tải agent card thành công cho {self.agent_name}")
            
            # Khởi tạo A2A client với agent card
            logger.info(f"🤖 Đang khởi tạo A2A client cho {self.agent_name}")
            self.a2a_client = A2AClient(
                httpx_client=self.httpx_client,
                agent_card=self.agent_card
            )
            
            self.is_initialized = True
            self.is_healthy = True
            self.last_health_check = datetime.now()
            
            logger.info(f"✅ {self.agent_name} A2A client khởi tạo thành công")
            logger.info(f"   🏷️  Name: {self.agent_card.name}")
            logger.info(f"   📝 Description: {self.agent_card.description}")
            logger.info(f"   🌐 Domain: {self.base_url}")
            
            return True
        
        try:
            return await self._retry_with_backoff(_do_initialize, "initialize")
        except Exception as e:
            logger.error(f"❌ Không thể khởi tạo A2A client cho {self.agent_name} tại {self.base_url}: {e}")
            return False

    async def send_message(self, message: str, context: Optional[str] = None, files: Optional[List[Any]] = None, user_id: Optional[str] = None) -> str:
        """Gửi message tới agent qua A2A, có thể kèm files với retry logic"""
        if not self.is_initialized:
            logger.info(f"🔄 {self.agent_name} chưa initialized, đang thử khởi tạo...")
            success = await self.initialize()
            if not success:
                raise Exception(f"Không thể khởi tạo A2A client cho {self.agent_name} tại {self.base_url}")
        
        async def _do_send_message():
            logger.info(f"🌐 Đang gửi message tới {self.agent_name} tại domain: {self.base_url}")
            
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
                logger.info(f"📤 Gửi message với {len(files)} files tới {self.agent_name} tại {self.base_url}: {message[:100]}...")
            else:
                if user_id and self.agent_name == "Order Agent":
                    logger.info(f"📤 Gửi message tới {self.agent_name} tại {self.base_url} với User ID {user_id}: {message[:100]}...")
                else:
                    logger.info(f"📤 Gửi message tới {self.agent_name} tại {self.base_url}: {message[:100]}...")
            
            # Tạo request
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            # Gửi message
            start_time = time.time()
            response = await self.a2a_client.send_message(
                request=request, 
                http_kwargs={"timeout": 360.0}
            )
            response_time = time.time() - start_time
            
            # Parse response
            response_data = response.model_dump(mode='json', exclude_none=True)
            
            # Extract content từ response
            content = {}
            if 'result' in response_data:
                result = response_data['result']["artifacts"][0]["parts"]
                for part in result:
                    if part.get('kind') == 'text':
                        content["text"] = part.get('text', '')
                    elif part.get('kind') == 'data':
                        content["data"] = part.get('data', {}).get("products", [])
                        content["orders"] = part.get('data', {}).get("orders", [])
                        content["user_info"] = part.get('data', {}).get("user_info", {})
            
            if not content:
                content["text"] = "Không có response từ agent"
            
            logger.info(f"📥 Nhận response từ {self.agent_name} tại {self.base_url} trong {response_time:.2f}s: {content['text'][:100]}...")
            
            # Đánh dấu healthy khi gửi message thành công
            self.is_healthy = True
            self.last_health_check = datetime.now()
            
            return content
        
        try:
            return await self._retry_with_backoff(_do_send_message, "send_message")
        except Exception as e:
            error_msg = f"Lỗi khi gửi message tới {self.agent_name} tại {self.base_url} sau {self.max_retries + 1} lần thử: {str(e)}"
            logger.error(error_msg)
            self.is_healthy = False
            raise Exception(error_msg)

    async def health_check(self) -> bool:
        """Kiểm tra health của agent với retry logic"""
        async def _do_health_check():
            if not self.httpx_client:
                return False
            
            logger.debug(f"🏥 Kiểm tra health cho {self.agent_name} tại {self.base_url}/.well-known/agent.json")
            
            # Kiểm tra endpoint /.well-known/agent.json
            response = await self.httpx_client.get(
                f"{self.base_url}/.well-known/agent.json",
                timeout=5.0
            )
            
            is_healthy = response.status_code == 200
            self.is_healthy = is_healthy
            self.last_health_check = datetime.now()
            
            if is_healthy:
                logger.debug(f"✅ Health check thành công cho {self.agent_name} tại {self.base_url}")
            else:
                logger.warning(f"⚠️ Health check failed cho {self.agent_name} tại {self.base_url} (status: {response.status_code})")
            
            return is_healthy
        
        try:
            return await self._retry_with_backoff(_do_health_check, "health_check")
        except Exception as e:
            logger.warning(f"⚠️ Health check failed cho {self.agent_name} tại {self.base_url} sau {self.max_retries + 1} lần thử: {e}")
            self.is_healthy = False
            return False

    async def close(self):
        """Đóng connections"""
        try:
            if self.httpx_client:
                await self.httpx_client.aclose()
            logger.info(f"✅ Đã đóng A2A client cho {self.agent_name} tại {self.base_url}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi đóng A2A client cho {self.agent_name} tại {self.base_url}: {e}")

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
        # Sử dụng container names cho Docker environment
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
                "url": os.getenv("ORDER_AGENT_URL", "http://localhost:10000"),
                "enabled": True
            }
        }

    async def initialize(self):
        """Khởi tạo tất cả A2A clients và Redis connection"""
        logger.info("🚀 Khởi tạo A2A Client Manager...")
        
        # Khởi tạo Redis connection
        try:
            redis_url = f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}"
            logger.info(f"🔗 Đang kết nối tới Redis tại: {self.redis_config['host']}:{self.redis_config['port']}")
            
            self.redis_client = aioredis.from_url(
                redis_url,
                password=self.redis_config['password'],
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            
            # Khởi tạo optimized Redis client và health monitor
            self.optimized_redis_client = OptimizedRedisClient(self.redis_client)
            self.redis_health_monitor = RedisHealthMonitor(self.redis_client)
            
            logger.info(f"✅ Redis connection khởi tạo thành công tại {self.redis_config['host']}:{self.redis_config['port']}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi khởi tạo Redis connection tại {self.redis_config['host']}:{self.redis_config['port']}: {e}")
            logger.warning("⚠️ Sẽ sử dụng in-memory storage cho chat history")
            self.redis_client = None
            self.optimized_redis_client = None
            self.redis_health_monitor = None
        
        # Khởi tạo các agents
        initialized_agents = 0
        total_agents = len([config for config in self.agents_config.values() if config["enabled"]])
        
        logger.info(f"🤖 Đang khởi tạo {total_agents} agents...")
        
        for agent_name, config in self.agents_config.items():
            if config["enabled"]:
                logger.info(f"🔄 Khởi tạo {agent_name} tại {config['url']}")
                self.agents[agent_name] = A2AAgentClient(
                    agent_name=agent_name,
                    base_url=config["url"]
                )
                
                # Thử khởi tạo ngay (không chặn nếu agent không available)
                try:
                    success = await self.agents[agent_name].initialize()
                    if success:
                        initialized_agents += 1
                        logger.info(f"✅ {agent_name} khởi tạo thành công")
                    else:
                        logger.warning(f"⚠️ {agent_name} khởi tạo thất bại")
                except Exception as e:
                    logger.warning(f"⚠️ Không thể khởi tạo {agent_name} tại {config['url']}: {e}")
        
        logger.info(f"✅ A2A Client Manager đã khởi tạo với {initialized_agents}/{total_agents} agents khả dụng")
        
        if initialized_agents == 0:
            logger.warning("⚠️ Không có agent nào khả dụng. Hệ thống có thể gặp vấn đề khi xử lý requests.")
        elif initialized_agents < total_agents:
            logger.warning(f"⚠️ Chỉ có {initialized_agents}/{total_agents} agents khả dụng. Một số chức năng có thể bị hạn chế.")

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
            available_agents = list(self.agents.keys())
            raise ValueError(f"Agent '{agent_name}' không tồn tại. Agents khả dụng: {available_agents}")
        
        agent_client = self.agents[agent_name]
        
        # Log thông tin về request
        if files:
            file_names = [f.name for f in files if hasattr(f, 'name')]
            logger.info(f"📤 Manager gửi message tới {agent_name} với {len(files)} files: [{', '.join(file_names)}]")
        else:
            logger.info(f"📤 Manager gửi message tới {agent_name}: {message[:100]}...")
        
        # Kiểm tra agent health trước khi gửi
        if not agent_client.is_healthy:
            logger.warning(f"⚠️ {agent_name} không healthy, đang thử health check...")
            is_healthy = await agent_client.health_check()
            if not is_healthy:
                logger.error(f"❌ {agent_name} tại {agent_client.base_url} không khả dụng")
                raise Exception(f"{agent_name} tại {agent_client.base_url} không khả dụng. Vui lòng thử lại sau.")
        
        try:
            # Gửi message với files và user_id
            start_time = time.time()
            response = await agent_client.send_message(message, None, files, user_id)
            total_time = time.time() - start_time
            
            logger.info(f"📥 Manager nhận response từ {agent_name} trong {total_time:.2f}s")
            
            # Lưu vào chat history
            if session_id:
                # Tạo message content bao gồm thông tin về files
                message_content = message
                if files:
                    file_names = [f.name for f in files if hasattr(f, 'name')]
                    message_content += f" [Đính kèm: {', '.join(file_names)}]"
                
                try:
                    if user_id and self.redis_client:
                        # Sử dụng Redis
                        chat_history = await self._ensure_chat_history_with_redis(user_id, session_id)
                        chat_history.add_message("assistant", response.get("text", ""), agent_name)
                        await self._save_chat_history_to_redis(user_id, session_id, chat_history)
                        logger.debug(f"💾 Lưu response vào Redis cho session {session_id}")
                    else:
                        # Fallback to in-memory
                        self._ensure_chat_history(session_id)
                        self.chat_histories[session_id].add_message("assistant", response.get("text", ""), agent_name)
                        logger.debug(f"💾 Lưu response vào memory cho session {session_id}")
                except Exception as e:
                    logger.error(f"❌ Lỗi khi lưu chat history cho session {session_id}: {e}")
                    # Không raise exception để không ảnh hưởng tới response
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Manager failed khi gửi message tới {agent_name} tại {agent_client.base_url}: {str(e)}")
            # Mark agent as unhealthy
            agent_client.is_healthy = False
            raise

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
        """Lấy danh sách agents khả dụng với real-time health check"""
        available = []
        total_agents = len(self.agents)
        
        logger.debug(f"🔍 Kiểm tra tính khả dụng của {total_agents} agents...")
        
        for agent_name, agent_client in self.agents.items():
            if agent_client.is_healthy:
                available.append(agent_name)
                logger.debug(f"✅ {agent_name} đã healthy")
            else:
                # Thử health check lần nữa
                logger.debug(f"🔄 {agent_name} không healthy, đang thử kiểm tra lại tại {agent_client.base_url}")
                is_healthy = await agent_client.health_check()
                if is_healthy:
                    available.append(agent_name)
                    logger.info(f"🔄 {agent_name} tại {agent_client.base_url} đã khôi phục")
                else:
                    logger.warning(f"❌ {agent_name} tại {agent_client.base_url} vẫn không khả dụng")
        
        logger.info(f"📊 Agents khả dụng: {len(available)}/{total_agents} - {available}")
        
        if not available:
            logger.error("❌ Không có agent nào khả dụng! Tất cả agents đều down.")
        
        return available

    async def health_check_all(self) -> Dict[str, Any]:
        """Health check tất cả agents với logging chi tiết"""
        results = {}
        healthy_count = 0
        total_count = len(self.agents)
        
        logger.info(f"🏥 Bắt đầu health check cho {total_count} agents...")
        
        for agent_name, agent_client in self.agents.items():
            logger.debug(f"🔍 Kiểm tra {agent_name} tại {agent_client.base_url}")
            
            start_time = time.time()
            is_healthy = await agent_client.health_check()
            check_time = time.time() - start_time
            
            if is_healthy:
                healthy_count += 1
                logger.info(f"✅ {agent_name} healthy tại {agent_client.base_url} ({check_time:.2f}s)")
            else:
                logger.warning(f"❌ {agent_name} unhealthy tại {agent_client.base_url} ({check_time:.2f}s)")
            
            results[agent_name] = {
                "healthy": is_healthy,
                "url": agent_client.base_url,
                "initialized": agent_client.is_initialized,
                "last_check": agent_client.last_health_check.isoformat() if agent_client.last_health_check else None,
                "response_time": round(check_time, 2)
            }
        
        logger.info(f"🏥 Health check hoàn tất: {healthy_count}/{total_count} agents healthy")
        
        if healthy_count == 0:
            logger.error("❌ Không có agent nào healthy! Hệ thống có thể gặp vấn đề nghiêm trọng.")
        elif healthy_count < total_count:
            logger.warning(f"⚠️ Chỉ {healthy_count}/{total_count} agents healthy. Một số tính năng có thể bị ảnh hưởng.")
        
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
        """Lấy danh sách tất cả sessions của user từ Redis (sử dụng optimized client)"""
        if not user_id or not self.optimized_redis_client:
            return []
        
        try:
            pattern = self._get_user_sessions_pattern(user_id)
            keys = await self.optimized_redis_client.get_all_keys_by_pattern(pattern, max_keys=1000)
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

    async def redis_health_check(self) -> dict:
        """Thực hiện Redis health check chi tiết"""
        if not self.redis_health_monitor:
            return {"error": "Redis health monitor not available"}
        
        return await self.redis_health_monitor.health_check()
    
    async def redis_performance_report(self) -> dict:
        """Tạo Redis performance report"""
        if not self.redis_health_monitor:
            return {"error": "Redis health monitor not available"}
        
        return await self.redis_health_monitor.performance_report()
    
    async def cleanup_expired_sessions(self, ttl_threshold: int = 86400) -> int:
        """Cleanup các chat history sessions đã expired"""
        if not self.optimized_redis_client:
            return 0
        
        pattern = "chat_history:*"
        return await self.optimized_redis_client.cleanup_expired_sessions(pattern, ttl_threshold)

    async def cleanup(self):
        """Cleanup tất cả resources"""
        logger.info("🔄 Cleanup A2A Client Manager...")
        
        for agent_name, agent_client in self.agents.items():
            await agent_client.close()
        
        # Cleanup expired sessions trước khi đóng connection
        if self.optimized_redis_client:
            try:
                cleaned_count = await self.cleanup_expired_sessions()
                logger.info(f"🧹 Đã cleanup {cleaned_count} expired sessions")
            except Exception as e:
                logger.error(f"❌ Lỗi khi cleanup expired sessions: {e}")
        
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