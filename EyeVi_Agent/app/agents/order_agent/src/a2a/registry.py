import json
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import aioredis
from src.api.models.a2a_models import (
    AgentInfo, AgentType, AgentDiscoveryRequest, 
    AgentDiscoveryResponse, HeartbeatMessage
)
import logging

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Agent Registry Service sử dụng Redis để quản lý đăng ký agents
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.heartbeat_timeout = 60  # seconds
        
    async def connect(self):
        """Kết nối tới Redis"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Connected to Redis for agent registry")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Ngắt kết nối Redis"""
        if self.redis:
            await self.redis.close()
            
    async def register_agent(self, agent_info: AgentInfo) -> bool:
        """
        Đăng ký một agent vào registry
        """
        try:
            # Lưu thông tin agent
            agent_key = f"agent:{agent_info.agent_id}"
            agent_data = agent_info.dict()
            agent_data['last_heartbeat'] = datetime.now().isoformat()
            
            await self.redis.hset(agent_key, mapping={
                'data': json.dumps(agent_data, default=str)
            })
            
            # Thêm vào index theo type
            type_key = f"agents_by_type:{agent_info.agent_type.value}"
            await self.redis.sadd(type_key, agent_info.agent_id)
            
            # Thêm vào index theo capabilities
            for capability in agent_info.capabilities:
                cap_key = f"agents_by_capability:{capability.name}"
                await self.redis.sadd(cap_key, agent_info.agent_id)
            
            # Thêm vào danh sách tất cả agents
            await self.redis.sadd("all_agents", agent_info.agent_id)
            
            logger.info(f"Registered agent: {agent_info.agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_info.agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Hủy đăng ký một agent
        """
        try:
            # Lấy thông tin agent trước khi xóa
            agent_info = await self.get_agent_info(agent_id)
            if not agent_info:
                return False
            
            # Xóa khỏi các indexes
            type_key = f"agents_by_type:{agent_info.agent_type.value}"
            await self.redis.srem(type_key, agent_id)
            
            for capability in agent_info.capabilities:
                cap_key = f"agents_by_capability:{capability.name}"
                await self.redis.srem(cap_key, agent_id)
            
            await self.redis.srem("all_agents", agent_id)
            
            # Xóa dữ liệu agent
            agent_key = f"agent:{agent_id}"
            await self.redis.delete(agent_key)
            
            logger.info(f"Unregistered agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """
        Lấy thông tin của một agent
        """
        try:
            agent_key = f"agent:{agent_id}"
            data = await self.redis.hget(agent_key, 'data')
            
            if data:
                agent_dict = json.loads(data)
                return AgentInfo(**agent_dict)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get agent info for {agent_id}: {e}")
            return None
    
    async def discover_agents(self, request: AgentDiscoveryRequest) -> AgentDiscoveryResponse:
        """
        Tìm kiếm agents theo điều kiện
        """
        try:
            agent_ids = set()
            
            # Lọc theo agent type
            if request.agent_type:
                type_key = f"agents_by_type:{request.agent_type.value}"
                type_agents = await self.redis.smembers(type_key)
                agent_ids.update(type_agents)
            
            # Lọc theo capability
            elif request.capability:
                cap_key = f"agents_by_capability:{request.capability}"
                cap_agents = await self.redis.smembers(cap_key)
                agent_ids.update(cap_agents)
            
            # Nếu không có filter nào, lấy tất cả
            else:
                all_agents = await self.redis.smembers("all_agents")
                agent_ids.update(all_agents)
            
            # Lấy thông tin chi tiết của các agents
            agents = []
            for agent_id in agent_ids:
                agent_info = await self.get_agent_info(agent_id)
                if agent_info and agent_info.status == request.status:
                    # Kiểm tra heartbeat timeout
                    if await self._is_agent_alive(agent_info):
                        agents.append(agent_info)
                    else:
                        # Agent đã timeout, đánh dấu inactive
                        await self._mark_agent_inactive(agent_id)
            
            return AgentDiscoveryResponse(
                agents=agents,
                total_count=len(agents)
            )
            
        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
            return AgentDiscoveryResponse(agents=[], total_count=0)
    
    async def update_heartbeat(self, heartbeat: HeartbeatMessage) -> bool:
        """
        Cập nhật heartbeat của agent
        """
        try:
            agent_info = await self.get_agent_info(heartbeat.agent_id)
            if not agent_info:
                return False
            
            # Cập nhật thông tin
            agent_info.status = heartbeat.status
            agent_info.last_heartbeat = datetime.now()
            
            # Cập nhật metadata
            if heartbeat.load_percentage is not None:
                agent_info.metadata['load_percentage'] = heartbeat.load_percentage
            if heartbeat.active_connections is not None:
                agent_info.metadata['active_connections'] = heartbeat.active_connections
            
            agent_info.metadata.update(heartbeat.metadata)
            
            # Lưu lại vào Redis
            agent_key = f"agent:{heartbeat.agent_id}"
            agent_data = agent_info.dict()
            agent_data['last_heartbeat'] = datetime.now().isoformat()
            
            await self.redis.hset(agent_key, mapping={
                'data': json.dumps(agent_data, default=str)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update heartbeat for {heartbeat.agent_id}: {e}")
            return False
    
    async def _is_agent_alive(self, agent_info: AgentInfo) -> bool:
        """
        Kiểm tra agent có còn sống không dựa trên heartbeat
        """
        try:
            if isinstance(agent_info.last_heartbeat, str):
                last_heartbeat = datetime.fromisoformat(agent_info.last_heartbeat.replace('Z', '+00:00'))
            else:
                last_heartbeat = agent_info.last_heartbeat
            
            timeout_threshold = datetime.now() - timedelta(seconds=self.heartbeat_timeout)
            return last_heartbeat > timeout_threshold
            
        except Exception:
            return False
    
    async def _mark_agent_inactive(self, agent_id: str):
        """
        Đánh dấu agent là inactive
        """
        try:
            agent_info = await self.get_agent_info(agent_id)
            if agent_info:
                agent_info.status = "inactive"
                
                agent_key = f"agent:{agent_id}"
                agent_data = agent_info.dict()
                
                await self.redis.hset(agent_key, mapping={
                    'data': json.dumps(agent_data, default=str)
                })
                
                logger.warning(f"Marked agent {agent_id} as inactive due to heartbeat timeout")
                
        except Exception as e:
            logger.error(f"Failed to mark agent {agent_id} as inactive: {e}")
    
    async def cleanup_inactive_agents(self):
        """
        Dọn dẹp các agents không hoạt động
        """
        try:
            all_agents = await self.redis.smembers("all_agents")
            
            for agent_id in all_agents:
                agent_info = await self.get_agent_info(agent_id)
                if agent_info and not await self._is_agent_alive(agent_info):
                    await self._mark_agent_inactive(agent_id)
                    
        except Exception as e:
            logger.error(f"Failed to cleanup inactive agents: {e}")

# Singleton instance
_agent_registry = None

async def get_agent_registry() -> AgentRegistry:
    """
    Lấy instance của AgentRegistry (singleton pattern)
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
        await _agent_registry.connect()
    return _agent_registry 