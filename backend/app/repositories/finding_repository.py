"""Repository for managing code review findings, issues, and suggestions."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.client import get_database


class FindingRepository:
    """Repository managing CRUD operations for the 'review_findings' collection."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db = db

    @property
    def collection(self):
        db = self._db if self._db is not None else get_database()
        return db["review_findings"]

    def _format_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return doc

    async def create(self, finding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single finding record."""
        data = dict(finding_data)
        now = datetime.now(timezone.utc)
        data.setdefault("created_at", now)

        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return self._format_doc(data)  # type: ignore

    async def create_many(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk insert multiple findings."""
        if not findings:
            return []
        now = datetime.now(timezone.utc)
        to_insert = []
        for f in findings:
            d = dict(f)
            d.setdefault("created_at", now)
            to_insert.append(d)

        result = await self.collection.insert_many(to_insert)
        for d, inserted_id in zip(to_insert, result.inserted_ids):
            d["_id"] = inserted_id
        return [self._format_doc(d) for d in to_insert]  # type: ignore

    async def get_by_id(self, finding_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single finding by ID."""
        try:
            oid = ObjectId(finding_id)
        except (InvalidId, TypeError):
            return None
        doc = await self.collection.find_one({"_id": oid})
        return self._format_doc(doc)

    async def list_by_review_id(self, review_id: str) -> List[Dict[str, Any]]:
        """List all findings associated with a specific code review."""
        cursor = self.collection.find({"review_id": review_id}).sort("line", 1)
        docs = await cursor.to_list(length=500)
        return [self._format_doc(d) for d in docs if d]  # type: ignore

    async def list(
        self, filter_query: Optional[Dict[str, Any]] = None, limit: int = 50, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List review findings with optional filtering and pagination."""
        query = filter_query or {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._format_doc(d) for d in docs if d]  # type: ignore

    async def update(self, finding_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing finding by ID."""
        try:
            oid = ObjectId(finding_id)
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

    async def delete(self, finding_id: str) -> bool:
        """Delete a finding document by ID."""
        try:
            oid = ObjectId(finding_id)
        except (InvalidId, TypeError):
            return False
        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0
