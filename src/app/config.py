"""Settings loaded from environment variables / .env (Spring: application.properties)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mini Bank"
    exchange_api_url: str = "https://api.frankfurter.dev/v1"
    http_timeout_seconds: float = 5.0

    # Env var names match field names, case-insensitive: EXCHANGE_API_URL -> exchange_api_url
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
