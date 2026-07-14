"""Collect and persist daily social-mention counts for stock tickers.

Uses StockTwits' free, public, unauthenticated symbol-stream endpoint to
count how many messages mention each ticker per day. No API key, OAuth
app, or registration is required, which makes it far more reliable for a
small personal project than Reddit (which now requires manual, multi-week
API approval) or Google Trends (an unofficial, frequently-broken scrape).

The collector module is source-specific, but downstream code (storage,
analytics, dashboard) only ever sees a generic ``social_mentions`` signal —
if StockTwits ever becomes unavailable, only this file needs to change.

Limitation: StockTwits' public stream only returns each symbol's ~30 most
recent messages (no arbitrary date-range search), so very actively
discussed tickers can have their daily count saturate at that cap, and
historical days beyond what's already stored build up gradually each time
the pipeline runs — the same way price history already accumulates.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from config.settings import SOCIAL_LOOKBACK_DAYS, SOCIAL_MENTIONS_FILE
from src.storage.csv_store import CSVStore


MENTION_COLUMNS = ["date", "ticker", "social_mentions"]

_STREAM_URL = "https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
_USER_AGENT = "earnings-intelligence-platform/1.0"
_REQUEST_DELAY_SECONDS = 0.3  # polite pacing; StockTwits allows 200 req/hour/IP


def fetch_social_mentions(
    tickers: list[str],
    lookback_days: int = SOCIAL_LOOKBACK_DAYS,
    timeout: float = 10.0,
) -> pd.DataFrame:
    """Return daily StockTwits mention counts for each ticker.

    Args:
        tickers: Ticker symbols to look up.
        lookback_days: Discard messages older than this many days.
        timeout: Per-request timeout in seconds.

    Returns:
        DataFrame with columns: date, ticker, social_mentions. Returns an
        empty DataFrame if every ticker fails (network issue, etc.).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    records: list[dict] = []

    for ticker in _normalise_tickers(tickers):
        try:
            response = requests.get(
                _STREAM_URL.format(ticker=ticker),
                headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            print(f"Warning: skipped {ticker} — StockTwits API error: {exc}")
            continue
        finally:
            time.sleep(_REQUEST_DELAY_SECONDS)

        if payload.get("response", {}).get("status") != 200:
            print(f"Warning: StockTwits has no data for {ticker}.")
            continue

        daily_counts: dict[str, int] = defaultdict(int)
        for message in payload.get("messages", []):
            created = _parse_timestamp(message.get("created_at"))
            if created is None or created < cutoff:
                continue
            daily_counts[created.date().isoformat()] += 1

        for mention_date, count in daily_counts.items():
            records.append(
                {"date": mention_date, "ticker": ticker, "social_mentions": count}
            )

    return pd.DataFrame(records, columns=MENTION_COLUMNS)


def save_social_mentions_history(
    tickers: list[str],
    lookback_days: int = SOCIAL_LOOKBACK_DAYS,
    output_path: Path | str = SOCIAL_MENTIONS_FILE,
) -> Path:
    """Fetch social mentions and append them to the historical CSV without duplicates."""
    output_path = Path(output_path)
    mentions = fetch_social_mentions(tickers, lookback_days)

    if mentions.empty:
        raise RuntimeError(
            "StockTwits returned no mention data. Existing history was left unchanged."
        )

    store = CSVStore(output_path.parent)
    store.append(mentions, output_path.name, dedup_cols=["date", "ticker"])
    print(f"Saved {len(mentions)} social mention count(s) → {output_path}")
    return output_path


def _parse_timestamp(created_at: str | None) -> datetime | None:
    """Parse a StockTwits ISO-8601 timestamp (e.g. '2026-07-14T12:47:35Z')."""
    if not created_at:
        return None
    try:
        return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalise_tickers(tickers: list[str]) -> list[str]:
    """Remove blank values and normalize symbols before sending requests."""
    return [ticker.strip().upper() for ticker in tickers if ticker.strip()]


# Example:
# from src.collectors.social_mentions import save_social_mentions_history
# save_social_mentions_history(["AAPL", "MSFT", "NVDA"])
#
# The CSV is saved at data/raw/social_mentions.csv:
# date,ticker,social_mentions
# 2026-07-14,AAPL,12
