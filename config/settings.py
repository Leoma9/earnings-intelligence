"""Application configuration and constants."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_FILE = DATA_DIR / "earnings_intelligence.db"
DATA_STATUS_FILE = PROJECT_ROOT / "site" / "data-status.json"
# Same URL the marketing site uses so /app and marketslite.com share one stamp.
PUBLIC_DATA_STATUS_URL = (
    "https://raw.githubusercontent.com/Leoma9/earnings-intelligence/main/site/data-status.json"
)

EARNINGS_LOOKAHEAD_DAYS = 30
SOCIAL_LOOKBACK_DAYS = 90
TICKER_UNIVERSE_SIZE = 100

EARNINGS_FILE = RAW_DIR / "earnings_calendar.csv"
MARKET_DATA_FILE = RAW_DIR / "market_data.csv"
STOCK_INFO_FILE = RAW_DIR / "stock_info.csv"
SOCIAL_MENTIONS_FILE = RAW_DIR / "social_mentions.csv"
RANKINGS_FILE = PROCESSED_DIR / "rankings.csv"
