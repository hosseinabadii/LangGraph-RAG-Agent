from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    base_url: str
    api_key: SecretStr = Field(alias="OPENAI_API_KEY")

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


settings = Settings()  # type: ignore
