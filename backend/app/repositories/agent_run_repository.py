"""Repository for logging agent execution runs, trace data, and metrics."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.client import get_database


class AgentRunRepository:
    """Repository managing CRUD operations for the 'agent_runs' collection."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db = db

    @property
    def collection(self):
        db = self._db if self._db is not None else get_database()
        return db["agent_runs"]

    def _format_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return doc

    async def create(self, agent_run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an agent run log document."""
        data = dict(agent_run_data)
        now = datetime.now(timezone.utc)
        data.setdefault("created_at", now)
        data.setdefault("status", "running")

        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return self._format_doc(data)  # type: ignore

    async def get_by_id(self, agent_run_id: str) -> Optional[Dict[str, Any]]:
        """Fetch an agent run record by ID."""
        try:
            oid = ObjectId(agent_run_id)
        except (InvalidId, TypeError):
            return None
        doc = await self.collection.find_one({"_id": oid})
        return self._format_doc(doc)

    async def list_by_review_id(self, review_id: str) -> List[Dict[str, Any]]:
        """List all agent run execution logs for a given review."""
        cursor = self.collection.find({"review_id": review_id}).sort("created_at", 1)
        docs = await cursor.to_list(length=100)
        return [self._format_doc(d) for d in docs if d]  # type: ignore

    async def list(
        self, filter_query: Optional[Dict[str, Any]] = None, limit: int = 50, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List agent run records with optional filtering and pagination."""
        query = filter_query or {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._format_doc(d) for d in docs if d]  # type: ignore

    async def update(self, agent_run_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing agent run log by ID."""
        try:
            oid = ObjectId(agent_run_id)
        except (InvalidId, TypeError):
            return None

        data = dict(update_data)
        data["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": data},
            return_document=True,
        )
        return self._format_doc(result)

    async def delete(self, agent_run_id: str) -> bool:
        """Delete an agent run document by ID."""
        try:
            oid = ObjectId(agent_run_id)
        except (InvalidId, TypeError):
            return False
        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0
