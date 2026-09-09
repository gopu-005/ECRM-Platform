import redis.asyncio as aioredis
from app.core.config import settings

# Redis connection pool
_redis_client = None


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency: returns async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis():
    """Close Redis connection on shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# Token blacklist operations
BLACKLIST_PREFIX = "blacklist:"
REFRESH_TOKEN_PREFIX = "refresh:"


async def blacklist_token(redis: aioredis.Redis, token: str, expires_in: int) -> None:
    """Add a token to the Redis blacklist with TTL."""
    await redis.setex(f"{BLACKLIST_PREFIX}{token}", expires_in, "1")


async def is_token_blacklisted(redis: aioredis.Redis, token: str) -> bool:
    """Check if a token is blacklisted."""
    return bool(await redis.exists(f"{BLACKLIST_PREFIX}{token}"))


async def store_refresh_token(
    redis: aioredis.Redis, user_id: str, token: str, expires_in: int
) -> None:
    """Store a refresh token for a user."""
    await redis.setex(f"{REFRESH_TOKEN_PREFIX}{user_id}:{token[:16]}", expires_in, token)


async def revoke_user_tokens(redis: aioredis.Redis, user_id: str) -> None:
    """Revoke all refresh tokens for a user."""
    pattern = f"{REFRESH_TOKEN_PREFIX}{user_id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)
