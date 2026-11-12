from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
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

    qdrant_url: str = "http://127.0.0.1:6333"

    embedding_model: str = "BAAI/bge-small-en-v1.5"

    qdrant_collection: str = "clearance_documents"

    groq_api_key: SecretStr
    groq_model: str = "openai/gpt-oss-20b"
    groq_temperature: float = 0.2
    groq_max_completion_tokens: int = 1024
    groq_input_cost_per_million_tokens_usd: float = 0.075
    groq_output_cost_per_million_tokens_usd: float = 0.30

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
