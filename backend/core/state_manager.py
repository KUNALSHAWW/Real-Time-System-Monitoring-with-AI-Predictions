"""
State Management System
Handles application state, caching, and session management with efficient synchronization
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import redis.asyncio as redis
from core.config import settings
from core.logger import get_logger

logger = get_logger("state_manager")


class StateScope(Enum):
    """Scopes for state management"""
    GLOBAL = "global"
    USER = "user"
    SESSION = "session"
    TEMPORARY = "temporary"


@dataclass
class StateEntry:
    """Individual state entry with metadata"""
    key: str
    value: Any
    scope: StateScope
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class StateManager:
    """
    Centralized state management with Redis caching
    Handles all application state with efficient synchronization
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.local_state: Dict[str, StateEntry] = {}
        self.state_lock = asyncio.Lock()
        self.metrics = {
            "gets": 0,
            "sets": 0,
            "deletes": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def initialize(self):
        """Initialize Redis connection and load state"""
        try:
            self.redis_client = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/"
                f"{settings.REDIS_DB}",
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
        except Exception as e:
            logger.warning(f"⚠️  Redis unavailable, using local state: {str(e)}")
            self.redis_client = None
    
    async def cleanup(self):
        """Cleanup and close connections"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✅ Redis connection closed")
    
    async def set(
        self,
        key: str,
        value: Any,
        scope: StateScope = StateScope.GLOBAL,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Set state value with optional TTL"""
        async with self.state_lock:
            try:
                expires_at = None
                if ttl:
                    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                
                entry = StateEntry(
                    key=key,
                    value=value,
                    scope=scope,
                    expires_at=expires_at,
                    metadata=metadata or {}
                )
                
                # Store locally
                self.local_state[key] = entry
                
                # Store in Redis if available
                if self.redis_client:
                    redis_key = f"{scope.value}:{key}"
                    value_json = json.dumps({
                        "value": value,
                        "metadata": metadata or {},
                        "expires_at": expires_at.isoformat() if expires_at else None
                    })
                    
                    await self.redis_client.set(
                        redis_key,
                        value_json,
                        ex=ttl
                    )
                
                self.metrics["sets"] += 1
                logger.debug(f"State set: {key}")
                return True
                
            except Exception as e:
                logger.error(f"Error setting state {key}: {str(e)}")
                return False
    
    async def get(
        self,
        key: str,
        scope: StateScope = StateScope.GLOBAL,
        default: Any = None
    ) -> Any:
        """Get state value with fallback to default"""
        async with self.state_lock:
            try:
                # Check local state first
                if key in self.local_state:
                    entry = self.local_state[key]
                    if not entry.is_expired():
                        self.metrics["gets"] += 1
                        self.metrics["cache_hits"] += 1
                        return entry.value
                    else:
                        # Remove expired entry
                        del self.local_state[key]
                
                # Try Redis
                if self.redis_client:
                    redis_key = f"{scope.value}:{key}"
                    value_json = await self.redis_client.get(redis_key)
                    
                    if value_json:
                        data = json.loads(value_json)
                        self.metrics["cache_hits"] += 1
                        return data["value"]
                
                self.metrics["cache_misses"] += 1
                self.metrics["gets"] += 1
                return default
                
            except Exception as e:
                logger.error(f"Error getting state {key}: {str(e)}")
                return default
    
    async def delete(self, key: str, scope: StateScope = StateScope.GLOBAL) -> bool:
        """Delete state value"""
        async with self.state_lock:
            try:
                # Delete from local state
                if key in self.local_state:
                    del self.local_state[key]
                
                # Delete from Redis
                if self.redis_client:
                    redis_key = f"{scope.value}:{key}"
                    await self.redis_client.delete(redis_key)
                
                self.metrics["deletes"] += 1
                logger.debug(f"State deleted: {key}")
                return True
                
            except Exception as e:
                logger.error(f"Error deleting state {key}: {str(e)}")
                return False
    
    async def exists(self, key: str, scope: StateScope = StateScope.GLOBAL) -> bool:
        """Check if state key exists"""
        async with self.state_lock:
            if key in self.local_state:
                return not self.local_state[key].is_expired()
            
            if self.redis_client:
                redis_key = f"{scope.value}:{key}"
                return await self.redis_client.exists(redis_key) > 0
            
            return False
    
    async def get_all(self, scope: StateScope = StateScope.GLOBAL) -> Dict[str, Any]:
        """Get all state values for a scope"""
        async with self.state_lock:
            result = {}
            
            # Get from local state
            for key, entry in self.local_state.items():
                if entry.scope == scope and not entry.is_expired():
                    result[key] = entry.value
            
            # Get from Redis
            if self.redis_client:
                pattern = f"{scope.value}:*"
                keys = await self.redis_client.keys(pattern)
                
                for redis_key in keys:
                    key = redis_key.replace(f"{scope.value}:", "")
                    if key not in result:
                        value_json = await self.redis_client.get(redis_key)
                        if value_json:
                            data = json.loads(value_json)
                            result[key] = data["value"]
            
            return result
    
    async def increment(
        self,
        key: str,
        amount: int = 1,
        scope: StateScope = StateScope.GLOBAL
    ) -> int:
        """Increment numeric state value"""
        async with self.state_lock:
            current = await self.get(key, scope, 0)
            new_value = current + amount
            await self.set(key, new_value, scope)
            return new_value
    
    async def append(
        self,
        key: str,
        value: Any,
        scope: StateScope = StateScope.GLOBAL,
        max_size: int = 1000
    ) -> List[Any]:
        """Append to list state value"""
        async with self.state_lock:
            current = await self.get(key, scope, [])
            if not isinstance(current, list):
                current = []
            
            current.append(value)
            
            # Keep only recent items
            if len(current) > max_size:
                current = current[-max_size:]
            
            await self.set(key, current, scope)
            return current
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get state manager metrics"""
        return {
            **self.metrics,
            "hit_rate": (
                self.metrics["cache_hits"] / 
                (self.metrics["cache_hits"] + self.metrics["cache_misses"])
                if (self.metrics["cache_hits"] + self.metrics["cache_misses"]) > 0
                else 0
            ),
            "local_state_size": len(self.local_state)
        }


# Global state manager instance
state_manager: Optional[StateManager] = None


async def get_state_manager() -> StateManager:
    """Get or create global state manager"""
    global state_manager
    if state_manager is None:
        state_manager = StateManager()
        await state_manager.initialize()
    return state_manager
