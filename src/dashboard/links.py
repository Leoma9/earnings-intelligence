"""External URLs for ticker symbols shown on the dashboard."""


def yahoo_ticker_url(ticker: str) -> str:
    """Return the Yahoo Finance quote page for a ticker."""
    return f"https://finance.yahoo.com/quote/{ticker.strip().upper()}"


def stocktwits_ticker_url(ticker: str) -> str:
    """Return the StockTwits symbol page for a ticker."""
    return f"https://stocktwits.com/symbol/{ticker.strip().upper()}"
