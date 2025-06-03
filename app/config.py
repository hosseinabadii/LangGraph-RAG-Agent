import logging
from datetime import datetime
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

# Set up logging
LOGS_DIR = BASE_DIR / "logs"
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOGS_DIR / f"api_{datetime.now().strftime('%Y%m%d')}.log"), logging.StreamHandler()],
)


class Settings(BaseSettings):
    base_url: str
    api_key: SecretStr = Field(alias="OPENAI_API_KEY")
    db_path: str = str(BASE_DIR / "rag.db")

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


settings = Settings()  # type: ignore
