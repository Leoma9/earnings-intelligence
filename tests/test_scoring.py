"""Unit tests for the Version 1 attention-score algorithm."""

import unittest

import pandas as pd

from src.analytics.scoring import AttentionScoreConfig, calculate_attention_scores


class AttentionScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_growth = pd.DataFrame(
            {
                "ticker": ["FULL", "MIXED", "NEGATIVE", "MISSING"],
                "social_7d_growth_pct": [100, 50, -10, None],
                "volume_7d_growth_pct": [100, 100, -20, 100],
                "price_7d_growth_pct": [30, 0, -5, 30],
            }
        )

    def test_scores_follow_version_one_weights(self) -> None:
        scored = calculate_attention_scores(self.sample_growth)

        # FULL: 100 × 50% + 100 × 30% + 100 × 20% = 100.
        self.assertEqual(scored.loc[scored["ticker"] == "FULL", "attention_score"].iloc[0], 100)

        # MIXED: 50 × 50% + 100 × 30% + 0 × 20% = 55.
        self.assertEqual(scored.loc[scored["ticker"] == "MIXED", "attention_score"].iloc[0], 55)

        # Negative inputs do not add attention points.
        self.assertEqual(
            scored.loc[scored["ticker"] == "NEGATIVE", "attention_score"].iloc[0], 0
        )

    def test_missing_signal_receives_zero_points(self) -> None:
        scored = calculate_attention_scores(self.sample_growth)

        # MISSING: no social points + 100 × 30% + 100 × 20% = 50.
        self.assertEqual(
            scored.loc[scored["ticker"] == "MISSING", "attention_score"].iloc[0], 50
        )

    def test_scores_are_ranked_and_bounded(self) -> None:
        scored = calculate_attention_scores(self.sample_growth)

        self.assertEqual(scored.index.name, "rank")
        self.assertEqual(scored.iloc[0]["ticker"], "FULL")
        self.assertTrue(scored["attention_score"].between(0, 100).all())

    def test_weights_are_adjustable(self) -> None:
        config = AttentionScoreConfig(
            social_weight=0.0,
            volume_weight=1.0,
            price_weight=0.0,
        )
        scored = calculate_attention_scores(self.sample_growth, config)

        self.assertEqual(
            scored.loc[scored["ticker"] == "MIXED", "attention_score"].iloc[0], 100
        )

    def test_invalid_weights_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            AttentionScoreConfig(
                social_weight=0.5,
                volume_weight=0.3,
                price_weight=0.3,
            )


if __name__ == "__main__":
    unittest.main()
