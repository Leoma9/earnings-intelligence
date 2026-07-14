"""Collect and persist daily Google Trends interest for stock ticker searches."""

import time
from pathlib import Path

import pandas as pd
from pytrends.request import TrendReq

from config.settings import TRENDS_FILE, TRENDS_LOOKBACK_DAYS
from src.storage.csv_store import CSVStore


TREND_COLUMNS = ["date", "ticker", "trend_score"]


def fetch_trends_interest(
    tickers: list[str],
    lookback_days: int = TRENDS_LOOKBACK_DAYS,
    geo: str = "US",
    retry_count: int = 2,
) -> pd.DataFrame:
    """
    Return daily Google Trends interest scores for ticker search terms.

    Args:
        tickers: Ticker symbols to use as Google Trends search terms.
        lookback_days: Number of recent days to retrieve.
        geo: Two-letter country code used to scope searches; use "" globally.
        retry_count: Number of retries after a temporary Google API failure.

    Returns:
        DataFrame with columns: date, ticker, trend_score.
    """
    pytrends = TrendReq(hl="en-US", tz=360)
    timeframe = f"{lookback_days}-days-ago today"
    records: list[dict] = []

    # Google Trends accepts no more than five search terms in a request.
    batch_size = 5
    for i in range(0, len(tickers), batch_size):
        batch = _normalise_tickers(tickers[i : i + batch_size])
        if not batch:
            continue

        data = _fetch_batch_with_retries(
            pytrends, batch, timeframe, geo, retry_count
        )
        if data.empty:
            continue

        for ticker in batch:
            if ticker not in data.columns:
                print(f"Warning: Google Trends returned no scores for {ticker}.")
                continue

            for timestamp, score in data[ticker].items():
                records.append(
                    {
                        "date": timestamp.strftime("%Y-%m-%d"),
                        "ticker": ticker,
                        "trend_score": int(score),
                    }
                )

        # A short pause reduces the chance of Google temporarily rate-limiting us.
        time.sleep(1)

    return pd.DataFrame(records, columns=TREND_COLUMNS)


def save_trends_history(
    tickers: list[str],
    lookback_days: int = TRENDS_LOOKBACK_DAYS,
    output_path: Path | str = TRENDS_FILE,
    geo: str = "US",
) -> Path:
    """Fetch trends data and append it to the historical CSV without duplicates."""
    output_path = Path(output_path)
    trends = fetch_trends_interest(tickers, lookback_days, geo)

    if trends.empty:
        raise RuntimeError(
            "Google Trends returned no data. Existing history was left unchanged."
        )

    store = CSVStore(output_path.parent)
    store.append(trends, output_path.name, dedup_cols=["date", "ticker"])
    print(f"Saved {len(trends)} trend scores → {output_path}")
    return output_path


def _fetch_batch_with_retries(
    client: TrendReq,
    tickers: list[str],
    timeframe: str,
    geo: str,
    retry_count: int,
) -> pd.DataFrame:
    """Fetch one Google Trends batch, retrying temporary API/network errors."""
    for attempt in range(retry_count + 1):
        try:
            client.build_payload(tickers, cat=0, timeframe=timeframe, geo=geo)
            return client.interest_over_time()
        except Exception as exc:
            if attempt == retry_count:
                print(
                    f"Warning: skipped {', '.join(tickers)} after "
                    f"{retry_count + 1} failed Google Trends attempt(s): {exc}"
                )
                return pd.DataFrame()

            wait_seconds = 2**attempt
            print(
                f"Warning: Google Trends request failed for {', '.join(tickers)}. "
                f"Retrying in {wait_seconds}s..."
            )
            time.sleep(wait_seconds)

    return pd.DataFrame()


def _normalise_tickers(tickers: list[str]) -> list[str]:
    """Remove blank values and normalize symbols before sending requests."""
    return [ticker.strip().upper() for ticker in tickers if ticker.strip()]


# Example:
# from src.collectors.google_trends import save_trends_history
# save_trends_history(["AAPL", "MSFT", "NVDA"])
#
# The CSV is saved at data/raw/google_trends.csv:
# date,ticker,trend_score
# 2026-07-13,AAPL,42
