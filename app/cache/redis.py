import json
from typing import Any, Optional, Type, TypeVar, Generic
from redis.asyncio import Redis, ConnectionPool
from loguru import logger
from pydantic import BaseModel

from app.config import settings

# Type variable for generic caching
T = TypeVar('T', bound=BaseModel)

# Global connection pool
redis_pool: Optional[ConnectionPool] = None
redis_client: Optional[Redis] = None


async def create_redis_pool() -> None:
    """
    Create a Redis connection pool.
    """
    global redis_pool, redis_client

    try:
        # Create connection pool with optimal settings for high concurrency
        redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=100,  # Maximum number of connections in the pool
            socket_timeout=5.0,  # Socket timeout
            socket_connect_timeout=5.0,  # Socket connect timeout
            retry_on_timeout=True,  # Retry on timeout
            health_check_interval=30,  # Health check interval in seconds
        )

        # Create Redis client
        redis_client = Redis(connection_pool=redis_pool)

        # Test the connection
        await redis_client.ping()
        logger.info("Redis connection pool created successfully")

    except Exception as e:
        logger.error(f"Failed to create Redis connection pool: {str(e)}")
        raise


async def close_redis_pool() -> None:
    """
    Close the Redis connection pool.
    """
    global redis_pool, redis_client

    if redis_client:
        await redis_client.close()

    if redis_pool:
        await redis_pool.disconnect()

    logger.info("Redis connection pool closed")


async def get_redis() -> Redis:
    """
    Get Redis client from the pool.
    """
    if redis_client is None:
        await create_redis_pool()
    return redis_client


class RedisCache(Generic[T]):
    """
    Generic Redis cache handler for Pydantic models.
    """

    def __init__(self, prefix: str, model_class: Type[T]):
        self.prefix = prefix
        self.model_class = model_class

    def _get_key(self, key: str) -> str:
        """Generate Redis key with prefix."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[T]:
        """
        Get value from cache.
        """
        redis = await get_redis()
        value = await redis.get(self._get_key(key))

        if value:
            try:
                data = json.loads(value)
                return self.model_class.model_validate(data)
            except Exception as e:
                logger.error(f"Error deserializing cached value: {str(e)}")

        return None

    async def set(self, key: str, value: T, expire: int = None) -> bool:
        """
        Set value in cache with optional expiration.
        """
        if expire is None:
            expire = settings.REDIS_TIMEOUT

        redis = await get_redis()

        try:
            json_value = value.model_dump_json()
            result = await redis.set(
                self._get_key(key),
                json_value,
                ex=expire
            )
            return result
        except Exception as e:
            logger.error(f"Error serializing value for cache: {str(e)}")
            return False