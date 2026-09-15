from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes.health import router as health_router

app = FastAPI(
    title="AI Code Review & Refactoring Platform API",
    description="Multi-agent platform for code review, security vulnerability detection, and refactoring.",
    version="1.0.0",
    debug=settings.DEBUG,
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
