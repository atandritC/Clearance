from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL
from pathlib import Path


class Settings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str

    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5433

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    demo_mode: bool = False
    jwt_secret_key: SecretStr
    access_token_expire_minutes: int = 30
    demo_user_password: SecretStr | None = None

    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_score_threshold: float = 0.68

    embedding_model: str = "BAAI/bge-small-en-v1.5"

    qdrant_collection: str = "clearance_documents"

    groq_api_key: SecretStr
    groq_model: str = "openai/gpt-oss-20b"
    groq_temperature: float = 0.2
    groq_max_completion_tokens: int = 1024
    groq_input_cost_per_million_tokens_usd: float = 0.075
    groq_output_cost_per_million_tokens_usd: float = 0.30

    @field_validator("jwt_secret_key")
    @classmethod
    def require_long_jwt_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters.")
        return value

    @field_validator("qdrant_score_threshold")
    @classmethod
    def require_valid_qdrant_score_threshold(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("QDRANT_SCORE_THRESHOLD must be between 0 and 1.")
        return value

    @property
    def database_url(self) -> URL:
        return URL.create(
            # Use PostgreSQL with the asyncpg driver.
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


settings = Settings()
