"""
Redis Performance Optimizations - Cải thiện performance cho Redis operations
"""

import asyncio
import logging
from typing import List, Set, Optional, AsyncGenerator
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

class OptimizedRedisClient:
    """
    Wrapper cho Redis client với các optimizations
    """
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis_client = redis_client
        self._pipeline_batch_size = 100
        self._scan_batch_size = 1000
    
    async def scan_keys_by_pattern(self, pattern: str, batch_size: Optional[int] = None) -> AsyncGenerator[str, None]:
        """
        Sử dụng SCAN thay vì KEYS để tránh block Redis server
        Trả về generator để handle large datasets efficiently
        """
        batch_size = batch_size or self._scan_batch_size
        cursor = 0
        
        while True:
            try:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor, 
                    match=pattern, 
                    count=batch_size
                )
                
                for key in keys:
                    yield key
                
                if cursor == 0:
                    break
                    
            except Exception as e:
                logger.error(f"❌ Lỗi khi scan Redis keys: {e}")
                break
    
    async def get_all_keys_by_pattern(self, pattern: str, max_keys: int = 10000) -> List[str]:
        """
        Lấy tất cả keys theo pattern với giới hạn số lượng
        """
        keys = []
        count = 0
        
        async for key in self.scan_keys_by_pattern(pattern):
            keys.append(key)
            count += 1
            if count >= max_keys:
                logger.warning(f"⚠️ Đạt giới hạn {max_keys} keys cho pattern {pattern}")
                break
        
        return keys
    
    async def batch_get(self, keys: List[str]) -> List[Optional[str]]:
        """
        Lấy nhiều keys cùng lúc sử dụng pipeline để tăng performance
        """
        if not keys:
            return []
        
        try:
            pipe = self.redis_client.pipeline()
            for key in keys:
                pipe.get(key)
            return await pipe.execute()
        except Exception as e:
            logger.error(f"❌ Lỗi khi batch get Redis keys: {e}")
            return [None] * len(keys)
    
    async def batch_set(self, key_value_pairs: List[tuple], ex: Optional[int] = None) -> bool:
        """
        Set nhiều keys cùng lúc sử dụng pipeline
        """
        if not key_value_pairs:
            return True
        
        try:
            pipe = self.redis_client.pipeline()
            for key, value in key_value_pairs:
                if ex:
                    pipe.set(key, value, ex=ex)
                else:
                    pipe.set(key, value)
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"❌ Lỗi khi batch set Redis keys: {e}")
            return False
    
    async def batch_delete(self, keys: List[str]) -> int:
        """
        Xóa nhiều keys cùng lúc
        """
        if not keys:
            return 0
        
        try:
            # Chia nhỏ thành batches để tránh timeout
            deleted_count = 0
            for i in range(0, len(keys), self._pipeline_batch_size):
                batch_keys = keys[i:i + self._pipeline_batch_size]
                deleted_count += await self.redis_client.delete(*batch_keys)
            return deleted_count
        except Exception as e:
            logger.error(f"❌ Lỗi khi batch delete Redis keys: {e}")
            return 0
    
    async def cleanup_expired_sessions(self, pattern: str, ttl_threshold: int = 86400) -> int:
        """
        Cleanup các sessions đã expired hoặc cũ
        """
        cleaned_count = 0
        keys_to_delete = []
        
        async for key in self.scan_keys_by_pattern(pattern):
            try:
                ttl = await self.redis_client.ttl(key)
                # Nếu key không có TTL hoặc TTL quá nhỏ, đánh dấu để xóa
                if ttl == -1 or (ttl > 0 and ttl < ttl_threshold):
                    keys_to_delete.append(key)
                    
                    # Batch delete when we have enough keys
                    if len(keys_to_delete) >= self._pipeline_batch_size:
                        deleted = await self.batch_delete(keys_to_delete)
                        cleaned_count += deleted
                        keys_to_delete.clear()
                        
            except Exception as e:
                logger.error(f"❌ Lỗi khi check TTL cho key {key}: {e}")
        
        # Delete remaining keys
        if keys_to_delete:
            deleted = await self.batch_delete(keys_to_delete)
            cleaned_count += deleted
        
        logger.info(f"🧹 Đã cleanup {cleaned_count} expired Redis keys")
        return cleaned_count
    
    async def get_memory_usage_stats(self) -> dict:
        """
        Lấy thống kê memory usage của Redis
        """
        try:
            info = await self.redis_client.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'max_memory': info.get('maxmemory', 0),
                'max_memory_human': info.get('maxmemory_human', '0B') if info.get('maxmemory') else 'unlimited'
            }
        except Exception as e:
            logger.error(f"❌ Lỗi khi lấy Redis memory stats: {e}")
            return {}

