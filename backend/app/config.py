from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # LLM API Keys
    GEMINI_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""

    # MongoDB Atlas Settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "code_review_db"

    # LangSmith Tracing Settings
    LANGCHAIN_TRACING_V2: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "ai-code-review-platform"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()


def setup_langsmith_tracing() -> bool:
    """Export LangSmith environment variables to enable project-wide tracing."""
    import os
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        return True
    return False


def get_settings() -> Settings:
    """Get global settings instance."""
    return settings
