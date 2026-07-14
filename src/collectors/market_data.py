"""Collect stock market data for tracked companies."""

from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from config.settings import TRENDS_LOOKBACK_DAYS


def fetch_market_data(
    tickers: list[str],
    lookback_days: int = TRENDS_LOOKBACK_DAYS,
) -> pd.DataFrame:
    """
    Return daily market metrics for each ticker.

    Columns: date, ticker, close, volume, avg_volume_30d, price_change_pct
    """
    start = date.today() - timedelta(days=lookback_days)
    records: list[dict] = []

    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(start=start.isoformat())
            if hist.empty:
                continue

            hist = hist.reset_index()
            avg_volume = hist["Volume"].tail(30).mean()

            for _, row in hist.iterrows():
                records.append(
                    {
                        "date": row["Date"].strftime("%Y-%m-%d"),
                        "ticker": ticker,
                        "close": round(row["Close"], 2),
                        "volume": int(row["Volume"]),
                        "avg_volume_30d": int(avg_volume),
                        "price_change_pct": round(
                            (row["Close"] - hist["Close"].iloc[0])
                            / hist["Close"].iloc[0]
                            * 100,
                            2,
                        ),
                    }
                )
        except Exception:
            continue

    return pd.DataFrame(records)
