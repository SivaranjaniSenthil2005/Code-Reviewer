import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.database.indexes import create_database_indexes
from app.api.routes.health import router as health_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan handler."""
    logger.info("Starting up application...")
    # Non-blocking connection check with retries
    is_connected = await connect_to_mongo(max_retries=2, initial_delay=0.5)
    if is_connected:
        await create_database_indexes()
    yield
    logger.info("Shutting down application...")
    await close_mongo_connection()


app = FastAPI(
    title="AI Code Review & Refactoring Platform API",
    description="Multi-agent platform for code review, security vulnerability detection, and refactoring.",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Enable CORS for localhost frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint welcome message."""
    return {
        "name": "AI Code Review & Refactoring Platform API",
        "status": "online",
        "docs": "/docs",
    }
