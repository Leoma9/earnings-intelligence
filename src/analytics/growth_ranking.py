"""Calculate multi-period growth signals and rank companies by momentum.

Example:
    from src.storage.sqlite_store import SQLiteStore
    from config.settings import DATABASE_FILE
    from src.analytics.growth_ranking import rank_companies_by_growth

    store = SQLiteStore(DATABASE_FILE)
    rankings = rank_companies_by_growth(store.get_all_daily_metrics())
    print(rankings.head())
"""

from __future__ import annotations

import pandas as pd


GROWTH_PERIODS = (1, 3, 7, 30)
SIGNALS = {
    "social_mentions": "social",
    "volume": "volume",
    "close": "price",
}


def calculate_growth_metrics(daily_metrics: pd.DataFrame) -> pd.DataFrame:
    """Calculate 1, 3, 7, and 30-day percentage growth for each ticker.

    Args:
        daily_metrics: A DataFrame containing ``date``, ``ticker``,
            ``social_mentions``, ``volume``, and ``close``. Fields can be
            null when a source did not return data.

    Returns:
        One row per ticker. Growth is calculated as
        ``(latest value / value N days earlier - 1) * 100``. If no value is
        available on the target date, the closest earlier observation is used.
        A metric is ``NaN`` when insufficient history or source data exists.
    """
    metrics = daily_metrics.copy()
    _validate_metrics(metrics)
    metrics["date"] = pd.to_datetime(metrics["date"])
    metrics = metrics.sort_values(["ticker", "date"])

    records: list[dict[str, object]] = []
    for ticker, ticker_data in metrics.groupby("ticker", sort=False):
        latest_row = ticker_data.iloc[-1]
        record: dict[str, object] = {
            "ticker": ticker,
            "latest_date": latest_row["date"].date().isoformat(),
        }

        for source_column, label in SIGNALS.items():
            for days in GROWTH_PERIODS:
                record[f"{label}_{days}d_growth_pct"] = _growth_for_period(
                    ticker_data, source_column, days
                )

        records.append(record)

    return pd.DataFrame(records)


def rank_companies_by_growth(daily_metrics: pd.DataFrame) -> pd.DataFrame:
    """Return companies ranked by equally weighted available growth signals.

    The ``growth_score`` is the arithmetic mean of all available 1-, 3-, 7-,
    and 30-day growth percentages across social mentions, volume, and price.
    It is a simple V1 momentum ranking, not investment advice.
    """
    growth = calculate_growth_metrics(daily_metrics)
    if growth.empty:
        return growth

    growth_columns = [
        f"{label}_{days}d_growth_pct"
        for label in SIGNALS.values()
        for days in GROWTH_PERIODS
    ]
    growth["growth_score"] = growth[growth_columns].mean(axis=1, skipna=True).round(2)
    growth = growth.dropna(subset=["growth_score"])
    growth = growth.sort_values(
        ["growth_score", "ticker"], ascending=[False, True]
    ).reset_index(drop=True)
    growth.index = growth.index + 1
    growth.index.name = "rank"
    return growth


def _growth_for_period(
    ticker_data: pd.DataFrame, column: str, days: int
) -> float | None:
    """Calculate a percentage change from the latest value to N days earlier."""
    usable_data = ticker_data.dropna(subset=[column])
    if usable_data.empty:
        return None

    latest = usable_data.iloc[-1]
    target_date = latest["date"] - pd.Timedelta(days=days)
    historical = usable_data[usable_data["date"] <= target_date]
    if historical.empty:
        return None

    previous_value = historical.iloc[-1][column]
    current_value = latest[column]
    if previous_value == 0:
        return None

    return round(((current_value - previous_value) / previous_value) * 100, 2)


def _validate_metrics(daily_metrics: pd.DataFrame) -> None:
    """Fail early with a clear message when a caller supplies the wrong data."""
    required_columns = {"date", "ticker"}
    missing = required_columns - set(daily_metrics.columns)
    if missing:
        raise ValueError(
            "daily_metrics is missing required column(s): " + ", ".join(sorted(missing))
        )

    # ``trend_score`` (Google Trends) and ``reddit_mentions`` (Reddit) were
    # earlier column names for this signal; support them transparently for
    # any caller not yet migrated to the generic ``social_mentions`` name.
    if "social_mentions" not in daily_metrics.columns:
        for legacy_column in ("trend_score", "reddit_mentions"):
            if legacy_column in daily_metrics.columns:
                daily_metrics.rename(
                    columns={legacy_column: "social_mentions"}, inplace=True
                )
                break

    for column in SIGNALS:
        if column not in daily_metrics.columns:
            daily_metrics[column] = pd.NA
