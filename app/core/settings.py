from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file.

    You can add more configuration items here as the backend grows.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # FastAPI
    app_name: str = "mxy-python API"
    app_version: str = "0.1.0"

    # DeepSeek / LLM
    deepseek_api_key: str | None = 'sk-77c7047241e7436490f08b5abf391a6a'
    deepseek_model: str = "deepseek-chat"
    deepseek_temperature: float = 0.3
    deepseek_base_url: str = "https://api.deepseek.com"

    # LangChain system prompt
    system_prompt: str = "You are a helpful AI assistant."

    # MySQL Database
    db_host: str = "localhost"
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "fastgpt"
    db_charset: str = "utf8mb4"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
