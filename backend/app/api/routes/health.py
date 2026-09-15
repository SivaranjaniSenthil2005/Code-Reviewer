from fastapi import APIRouter
from app.database.connection import check_database_health

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint returning application and database status."""
    db_health = await check_database_health()
    return {
        "status": "ok",
        "database": db_health["status"],
    }
