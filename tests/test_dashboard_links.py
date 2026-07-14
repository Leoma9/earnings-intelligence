"""Unit tests for dashboard ticker link helpers."""

import unittest

from src.dashboard.links import stocktwits_ticker_url, yahoo_ticker_url


class DashboardLinkTests(unittest.TestCase):
    def test_yahoo_ticker_url_points_to_quote_page(self) -> None:
        self.assertEqual(
            yahoo_ticker_url("ibm"),
            "https://finance.yahoo.com/quote/IBM",
        )

    def test_stocktwits_ticker_url_points_to_symbol_page(self) -> None:
        self.assertEqual(
            stocktwits_ticker_url("ibm"),
            "https://stocktwits.com/symbol/IBM",
        )


if __name__ == "__main__":
    unittest.main()
