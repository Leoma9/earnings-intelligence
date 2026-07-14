"""CSV-based data persistence layer."""

from pathlib import Path

import pandas as pd


class CSVStore:
    """Read and write DataFrames to CSV files."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, df: pd.DataFrame, filename: str) -> Path:
        path = self.base_dir / filename
        df.to_csv(path, index=False)
        return path

    def load(self, filename: str) -> pd.DataFrame:
        path = self.base_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            return pd.DataFrame()
        try:
            return pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()

    def append(self, df: pd.DataFrame, filename: str, dedup_cols: list[str] | None = None) -> Path:
        """Append new rows, optionally deduplicating on key columns."""
        existing = self.load(filename)
        combined = pd.concat([existing, df], ignore_index=True)

        if dedup_cols and not combined.empty:
            combined = combined.drop_duplicates(subset=dedup_cols, keep="last")

        return self.save(combined, filename)

    def exists(self, filename: str) -> bool:
        return (self.base_dir / filename).exists()
