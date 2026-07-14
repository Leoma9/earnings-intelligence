"""Configurable 0–100 attention scoring for earnings candidates.

Example:
    import pandas as pd
    from src.analytics.scoring import calculate_attention_scores

    growth = pd.DataFrame(
        {
            "ticker": ["AAPL", "MSFT"],
            "google_trends_7d_growth_pct": [60, 20],
            "volume_7d_growth_pct": [40, 80],
            "price_7d_growth_pct": [10, 5],
        }
    )
    ranked = calculate_attention_scores(growth)
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AttentionScoreConfig:
    """Weights and caps used to calculate the Version 1 attention score.

    Weights must total 1.0. Caps convert percentage growth to a bounded
    0–100 signal; a growth rate at or above a cap receives 100 points.
    """

    google_trends_weight: float = 0.50
    volume_weight: float = 0.30
    price_weight: float = 0.20
    google_trends_cap_pct: float = 100.0
    volume_cap_pct: float = 100.0
    price_cap_pct: float = 30.0
    growth_period_days: int = 7

    def __post_init__(self) -> None:
        weights = (
            self.google_trends_weight,
            self.volume_weight,
            self.price_weight,
        )
        if any(weight < 0 for weight in weights):
            raise ValueError("Attention-score weights cannot be negative.")
        if round(sum(weights), 10) != 1.0:
            raise ValueError("Attention-score weights must add up to 1.0.")
        if any(
            cap <= 0
            for cap in (
                self.google_trends_cap_pct,
                self.volume_cap_pct,
                self.price_cap_pct,
            )
        ):
            raise ValueError("Attention-score growth caps must be greater than zero.")
        if self.growth_period_days <= 0:
            raise ValueError("growth_period_days must be greater than zero.")


def calculate_attention_scores(
    growth_metrics: pd.DataFrame,
    config: AttentionScoreConfig = AttentionScoreConfig(),
) -> pd.DataFrame:
    """Calculate and rank Version 1 0–100 attention scores.

    The input normally comes from ``calculate_growth_metrics``. The selected
    growth period defaults to seven days and is configurable through
    ``AttentionScoreConfig``.

    Missing signals receive zero points. This deliberately avoids inflating a
    company's score when Google Trends or another source is unavailable.
    """
    period = config.growth_period_days
    required_columns = {
        "ticker",
        f"google_trends_{period}d_growth_pct",
        f"volume_{period}d_growth_pct",
        f"price_{period}d_growth_pct",
    }
    missing = required_columns - set(growth_metrics.columns)
    if missing:
        raise ValueError(
            "growth_metrics is missing required column(s): "
            + ", ".join(sorted(missing))
        )

    scored = growth_metrics.copy()
    trends_column = f"google_trends_{period}d_growth_pct"
    volume_column = f"volume_{period}d_growth_pct"
    price_column = f"price_{period}d_growth_pct"

    # A negative change has no attention contribution. Positive change is
    # scaled to 0–100 and capped so one extreme outlier cannot dominate.
    scored["google_trends_points"] = _normalize_growth(
        scored[trends_column], config.google_trends_cap_pct
    )
    scored["volume_points"] = _normalize_growth(
        scored[volume_column], config.volume_cap_pct
    )
    scored["price_points"] = _normalize_growth(
        scored[price_column], config.price_cap_pct
    )

    # Canonical, period-independent column names so storage and the dashboard
    # never depend on the configured growth-period suffix.
    scored["trends_growth_pct"] = scored[trends_column]
    scored["volume_growth_pct"] = scored[volume_column]
    scored["price_growth_pct"] = scored[price_column]

    scored["attention_score"] = (
        scored["google_trends_points"] * config.google_trends_weight
        + scored["volume_points"] * config.volume_weight
        + scored["price_points"] * config.price_weight
    ).round(2)

    scored = scored.sort_values(
        ["attention_score", "ticker"], ascending=[False, True]
    ).reset_index(drop=True)
    scored.index = scored.index + 1
    scored.index.name = "rank"
    return scored


def _normalize_growth(growth: pd.Series, cap_pct: float) -> pd.Series:
    """Turn percentage growth into a capped 0–100 component score."""
    return (growth.fillna(0).clip(lower=0, upper=cap_pct) / cap_pct * 100).round(2)
