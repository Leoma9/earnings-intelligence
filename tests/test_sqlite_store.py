"""Integration tests for SQLite persistence using a temporary database."""

from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from src.storage.sqlite_store import SQLiteStore


class SQLiteStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp_directory.name) / "test.db")

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_company_and_earnings_upsert_then_retrieve(self) -> None:
        earnings_date = (date.today() + timedelta(days=5)).isoformat()
        earnings = pd.DataFrame(
            {
                "ticker": ["aapl"],
                "company_name": ["Apple Inc."],
                "sector": ["Technology"],
                "earnings_date": [earnings_date],
                "estimated_eps": [2.0],
                "estimated_revenue": [100.0],
            }
        )

        self.store.upsert_earnings(earnings)
        self.store.upsert_earnings(earnings.assign(estimated_eps=2.5))
        result = self.store.get_upcoming_earnings()

        self.assertEqual(len(result), 1)
        self.assertEqual(result.loc[0, "ticker"], "AAPL")
        self.assertEqual(result.loc[0, "company_name"], "Apple Inc.")
        self.assertEqual(result.loc[0, "estimated_eps"], 2.5)

    def test_daily_metric_upserts_merge_market_and_trend_values(self) -> None:
        market = pd.DataFrame(
            {
                "ticker": ["AAPL"],
                "date": ["2026-01-02"],
                "close": [100.0],
                "volume": [1_000],
                "avg_volume_30d": [900],
                "price_change_pct": [1.0],
            }
        )
        trends = pd.DataFrame(
            {
                "ticker": ["AAPL"],
                "date": ["2026-01-02"],
                "trend_score": [55],
            }
        )

        self.store.upsert_daily_metrics(market)
        self.store.upsert_daily_metrics(trends)
        result = self.store.get_daily_metrics("aapl")

        self.assertEqual(len(result), 1)
        self.assertEqual(result.loc[0, "close"], 100.0)
        self.assertEqual(result.loc[0, "trend_score"], 55)

    def test_attention_scores_return_ranked_company_data(self) -> None:
        earnings = pd.DataFrame(
            {
                "ticker": ["AAPL", "MSFT"],
                "company_name": ["Apple", "Microsoft"],
                "earnings_date": [
                    (date.today() + timedelta(days=5)).isoformat(),
                    (date.today() + timedelta(days=8)).isoformat(),
                ],
                "estimated_eps": [2.0, 3.0],
                "estimated_revenue": [100.0, 200.0],
            }
        )
        scores = pd.DataFrame(
            {
                "ticker": ["AAPL", "MSFT"],
                "attention_score": [68.0, 5.0],
                "trends_growth_pct": [100.0, 0.0],
                "volume_growth_pct": [20.0, 10.0],
                "price_growth_pct": [5.0, 1.0],
                "google_trends_points": [100.0, 0.0],
                "volume_points": [20.0, 10.0],
                "price_points": [16.7, 3.3],
            }
        )

        self.store.upsert_earnings(earnings)
        self.store.upsert_attention_scores(scores, calculation_date=date.today().isoformat())
        result = self.store.get_rankings()

        self.assertEqual(result["ticker"].tolist(), ["AAPL", "MSFT"])
        self.assertEqual(result.iloc[0]["attention_score"], 68.0)
        self.assertEqual(result.iloc[0]["trends_growth_pct"], 100.0)

    def test_stored_scores_match_scoring_module_output(self) -> None:
        """Guard against the pipeline/dashboard scoring split regressing."""
        from src.analytics.scoring import calculate_attention_scores

        growth = pd.DataFrame(
            {
                "ticker": ["AAPL", "MSFT"],
                "google_trends_7d_growth_pct": [100.0, 20.0],
                "volume_7d_growth_pct": [50.0, 80.0],
                "price_7d_growth_pct": [30.0, 5.0],
            }
        )
        scored = calculate_attention_scores(growth)

        self.store.upsert_attention_scores(
            scored, calculation_date=date.today().isoformat()
        )
        stored = self.store.get_rankings().set_index("ticker")["attention_score"]
        expected = scored.set_index("ticker")["attention_score"]

        for ticker in expected.index:
            self.assertAlmostEqual(stored[ticker], expected[ticker], places=2)


if __name__ == "__main__":
    unittest.main()
