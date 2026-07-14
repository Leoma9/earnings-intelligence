"""Deterministic unit tests for growth calculations."""

import unittest

import pandas as pd

from src.analytics.growth_ranking import (
    calculate_growth_metrics,
    rank_companies_by_growth,
)


class AnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=31, freq="D").tolist() * 2,
                "ticker": ["AAPL"] * 31 + ["MSFT"] * 31,
                "social_mentions": list(range(10, 41)) + list(range(40, 9, -1)),
                "volume": [100] * 30 + [200] + [100] * 31,
                "close": [100] * 30 + [110] + [100] * 31,
                "avg_volume_30d": [100] * 62,
            }
        )

    def test_growth_metrics_calculate_expected_period_changes(self) -> None:
        growth = calculate_growth_metrics(self.metrics)
        apple = growth[growth["ticker"] == "AAPL"].iloc[0]

        self.assertEqual(apple["social_30d_growth_pct"], 300.0)
        self.assertEqual(apple["volume_1d_growth_pct"], 100.0)
        self.assertEqual(apple["price_1d_growth_pct"], 10.0)

    def test_growth_ranking_orders_larger_momentum_first(self) -> None:
        rankings = rank_companies_by_growth(self.metrics)

        self.assertEqual(rankings.index.name, "rank")
        self.assertEqual(rankings.iloc[0]["ticker"], "AAPL")


if __name__ == "__main__":
    unittest.main()
