"""Data models for the Earnings Intelligence Platform."""

from dataclasses import dataclass
from datetime import date


@dataclass
class Company:
    """A company with an upcoming earnings report."""

    ticker: str
    name: str
    earnings_date: date
    sector: str = ""

    @property
    def days_until_earnings(self) -> int:
        return (self.earnings_date - date.today()).days
