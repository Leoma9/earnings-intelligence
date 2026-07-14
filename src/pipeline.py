"""The core data-refresh pipeline, reusable from a CLI, scheduler, or app.

Both ``scripts/refresh_data.py`` (command line / cron / GitHub Actions) and
the Streamlit app's admin-gated "Refresh data now" button call
``run_refresh_pipeline`` so there is exactly one implementation to keep in
sync with the storage schema and scoring model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from config.settings import DATABASE_FILE
from src.analytics.growth_ranking import calculate_growth_metrics
from src.analytics.scoring import calculate_attention_scores
from src.collectors.earnings_calendar import fetch_upcoming_earnings
from src.collectors.google_trends import fetch_trends_interest
from src.collectors.market_data import fetch_market_data
from src.storage.sqlite_store import SQLiteStore


@dataclass
class PipelineResult:
    """Outcome of one refresh run, used for CLI printing and UI feedback."""

    tickers_found: int = 0
    trends_collected: bool = False
    rankings: pd.DataFrame = field(default_factory=pd.DataFrame)
    messages: list[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        self.messages.append(message)


def run_refresh_pipeline(database_path=DATABASE_FILE) -> PipelineResult:
    """Collect fresh data, store it, and recompute attention scores.

    Safe to call repeatedly (all storage operations are idempotent upserts).
    Any collector failure for one ticker does not stop the overall run.
    """
    result = PipelineResult()
    store = SQLiteStore(database_path)

    result.log("Fetching upcoming earnings...")
    earnings = fetch_upcoming_earnings()
    if not earnings.empty:
        tickers = earnings["ticker"].tolist()
        result.tickers_found = len(tickers)
        result.log(f"Found {len(tickers)} companies: {', '.join(tickers)}")
        store.upsert_earnings(earnings)

        result.log("Fetching market data...")
        market = fetch_market_data(tickers)
        store.upsert_daily_metrics(market)

        result.log("Fetching Google Trends interest...")
        trends = fetch_trends_interest(tickers)
        if trends.empty:
            result.log("Google Trends returned no data (rate limit or network issue).")
        else:
            store.upsert_daily_metrics(trends)
            result.trends_collected = True
    else:
        result.log("No upcoming earnings found in this refresh; rescoring existing history.")

    result.log("Calculating attention scores...")
    all_metrics = store.get_all_daily_metrics()
    growth = calculate_growth_metrics(all_metrics)

    if growth.empty:
        result.log("No metric history available yet — no scores produced.")
        return result

    rankings = calculate_attention_scores(growth)
    store.upsert_attention_scores(rankings, calculation_date=date.today().isoformat())
    result.rankings = rankings
    result.log(f"Saved {len(rankings)} attention score(s).")
    return result
