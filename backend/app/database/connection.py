"""Database connection lifecycle management, health check, and retry backoff handling."""

import asyncio
import logging
from typing import Dict, Any
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from app.database.client import get_motor_client, get_database, close_motor_client

logger = logging.getLogger(__name__)


async def connect_to_mongo(max_retries: int = 3, initial_delay: float = 1.0) -> bool:
    """Attempt connection to MongoDB with retry backoff.
    
    Returns True if connection ping succeeds, False if unreachable after retries.
    Gracefully logs error instead of crashing application startup.
    """
    client = get_motor_client()
    delay = initial_delay

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Connecting to MongoDB (attempt {attempt}/{max_retries})...")
            # The ping command forces a server selection check
            await client.admin.command("ping")
            logger.info("Successfully connected to MongoDB.")
            return True
        except (ServerSelectionTimeoutError, PyMongoError, Exception) as exc:
            logger.warning(
                f"MongoDB connection attempt {attempt}/{max_retries} failed: {exc}. Retrying in {delay}s..."
            )
            if attempt < max_retries:
                await asyncio.sleep(delay)
                delay *= 2.0

    logger.error("MongoDB is unreachable after maximum connection retries. App starting in degraded state.")
    return False


async def close_mongo_connection() -> None:
    """Close MongoDB connection pool on shutdown."""
    close_motor_client()


async def check_database_health() -> Dict[str, Any]:
    """Check database connection status for health checks."""
    try:
        client = get_motor_client()
        await client.admin.command("ping")
        return {"status": "connected"}
    except Exception as exc:
        logger.warning(f"Health check failed to ping MongoDB: {exc}")
        return {"status": "disconnected", "error": str(exc)}
