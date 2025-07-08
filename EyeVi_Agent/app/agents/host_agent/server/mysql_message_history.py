"""
MySQL Message History Manager - Real-time message logging vào MySQL
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

logger = logging.getLogger(__name__)

class SenderType(Enum):
    """Enum cho sender_type trong database"""
    USER = "user"
    HOST_AGENT = "host_agent"
    ADVISOR_AGENT = "advisor_agent"
    SEARCH_AGENT = "search_agent"
    ORDER_AGENT = "order_agent"

class MySQLMessageHistory:
    """
    Manager để save messages vào MySQL real-time
    """
    
    def __init__(self):
        """Khởi tạo MySQL connection"""
        self.engine = None
        self.async_session = None
        self.connection_pool = None
        
        # MySQL config từ environment
        self.mysql_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "chat_db"),
            "charset": "utf8mb4"
        }
    
    async def initialize(self):
        """Khởi tạo MySQL connection pool"""
        try:
            # Tạo SQLAlchemy async engine
            mysql_url = (
                f"mysql+aiomysql://{self.mysql_config['user']}:"
                f"{self.mysql_config['password']}@{self.mysql_config['host']}:"
                f"{self.mysql_config['port']}/{self.mysql_config['database']}"
                f"?charset={self.mysql_config['charset']}"
            )
            
            self.engine = create_async_engine(
                mysql_url,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections every hour
                pool_size=10,        # Connection pool size
                max_overflow=20,     # Max overflow connections
                echo=False           # Set True for SQL debugging
            )
            
            # Tạo async session factory
            self.async_session = sessionmaker(
                self.engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            # Test connection
            await self._test_connection()
            
            logger.info("✅ MySQL Message History initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MySQL: {e}")
            raise
    
    async def _test_connection(self):
        """Test MySQL connection"""
        async with self.async_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("✅ MySQL connection test successful")
    
    async def save_message(
        self,
        session_id: str,
        sender_type: str,
        message_content: str,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Save message vào MySQL database
        
        Args:
            session_id: ID phiên chat
            sender_type: Loại người gửi (user, host_agent, etc.)
            message_content: Nội dung tin nhắn
            user_id: ID người dùng (optional)
            metadata: Thông tin bổ sung (optional)
            
        Returns:
            ID của message đã save, hoặc None nếu fail
        """
        if not self.async_session:
            logger.error("❌ MySQL not initialized")
            return None
        
        try:
            # Validate sender_type
            if sender_type not in [e.value for e in SenderType]:
                logger.warning(f"⚠️ Invalid sender_type: {sender_type}, defaulting to host_agent")
                sender_type = SenderType.HOST_AGENT.value
            
            # Prepare metadata JSON
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Insert query
            insert_query = text("""
                INSERT INTO message_history 
                (session_id, user_id, sender_type, message_content, metadata)
                VALUES (:session_id, :user_id, :sender_type, :message_content, :metadata)
            """)
            
            async with self.async_session() as session:
                result = await session.execute(insert_query, {
                    "session_id": session_id,
                    "user_id": user_id,
                    "sender_type": sender_type,
                    "message_content": message_content,
                    "metadata": metadata_json
                })
                
                await session.commit()
                
                # Get inserted ID
                message_id = result.lastrowid
                
                logger.debug(
                    f"💾 Saved message to MySQL: "
                    f"session={session_id}, sender={sender_type}, id={message_id}"
                )
                
                return message_id
                
        except Exception as e:
            logger.error(f"❌ Failed to save message to MySQL: {e}")
            return None
    
    async def save_user_message(
        self,
        session_id: str,
        message_content: str,
        user_id: Optional[int] = None,
        clarified_content: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> Optional[int]:
        """
        Save user message với metadata
        """
        metadata = {}
        
        if clarified_content and clarified_content != message_content:
            metadata["clarified_content"] = clarified_content
        
        if files:
            metadata["files"] = files
            
        return await self.save_message(
            session_id=session_id,
            sender_type=SenderType.USER.value,
            message_content=message_content,
            user_id=user_id,
            metadata=metadata if metadata else None
        )
    
    async def save_agent_message(
        self,
        session_id: str,
        message_content: str,
        agent_name: str,
        user_id: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        analysis: Optional[str] = None,
        orders: Optional[List[Dict[str, Any]]] = None,
        user_info: Optional[Dict[str, Any]] = None,
        products: Optional[List[Dict[str, Any]]] = None,
        extracted_product_ids: Optional[List[str]] = None
    ) -> Optional[int]:
        """
        Save agent response message với thông tin đầy đủ về products, orders, user_info
        
        Args:
            session_id: ID phiên chat
            message_content: Nội dung tin nhắn
            agent_name: Tên agent
            user_id: ID người dùng (optional)
            response_data: Dữ liệu response (optional)
            analysis: Phân tích (optional)
            orders: Danh sách đơn hàng (optional)
            user_info: Thông tin user (optional) 
            products: Danh sách sản phẩm (optional)
            extracted_product_ids: Danh sách product IDs được trích xuất (optional)
            
        Returns:
            ID của message đã save, hoặc None nếu fail
        """
        # Map agent name to sender_type
        agent_mapping = {
            "Advisor Agent": SenderType.ADVISOR_AGENT.value,
            "Search Agent": SenderType.SEARCH_AGENT.value,
            "Order Agent": SenderType.ORDER_AGENT.value,
            "Host Agent": SenderType.HOST_AGENT.value
        }
        
        sender_type = agent_mapping.get(agent_name, SenderType.HOST_AGENT.value)
        
        metadata = {
            "agent_name": agent_name
        }
        
        # Lưu response_data nếu có
        if response_data:
            metadata["response_data"] = response_data
            
        # Lưu analysis nếu có
        if analysis:
            metadata["analysis"] = analysis
            
        # Lưu danh sách orders nếu có (thông tin chi tiết đơn hàng)
        if orders and len(orders) > 0:
            metadata["orders"] = orders
            
        # Lưu thông tin user nếu có
        if user_info and user_info:
            metadata["user_info"] = user_info
            
        # Lưu danh sách products nếu có (thông tin chi tiết sản phẩm)
        if products and len(products) > 0:
            metadata["products"] = products
            
        # Lưu danh sách product IDs được trích xuất
        if extracted_product_ids and len(extracted_product_ids) > 0:
            metadata["extracted_product_ids"] = extracted_product_ids
        
        return await self.save_message(
            session_id=session_id,
            sender_type=sender_type,
            message_content=message_content,
            user_id=user_id,
            metadata=metadata
        )
    
    async def save_session(
        self,
        session_id: str,
        user_id: int,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> bool:
        """
        Lưu session mới vào bảng sessions
        Args:
            session_id: ID của session
            user_id: ID của user
            created_at: thời gian tạo (nếu không truyền sẽ lấy now)
            updated_at: thời gian cập nhật (nếu không truyền sẽ lấy now)
        Returns:
            True nếu thành công, False nếu lỗi
        """
        if not self.async_session:
            logger.error("❌ MySQL not initialized")
            return False
        try:
            from datetime import datetime
            now = datetime.now()
            insert_query = text("""
                INSERT INTO sessions (session_id, user_id, created_at, updated_at)
                VALUES (:session_id, :user_id, :created_at, :updated_at)
            """)
            async with self.async_session() as session:
                await session.execute(
                    insert_query,
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "created_at": created_at or now,
                        "updated_at": updated_at or now
                    }
                )
                await session.commit()
            logger.debug(f"💾 Đã lưu session vào MySQL: session_id={session_id}, user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save session to MySQL: {e}")
            return False
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lấy messages của một session (cho debugging/admin)
        """
        if not self.async_session:
            return []
        
        try:
            query = text("""
                SELECT 
                    id, session_id, user_id, sender_type, 
                    message_content, metadata, created_at
                FROM message_history 
                WHERE session_id = :session_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            async with self.async_session() as session:
                result = await session.execute(query, {
                    "session_id": session_id,
                    "limit": limit,
                    "offset": offset
                })
                
                messages = []
                for row in result.fetchall():
                    message = {
                        "id": row.id,
                        "session_id": row.session_id,
                        "user_id": row.user_id,
                        "sender_type": row.sender_type,
                        "message_content": row.message_content,
                        "metadata": json.loads(row.metadata) if row.metadata else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    }
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"❌ Failed to get session messages: {e}")
            return []
    
    async def get_user_sessions(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[str]:
        """
        Lấy danh sách session_ids của user
        """
        if not self.async_session:
            return []
        
        try:
            query = text("""
                SELECT DISTINCT session_id, created_at
                FROM message_history 
                WHERE user_id = :user_id
                ORDER BY (created_at) DESC
                LIMIT :limit
            """)
            
            async with self.async_session() as session:
                result = await session.execute(query, {
                    "user_id": user_id,
                    "limit": limit
                })
                
                return [row.session_id for row in result.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Failed to get user sessions: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup connections"""
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("✅ MySQL connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing MySQL connections: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check cho MySQL connection"""
        health = {
            "status": "unhealthy",
            "connected": False,
            "error": None
        }
        
        try:
            if self.async_session:
                async with self.async_session() as session:
                    await session.execute(text("SELECT 1"))
                    health["status"] = "healthy"
                    health["connected"] = True
            else:
                health["error"] = "MySQL not initialized"
                
        except Exception as e:
            health["error"] = str(e)
            logger.error(f"❌ MySQL health check failed: {e}")
        
        return health 