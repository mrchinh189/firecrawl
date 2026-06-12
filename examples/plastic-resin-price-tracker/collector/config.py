"""Cau hinh tap trung, doc tu bien moi truong + sources.json."""
import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:  # dotenv khong bat buoc (vd khi chay unit test)
    pass

ROOT = Path(__file__).resolve().parent.parent
SOURCES_PATH = Path(os.environ.get("SOURCES_PATH", ROOT / "sources.json"))

# Firecrawl
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

# Database
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://resin:resin@db:5432/resin"
)

# FX
# Ti gia mac dinh (fallback) khi khong goi duoc API ti gia.
FX_USD_VND_FALLBACK = float(os.environ.get("FX_USD_VND_FALLBACK", "25400"))
FX_API_URL = os.environ.get("FX_API_URL", "https://open.er-api.com/v6/latest/USD")

# Canh bao
ALERT_THRESHOLD_PCT = float(os.environ.get("ALERT_THRESHOLD_PCT", "2"))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Lich chay (mac dinh: 07:00 thu Hai hang tuan)
SCHEDULE_DAY_OF_WEEK = os.environ.get("SCHEDULE_DAY_OF_WEEK", "mon")
SCHEDULE_HOUR = int(os.environ.get("SCHEDULE_HOUR", "7"))
SCHEDULE_MINUTE = int(os.environ.get("SCHEDULE_MINUTE", "0"))
SCHEDULE_TZ = os.environ.get("SCHEDULE_TZ", "Asia/Ho_Chi_Minh")
RUN_ON_START = os.environ.get("RUN_ON_START", "false").lower() == "true"


def load_sources_config() -> dict:
    with SOURCES_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)
