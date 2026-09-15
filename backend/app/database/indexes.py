"""Database indexing definitions and schema index setup."""

import logging
from typing import Dict, List, Optional
from pymongo import IndexModel, ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.client import get_database

logger = logging.getLogger(__name__)

# Index specifications for MongoDB collections
INDEX_DEFINITIONS: Dict[str, List[IndexModel]] = {
    "users": [
        IndexModel([("email", ASCENDING)], unique=True, name="idx_users_email_unique"),
        IndexModel([("created_at", DESCENDING)], name="idx_users_created_at"),
    ],
    "code_reviews": [
        IndexModel([("user_id", ASCENDING)], name="idx_reviews_user_id"),
        IndexModel([("created_at", DESCENDING)], name="idx_reviews_created_at_desc"),
        IndexModel([("status", ASCENDING)], name="idx_reviews_status"),
        IndexModel([("mode", ASCENDING)], name="idx_reviews_mode"),
    ],
    "review_findings": [
        IndexModel([("review_id", ASCENDING)], name="idx_findings_review_id"),
        IndexModel([("severity", ASCENDING)], name="idx_findings_severity"),
        IndexModel([("category", ASCENDING)], name="idx_findings_category"),
    ],
    "agent_runs": [
        IndexModel([("review_id", ASCENDING)], name="idx_agent_runs_review_id"),
        IndexModel([("agent_name", ASCENDING)], name="idx_agent_runs_agent_name"),
        IndexModel([("created_at", DESCENDING)], name="idx_agent_runs_created_at"),
    ],
}


async def create_database_indexes(db: Optional[AsyncIOMotorDatabase] = None) -> Dict[str, List[str]]:
    """Create indexes for all application collections.
    
    Returns a dictionary mapping collection names to created index names.
    """
    if db is None:
        db = get_database()

    created_indexes: Dict[str, List[str]] = {}

    for collection_name, models in INDEX_DEFINITIONS.items():
        try:
            collection = db[collection_name]
            result = await collection.create_indexes(models)
            created_indexes[collection_name] = result
            logger.info(f"Created indexes for collection '{collection_name}': {result}")
        except Exception as exc:
            logger.warning(f"Failed to create indexes for collection '{collection_name}': {exc}")
            created_indexes[collection_name] = []

    return created_indexes
