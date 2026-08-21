"""Base repository connection manager for asyncpg PostgreSQL connections."""

from typing import Any, List, Optional
from app.core.config import settings
from app.core.logging import logger

_db_pool: Optional[Any] = None


async def init_db_pool() -> Optional[Any]:
    global _db_pool
    if not settings.DATABASE_URL:
        logger.warning("DATABASE_URL not configured; repository queries will operate in fallback mode")
        return None
    try:
        import asyncpg
        _db_pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=settings.DB_POOL_MIN_SIZE,
            max_size=settings.DB_POOL_MAX_SIZE,
        )
        logger.info("PostgreSQL connection pool initialized successfully")
        return _db_pool
    except ImportError:
        logger.info("asyncpg not installed in local environment; repositories operating in in-memory mode")
        return None
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}); repository queries will use in-memory fallback")
        return None


async def close_db_pool() -> None:
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
        logger.info("PostgreSQL connection pool closed")


def get_db_pool() -> Optional[Any]:
    return _db_pool
