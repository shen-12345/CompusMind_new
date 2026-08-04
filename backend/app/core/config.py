from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "校事通"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://compusmind:compusmind_dev@localhost:5432/compusmind"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://compusmind:compusmind_dev@localhost:5432/compusmind"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    PASSWORD_MIN_LENGTH: int = 8
    LOGIN_LOCK_THRESHOLD: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    # LLM
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_URL: Optional[str] = "https://api.deepseek.com/v1/chat/completions"

    # Embedding
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_API_URL: Optional[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
    EMBEDDING_MODEL: str = "text-embedding-v2"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()