class RedisHealthMonitor:
    """
    Monitor health và performance của Redis
    """
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis_client = redis_client
        self.optimized_client = OptimizedRedisClient(redis_client)
    
    async def health_check(self) -> dict:
        """
        Comprehensive health check cho Redis
        """
        health_data = {
            'is_healthy': False,
            'latency_ms': None,
            'memory_usage': {},
            'connections': {},
            'errors': []
        }
        
        try:
            # Test ping latency
            import time
            start_time = time.time()
            await self.redis_client.ping()
            health_data['latency_ms'] = (time.time() - start_time) * 1000
            
            # Memory usage
            health_data['memory_usage'] = await self.optimized_client.get_memory_usage_stats()
            
            # Connection info
            info = await self.redis_client.info('clients')
            health_data['connections'] = {
                'connected_clients': info.get('connected_clients', 0),
                'blocked_clients': info.get('blocked_clients', 0),
                'max_clients': info.get('maxclients', 0)
            }
            
            health_data['is_healthy'] = True
            
        except Exception as e:
            health_data['errors'].append(str(e))
            logger.error(f"❌ Redis health check failed: {e}")
        
        return health_data
    
    async def performance_report(self) -> dict:
        """
        Tạo performance report cho Redis
        """
        report = {
            'timestamp': asyncio.get_event_loop().time(),
            'health': await self.health_check(),
            'recommendations': []
        }
        
        # Performance recommendations
        if report['health']['latency_ms'] and report['health']['latency_ms'] > 100:
            report['recommendations'].append("Latency cao (>100ms) - kiểm tra network hoặc Redis load")
        
        memory_usage = report['health']['memory_usage']
        if memory_usage.get('max_memory', 0) > 0:
            used_pct = (memory_usage.get('used_memory', 0) / memory_usage['max_memory']) * 100
            if used_pct > 80:
                report['recommendations'].append(f"Memory usage cao ({used_pct:.1f}%) - cân nhắc cleanup hoặc tăng memory")
        
        connections = report['health']['connections']
        if connections.get('max_clients', 0) > 0:
            conn_pct = (connections.get('connected_clients', 0) / connections['max_clients']) * 100
            if conn_pct > 80:
                report['recommendations'].append(f"Connection usage cao ({conn_pct:.1f}%) - kiểm tra connection pooling")
        
        return report

# Utility functions
async def migrate_keys_with_new_pattern(
    redis_client: aioredis.Redis,
    old_pattern: str,
    new_pattern_template: str,
    dry_run: bool = True
) -> dict:
    """
    Migrate Redis keys từ pattern cũ sang pattern mới
    """
    optimized_client = OptimizedRedisClient(redis_client)
    migration_report = {
        'found_keys': 0,
        'migrated_keys': 0,
        'errors': [],
        'dry_run': dry_run
    }
    
    try:
        async for old_key in optimized_client.scan_keys_by_pattern(old_pattern):
            migration_report['found_keys'] += 1
            
            # Generate new key name
            # Simple replacement for now - có thể customize logic này
            new_key = old_key.replace('chat_history:', 'langchain_history:')
            
            if not dry_run:
                try:
                    # Get old value
                    value = await redis_client.get(old_key)
                    if value:
                        # Set new key with same TTL
                        ttl = await redis_client.ttl(old_key)
                        if ttl > 0:
                            await redis_client.set(new_key, value, ex=ttl)
                        else:
                            await redis_client.set(new_key, value)
                        
                        # Delete old key
                        await redis_client.delete(old_key)
                        migration_report['migrated_keys'] += 1
                        
                except Exception as e:
                    migration_report['errors'].append(f"Error migrating {old_key}: {str(e)}")
            else:
                logger.info(f"[DRY RUN] Would migrate {old_key} -> {new_key}")
                migration_report['migrated_keys'] += 1
    
    except Exception as e:
        migration_report['errors'].append(f"Migration error: {str(e)}")
    
    return migration_report 