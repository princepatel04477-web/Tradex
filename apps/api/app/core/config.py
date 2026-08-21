"""Application settings and configuration management via Pydantic Settings."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application
    APP_NAME: str = "Tradly API"
    APP_ENV: str = Field(default="development", description="development, staging, production")
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server & Networking
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://tradex-main.vercel.app",
        "https://tradly.vercel.app",
    ]

    # Database (Neon PostgreSQL with pgvector)
    DATABASE_URL: Optional[str] = "postgresql://tradly:tradlypass@localhost:5432/tradly"
    DIRECT_URL: Optional[str] = None
    DB_POOL_MIN_SIZE: int = 2
    DB_POOL_MAX_SIZE: int = 10

    # Hot Cache & Task Broker (Redis)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Auth
    JWT_SECRET_KEY: str = Field(
        default="tradly-production-jwt-secret-key-change-in-env-file-min-32-chars",
        description="Must be set in production env var"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Market Data Providers (twelvedata, yahoo, finnhub, oanda, fake)
    MARKET_DATA_PROVIDER: str = "twelvedata"
    TWELVEDATA_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    OANDA_API_KEY: Optional[str] = None
    OANDA_ACCOUNT_ID: Optional[str] = None
    OANDA_ENVIRONMENT: str = "practice"  # practice or live
    OANDA_RATE_LIMIT_RPS: int = 120

    # LLM & AI Providers
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    PERPLEXITY_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None

    # Responsible AI & Financial Disclaimer
    AI_DISCLAIMER: str = (
        "TRADLY RESPONSIBLE AI DISCLAIMER: All AI-generated market intelligence, "
        "sentiment scores, and technical signals are strictly informational and educational. "
        "Tradly does not provide financial or investment advice. Forex trading involves "
        "substantial risk of loss."
    )


settings = Settings()
