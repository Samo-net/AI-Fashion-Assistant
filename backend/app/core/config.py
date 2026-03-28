from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Fashion Assistant"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://fashionuser:fashionpass@localhost:5432/fashiondb"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_BUCKET_NAME: str = "ai-fashion-assistant"
    AWS_REGION: str = "us-east-1"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"  # Use mini for dev; switch to gpt-4o for evaluation

    # Replicate (SD + ControlNet during dev)
    REPLICATE_API_TOKEN: Optional[str] = None

    # OpenWeatherMap
    OPENWEATHER_API_KEY: Optional[str] = None

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:19006"]

    # Recommendation cache TTL (seconds)
    RECOMMENDATION_CACHE_TTL: int = 21600  # 6 hours

    # Visualization limits
    MAX_VISUALIZATIONS_PER_DAY: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
