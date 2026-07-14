# Earnings Intelligence Platform

A web application that identifies companies with upcoming earnings reports experiencing unusual increases in investor attention.

## Quick Start

**New to coding?** Follow the step-by-step guide in **[SETUP.md](SETUP.md)**.
For daily automation, see **[AUTOMATION.md](AUTOMATION.md)**.
To publish this as a free public website, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

```bash
cd ~/Projects/earnings-intelligence
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/refresh_data.py
streamlit run app.py
```

## How It Works

1. **Earnings Calendar** — Finds companies reporting earnings in the next 30 days
2. **Market Data** — Collects daily price and volume from Yahoo Finance
3. **Google Trends** — Tracks search interest for each ticker
4. **Attention Growth** — Compares recent vs prior interest and volume
5. **Ranking** — Scores and ranks companies by composite attention signal
6. **Dashboard** — Displays results in an interactive Streamlit UI

## Project Structure

```
earnings-intelligence/
├── app.py                          # Streamlit dashboard (main entry point)
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── .gitignore                      # Git ignore rules
│
├── config/
│   └── settings.py                 # Paths, constants, and file locations
│
├── data/
│   └── earnings_intelligence.db    # SQLite database (generated locally)
│
├── src/
│   ├── collectors/                 # Data fetching modules
│   │   ├── earnings_calendar.py  # Upcoming earnings from Yahoo Finance
│   │   ├── market_data.py        # Stock price and volume data
│   │   └── google_trends.py      # Google Trends search interest
│   │
│   ├── storage/                    # Persistence layer
│   │   └── sqlite_store.py          # Schema, upserts, and history queries
│   │
│   ├── analytics/                  # Analysis and scoring
│   │   ├── growth_ranking.py       # Multi-period growth metrics
│   │   └── scoring.py              # Canonical 0–100 attention score
│   │
│   └── models/                     # Data models
│       └── company.py              # Company dataclass
│
└── scripts/
    └── refresh_data.py             # End-to-end data pipeline script
```

## File Reference

| File | Purpose |
|------|---------|
| `app.py` | Streamlit frontend — loads rankings and renders the dashboard with summary metrics, ranked table, and per-company charts |
| `requirements.txt` | Pinned Python package dependencies |
| `config/settings.py` | Central configuration: directory paths, database location, and analysis parameters |
| `src/collectors/earnings_calendar.py` | Queries Yahoo Finance for companies with earnings in the next 30 days |
| `src/collectors/market_data.py` | Downloads daily OHLCV data and computes volume averages |
| `src/collectors/google_trends.py` | Fetches Google Trends interest scores via pytrends |
| `src/storage/sqlite_store.py` | Creates SQLite tables and provides insert/query functions for all platform data |
| `src/analytics/growth_ranking.py` | Calculates 1/3/7/30-day growth for search interest, volume, and price |
| `src/analytics/scoring.py` | Canonical 0–100 attention score (single source of truth) |
| `src/models/company.py` | `Company` dataclass representing a tracked company |
| `scripts/refresh_data.py` | Orchestrates the full pipeline: collect → store → score → rank |
| `data/earnings_intelligence.db` | Local SQLite database holding companies, earnings, daily metrics, and attention-score history |

## Scoring

The attention score is a single 0–100 value defined in `src/analytics/scoring.py`.
Each 7-day growth signal is scaled to 0–100 (negative growth scores 0) and
combined with these weights:

- **50%** — Google Trends search-interest growth
- **30%** — Trading-volume growth
- **20%** — Price momentum

`scripts/refresh_data.py` computes and stores this score; the dashboard reads
the stored values, so automation and the UI always agree. Weights and caps are
adjustable via `AttentionScoreConfig`.

## V1 Limitations

- SQLite storage is local-only; it is not intended for concurrent or hosted multi-user access
- Fixed watchlist of ~30 large-cap tickers
- Google Trends rate-limited to 5 tickers per request
- Scheduling is optional and runs locally (see [AUTOMATION.md](AUTOMATION.md))

## License

MIT
