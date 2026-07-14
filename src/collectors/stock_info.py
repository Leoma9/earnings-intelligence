"""
Collect current stock market snapshots from Yahoo Finance.

Each ticker returns a single row with price, volume, market cap, and sector.
Results can be saved directly to CSV.
"""

from pathlib import Path

import pandas as pd
import yfinance as yf

from config.settings import RAW_DIR, STOCK_INFO_FILE


def fetch_stock_info(tickers: list[str]) -> pd.DataFrame:
    """
    Fetch current market information for a list of ticker symbols.

    Args:
        tickers: List of stock ticker symbols (e.g. ["AAPL", "MSFT"]).

    Returns:
        DataFrame with one row per successfully fetched ticker.
        Columns: ticker, current_price, daily_change_pct, volume,
                  market_cap, sector, fetched_at
    """
    records: list[dict] = []
    errors: list[str] = []

    for ticker in tickers:
        # Normalize ticker to uppercase for consistent Yahoo Finance lookups
        symbol = ticker.strip().upper()
        if not symbol:
            continue

        try:
            record = _fetch_single_ticker(symbol)
            if record:
                records.append(record)
            else:
                errors.append(f"{symbol}: no data returned")
        except Exception as exc:
            # Log the failure but keep processing remaining tickers
            errors.append(f"{symbol}: {exc}")

    if errors:
        print(f"Warning — {len(errors)} ticker(s) skipped:")
        for msg in errors:
            print(f"  - {msg}")

    return pd.DataFrame(records)


def _fetch_single_ticker(ticker: str) -> dict | None:
    """
    Fetch market snapshot for one ticker from Yahoo Finance.

    Uses both the .info dict (fundamentals) and recent price history
    (for accurate daily change and volume).
    """
    stock = yf.Ticker(ticker)

    # .info provides sector, market cap, and current price
    info = stock.info
    if not info or info.get("regularMarketPrice") is None:
        return None

    # Recent history gives us today's volume and daily price change
    history = stock.history(period="5d")
    if history.empty:
        return None

    latest = history.iloc[-1]
    previous_close = info.get("previousClose") or history.iloc[-2]["Close"]

    current_price = info.get("regularMarketPrice", latest["Close"])
    daily_change_pct = _calculate_daily_change(current_price, previous_close)

    return {
        "ticker": ticker,
        "current_price": round(float(current_price), 2),
        "daily_change_pct": round(daily_change_pct, 2),
        "volume": int(latest["Volume"]),
        "market_cap": int(info.get("marketCap", 0)),
        "sector": info.get("sector", "Unknown"),
        "fetched_at": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def _calculate_daily_change(current_price: float, previous_close: float) -> float:
    """Calculate percentage change from the previous closing price."""
    if previous_close and previous_close > 0:
        return ((current_price - previous_close) / previous_close) * 100
    return 0.0


def save_stock_info(
    tickers: list[str],
    output_path: Path | str | None = None,
) -> Path:
    """
    Fetch stock info for tickers and save results to a CSV file.

    Args:
        tickers: List of ticker symbols to fetch.
        output_path: Destination CSV path. Defaults to data/raw/stock_info.csv.

    Returns:
        Path to the saved CSV file.
    """
    if output_path is None:
        output_path = STOCK_INFO_FILE
    else:
        output_path = Path(output_path)

    # Ensure the output directory exists before writing
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = fetch_stock_info(tickers)

    if df.empty:
        raise ValueError("No stock data collected — CSV was not written.")

    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} ticker(s) → {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Example usage — run this file directly to test:
#   python -m src.collectors.stock_info
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_tickers = ["AAPL", "MSFT", "GOOGL", "INVALID_TICKER"]

    print("Fetching stock info...")
    output = save_stock_info(sample_tickers)

    df = pd.read_csv(output)
    print("\nResults:")
    print(df.to_string(index=False))
