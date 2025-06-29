import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOGS_DIR = BASE_DIR / "logs"
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOGS_DIR / f"gui_{datetime.now().strftime('%Y%m%d')}.log"), logging.StreamHandler()],
)


@dataclass
class Settings:
    base_dir: Path = BASE_DIR
    base_url: str = "http://localhost:8000/api/v1"


settings = Settings()
