"""Database client instance and connection pool configuration."""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

logger = logging.getLogger(__name__)

_mongo_client: Optional[AsyncIOMotorClient] = None


def get_motor_client() -> AsyncIOMotorClient:
    """Get or initialize the global AsyncIOMotorClient instance."""
    global _mongo_client
    if _mongo_client is None:
        logger.info(f"Initializing Motor Mongo client targeting URI: {settings.MONGODB_URI}")
        _mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
    return _mongo_client


def set_motor_client(client: AsyncIOMotorClient) -> None:
    """Override global Motor client instance (primarily used for unit/integration testing)."""
    global _mongo_client
    _mongo_client = client


def get_database() -> AsyncIOMotorDatabase:
    """Get the active Motor database instance for the application."""
    client = get_motor_client()
    return client[settings.MONGODB_DATABASE]


def close_motor_client() -> None:
    """Gracefully close the global Motor client connection pool."""
    global _mongo_client
    if _mongo_client is not None:
        logger.info("Closing Motor Mongo client connection pool.")
        _mongo_client.close()
        _mongo_client = None
