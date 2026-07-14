"""Data collectors package."""

from src.collectors.earnings_calendar import (
    EarningsCalendarProvider,
    YahooFinanceEarningsProvider,
    fetch_upcoming_earnings,
    save_upcoming_earnings,
)
from src.collectors.google_trends import fetch_trends_interest, save_trends_history
from src.collectors.market_data import fetch_market_data
from src.collectors.stock_info import fetch_stock_info, save_stock_info

__all__ = [
    "fetch_upcoming_earnings",
    "fetch_market_data",
    "fetch_stock_info",
    "fetch_trends_interest",
    "save_trends_history",
    "save_stock_info",
    "save_upcoming_earnings",
    "EarningsCalendarProvider",
    "YahooFinanceEarningsProvider",
]
