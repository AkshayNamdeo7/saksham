from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required — must be set (e.g. DATABASE_URL=postgresql://...@ep-xxx.neon.tech/dbname?sslmode=require).
    # There is NO default.  A missing or empty value produces a clear startup error
    # instead of silently falling back to a local SQLite file.
    DATABASE_URL: str = ""

    JWT_SECRET: str = "change-me-to-a-strong-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o-mini"

    MAP_TILE_URL: str = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

    SEED_ON_STARTUP: int = 1
    DEMO_MODE: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _validate_database_url(self) -> "Settings":
        if not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL is required. "
                "Set it in Vercel project settings (api service env var) to your "
                "Neon PostgreSQL URL, e.g. "
                "postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require"
            )
        return self


settings = Settings()
