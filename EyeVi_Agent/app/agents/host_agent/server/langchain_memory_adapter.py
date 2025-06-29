"""
LangChain Memory Adapter - Tích hợp LangChain memory với Redis backend
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import redis.asyncio as aioredis
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage as CoreBaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

class RedisChatMessageHistory(BaseChatMessageHistory):
    """
    LangChain-compatible chat history với Redis backend
    """
    
    def __init__(self, session_id: str, user_id: Optional[str] = None, redis_client: Optional[aioredis.Redis] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.redis_client = redis_client
        self._messages: List[CoreBaseMessage] = []
        
    def _get_redis_key(self) -> str:
        """Tạo Redis key cho chat history"""
        if self.user_id:
            return f"langchain_history:{self.user_id}:{self.session_id}"
        return f"langchain_history:anonymous:{self.session_id}"
    
    async def _load_messages(self):
        """Load messages từ Redis"""
        if not self.redis_client:
            return
            
        try:
            redis_key = self._get_redis_key()
            data = await self.redis_client.get(redis_key)
            if data:
                messages_data = json.loads(data)
                self._messages = []
                for msg_data in messages_data:
                    if msg_data["type"] == "human":
                        self._messages.append(HumanMessage(content=msg_data["content"]))
                    elif msg_data["type"] == "ai":
                        self._messages.append(AIMessage(content=msg_data["content"]))
        except Exception as e:
            logger.error(f"❌ Lỗi khi load messages từ Redis: {e}")
    
    async def _save_messages(self):
        """Save messages vào Redis"""
        if not self.redis_client:
            return
            
        try:
            redis_key = self._get_redis_key()
            messages_data = []
            for msg in self._messages:
                if isinstance(msg, HumanMessage):
                    messages_data.append({"type": "human", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages_data.append({"type": "ai", "content": msg.content})
            
            data = json.dumps(messages_data)
            await self.redis_client.set(redis_key, data, ex=86400*7)  # Expire sau 7 ngày
        except Exception as e:
            logger.error(f"❌ Lỗi khi save messages vào Redis: {e}")
    
    @property
    def messages(self) -> List[CoreBaseMessage]:
        """Get messages (sync property required by LangChain)"""
        return self._messages
    
    def add_user_message(self, message: str) -> None:
        """Thêm user message"""
        self._messages.append(HumanMessage(content=message))
        # Schedule async save
        asyncio.create_task(self._save_messages())
    
    def add_ai_message(self, message: str) -> None:
        """Thêm AI message"""
        self._messages.append(AIMessage(content=message))
        # Schedule async save
        asyncio.create_task(self._save_messages())
    
    def clear(self) -> None:
        """Xóa tất cả messages"""
        self._messages.clear()
        # Schedule async delete from Redis
        if self.redis_client:
            asyncio.create_task(self._delete_from_redis())
    
    async def _delete_from_redis(self):
        """Delete messages từ Redis"""
        try:
            redis_key = self._get_redis_key()
            await self.redis_client.delete(redis_key)
        except Exception as e:
            logger.error(f"❌ Lỗi khi delete messages từ Redis: {e}")

class EnhancedMemoryManager:
    """
    Memory Manager sử dụng LangChain với Redis backend
    """
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None, llm: Optional[Any] = None):
        self.redis_client = redis_client
        self.llm = llm
        self._memories: Dict[str, BaseChatMemory] = {}
    
    def _get_memory_key(self, session_id: str, user_id: Optional[str] = None) -> str:
        """Tạo memory key"""
        if user_id:
            return f"{user_id}:{session_id}"
        return f"anonymous:{session_id}"
    
    async def get_memory(
        self, 
        session_id: str, 
        user_id: Optional[str] = None,
        memory_type: str = "buffer",
        max_token_limit: int = 1000
    ) -> BaseChatMemory:
        """
        Lấy hoặc tạo memory cho session
        
        Args:
            session_id: Session ID
            user_id: User ID (optional)
            memory_type: Loại memory ("buffer", "summary_buffer")
            max_token_limit: Giới hạn token cho summary buffer
        """
        memory_key = self._get_memory_key(session_id, user_id)
        
        if memory_key not in self._memories:
            # Tạo chat history với Redis backend
            chat_history = RedisChatMessageHistory(
                session_id=session_id,
                user_id=user_id,
                redis_client=self.redis_client
            )
            
            # Load existing messages
            await chat_history._load_messages()
            
            # Tạo memory dựa trên type
            if memory_type == "summary_buffer" and self.llm:
                memory = ConversationSummaryBufferMemory(
                    llm=self.llm,
                    chat_memory=chat_history,
                    max_token_limit=max_token_limit,
                    return_messages=True
                )
            else:
                memory = ConversationBufferMemory(
                    chat_memory=chat_history,
                    return_messages=True
                )
            
            self._memories[memory_key] = memory
        
        return self._memories[memory_key]
    
    async def add_user_message(self, session_id: str, message: str, user_id: Optional[str] = None):
        """Thêm user message vào memory"""
        memory = await self.get_memory(session_id, user_id)
        memory.chat_memory.add_user_message(message)
    
    async def add_ai_message(self, session_id: str, message: str, user_id: Optional[str] = None):
        """Thêm AI message vào memory"""
        memory = await self.get_memory(session_id, user_id)
        memory.chat_memory.add_ai_message(message)
    
    async def get_conversation_context(
        self, 
        session_id: str, 
        user_id: Optional[str] = None,
        max_messages: int = 10
    ) -> str:
        """Lấy context từ conversation history"""
        try:
            memory = await self.get_memory(session_id, user_id)
            
            # Lấy messages gần đây
            messages = memory.chat_memory.messages[-max_messages:] if memory.chat_memory.messages else []
            
            context_parts = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    context_parts.append(f"User: {msg.content}")
                elif isinstance(msg, AIMessage):
                    # Kiểm tra xem có agent information không
                    agent_info = ""
                    if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                        agent_used = msg.additional_kwargs.get('agent_used')
                        if agent_used:
                            agent_info = f" ({agent_used})"
                    context_parts.append(f"Assistant{agent_info}: {msg.content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi lấy conversation context: {e}")
            return ""
    
    async def get_memory_variables(self, session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Lấy memory variables cho LLM chain"""
        memory = await self.get_memory(session_id, user_id)
        return memory.load_memory_variables({})
    
    async def clear_memory(self, session_id: str, user_id: Optional[str] = None):
        """Xóa memory cho session"""
        memory_key = self._get_memory_key(session_id, user_id)
        if memory_key in self._memories:
            self._memories[memory_key].clear()
            del self._memories[memory_key]
    
    async def get_all_user_sessions(self, user_id: str) -> List[str]:
        """Lấy tất cả sessions của user từ Redis"""
        if not self.redis_client:
            return []
        
        try:
            pattern = f"langchain_history:{user_id}:*"
            keys = await self.redis_client.keys(pattern)
            sessions = []
            for key in keys:
                parts = key.split(":")
                if len(parts) >= 3:
                    session_id = ":".join(parts[2:])
                    sessions.append(session_id)
            return sessions
        except Exception as e:
            logger.error(f"❌ Lỗi khi lấy user sessions: {e}")
            return []

# Utility functions cho migration từ ChatHistory cũ
async def migrate_chat_history_to_langchain(
    old_chat_history: Any, 
    memory_manager: EnhancedMemoryManager,
    session_id: str,
    user_id: Optional[str] = None
):
    """
    Migration function từ ChatHistory cũ sang LangChain memory
    """
    try:
        if hasattr(old_chat_history, 'messages'):
            for msg in old_chat_history.messages:
                if msg.get("role") == "user":
                    await memory_manager.add_user_message(session_id, msg["content"], user_id)
                elif msg.get("role") == "assistant":
                    await memory_manager.add_ai_message(session_id, msg["content"], user_id)
        
        logger.info(f"✅ Migrated chat history for session {session_id}")
    except Exception as e:
        logger.error(f"❌ Error migrating chat history: {e}") 