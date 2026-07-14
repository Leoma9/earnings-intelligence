"""Run the Earnings Intelligence data pipeline once or every day.

Examples:
    python scripts/scheduler.py --once
    python scripts/scheduler.py --daily-at 06:30
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_SCRIPT = PROJECT_ROOT / "scripts" / "refresh_data.py"
LOG_FILE = PROJECT_ROOT / "logs" / "daily_pipeline.log"


def configure_logging() -> None:
    """Write pipeline progress to both the terminal and a rotating daily log."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE)],
    )


def run_pipeline() -> bool:
    """Run the refresh pipeline once and return whether it completed successfully."""
    logging.info("Starting daily Earnings Intelligence refresh.")
    result = subprocess.run(
        [sys.executable, str(PIPELINE_SCRIPT)],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode == 0:
        logging.info("Daily refresh completed successfully.")
        return True

    logging.error("Daily refresh failed with exit code %s.", result.returncode)
    return False


def next_run_at(schedule_time: str) -> datetime:
    """Return the next local datetime matching a HH:MM daily schedule."""
    try:
        hour, minute = (int(value) for value in schedule_time.split(":"))
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError
    except ValueError as exc:
        raise ValueError("--daily-at must use 24-hour HH:MM format, e.g. 06:30.") from exc

    now = datetime.now().astimezone()
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def run_daily(schedule_time: str) -> None:
    """Keep this process running and execute the pipeline once per day."""
    while True:
        scheduled_run = next_run_at(schedule_time)
        wait_seconds = (scheduled_run - datetime.now().astimezone()).total_seconds()
        logging.info("Next refresh scheduled for %s.", scheduled_run.strftime("%Y-%m-%d %H:%M %Z"))

        # Wake at least once per minute so Ctrl+C can stop the scheduler quickly.
        while wait_seconds > 0:
            time.sleep(min(wait_seconds, 60))
            wait_seconds = (scheduled_run - datetime.now().astimezone()).total_seconds()

        run_pipeline()


def parse_args() -> argparse.Namespace:
    """Parse scheduler command-line options."""
    parser = argparse.ArgumentParser(description="Schedule the data refresh pipeline.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--once", action="store_true", help="Run the pipeline now, then exit."
    )
    mode.add_argument(
        "--daily-at",
        metavar="HH:MM",
        help="Run every day at this local 24-hour time, e.g. 06:30.",
    )
    return parser.parse_args()


def main() -> None:
    """Start the requested scheduling mode."""
    configure_logging()
    args = parse_args()

    try:
        if args.once:
            raise SystemExit(0 if run_pipeline() else 1)
        run_daily(args.daily_at)
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user.")


if __name__ == "__main__":
    main()
