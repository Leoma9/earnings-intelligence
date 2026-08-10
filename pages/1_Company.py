"""Company research page for the Earnings Intelligence dashboard."""

import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.data import (
    format_last_data_refresh,
    format_market_cap,
    format_share_volume,
    get_company_data,
    get_last_data_refresh_at,
    get_researchable_tickers,
    score_component_rows,
)

_COMPANY_PAGE = "pages/1_Company.py"


def _chart_layout(y_title: str) -> dict:
    """Provide consistent dark financial-chart styling."""
    return {
        "height": 320,
        "margin": dict(l=10, r=10, t=25, b=10),
        "paper_bgcolor": "#121c31",
        "plot_bgcolor": "#121c31",
        "font": {"color": "#dbeafe"},
        # A fixed date tickformat (rather than Plotly's auto-detected format)
        # avoids nonsensical sub-second tick labels when a ticker only has a
        # single day of history so far (e.g. right after adding a new signal).
        "xaxis": {"showgrid": False, "title": "", "type": "date", "tickformat": "%b %d"},
        "yaxis": {"gridcolor": "#23304d", "title": y_title},
        "showlegend": False,
    }


def _format_value(value: object, pattern: str) -> str:
    """Format an optional numeric earnings estimate for display."""
    return pattern % value if value is not None and pd.notna(value) else "—"


st.set_page_config(
    page_title="Company Research | MarketsLite",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        :root, html, body, .stApp, [data-testid="stAppViewContainer"] {
            --st-base-radius: 0 !important;
            --st-button-radius: 0 !important;
            background-color: #0b1120 !important;
            border-radius: 0 !important;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"],
        [data-testid="stMain"],
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"],
        section.main,
        .block-container,
        .stAppViewContainer,
        .stApp > header,
        .stApp > div,
        [data-testid="stMetric"],
        [data-testid="stMetric"] > div,
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            border-radius: 0 !important;
        }
        .stApp { background: #0b1120; }
        [data-testid="stMetric"] {
            background: #121c31; border: 1px solid #23304d; border-radius: 0;
            padding: 14px;
            min-height: 108px;
        }
        [data-testid="stMetricValue"] {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: unset !important;
            line-height: 1.25 !important;
            font-size: 1.15rem !important;
            word-break: break-word;
        }
        [data-testid="stMetricLabel"] { color: #9fb0cc; }
        h1, h2, h3 { color: #f3f7ff; }
        .peer-link { color: #93c5fd; text-decoration: none; font-weight: 600; }
        .peer-link:hover { text-decoration: underline; }
        .why-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0.4rem 0 0.8rem; }
        .why-chip {
            background: #121c31;
            border: 1px solid #23304d;
            color: #cbd5e1;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 0.88rem;
            font-weight: 600;
        }
        .why-chip.active { border-color: #4f8cff; color: #f3f7ff; }
        .attention-card {
            background: #121c31;
            border: 1px solid #23304d;
            border-radius: 0;
            padding: 14px;
            min-height: 108px;
        }
        .attention-card-label {
            color: #9fb0cc;
            font-size: 0.85rem;
            margin-bottom: 6px;
        }
        .attention-card-value {
            color: #f3f7ff;
            font-size: 1.15rem;
            font-weight: 700;
            line-height: 1.3;
            word-break: break-word;
        }
        .score-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 0.35rem 0 0.85rem;
        }
        .score-cell {
            background: #121c31;
            border: 1px solid #23304d;
            border-radius: 0;
            padding: 12px 10px;
        }
        .score-cell-label {
            color: #9fb0cc;
            font-size: 0.78rem;
            margin-bottom: 4px;
        }
        .score-cell-value {
            color: #f3f7ff;
            font-size: 1.2rem;
            font-weight: 700;
        }
        .score-cell-detail {
            color: #64748b;
            font-size: 0.75rem;
            margin-top: 2px;
        }
        @media (max-width: 720px) {
            .score-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            [data-testid="stMainBlockContainer"] {
                padding-left: 1.35rem !important;
                padding-right: 1.35rem !important;
                padding-bottom: 6rem !important;
            }
        }
        [data-testid="stMainBlockContainer"] {
            padding-bottom: 5rem;
        }
        [data-testid="stPageLink"] a,
        [data-testid="stPageLink-NavLink"] {
            color: #93c5fd !important;
            font-weight: 700 !important;
            text-decoration: none !important;
        }
        [data-testid="stPageLink"] a:hover {
            text-decoration: underline !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def get_company_list() -> list[str]:
    """Return researchable tickers from the current database snapshot."""
    return get_researchable_tickers()


@st.cache_data(ttl=60)
def load_company(ticker: str) -> dict[str, object]:
    """Cache individual company queries during a browsing session."""
    return get_company_data(ticker)


tickers = get_company_list()
if not tickers:
    st.page_link("home.py", label="← Back to home")
    st.info(
        "No companies in this snapshot yet. Check back after the next data refresh."
    )
    st.stop()

query_ticker = str(st.query_params.get("ticker", "")).upper().strip()
invalid_query = bool(query_ticker) and query_ticker not in tickers
default_index = tickers.index(query_ticker) if query_ticker in tickers else 0
selected_ticker = st.selectbox("Search a ticker", tickers, index=default_index)
if st.query_params.get("ticker") != selected_ticker:
    st.query_params["ticker"] = selected_ticker

company = load_company(selected_ticker)
metrics = company["metrics"].copy()
earnings = company["earnings"]
score = company.get("score") or {}
peers = company.get("peers") or []
why_chips = company.get("why_chips") or ["Quiet this week"]
headline = company.get("attention_headline") or "Background"
components = score_component_rows(score)

st.page_link("home.py", label="← Back to home")

if invalid_query:
    st.info(
        f"**{query_ticker}** isn’t in this snapshot. Showing **{selected_ticker}** — "
        "pick another ticker below, or check back after the next refresh."
    )

if metrics.empty:
    st.info(
        f"No price history for **{selected_ticker}** yet — "
        "it may be new to the watchlist."
    )
    st.stop()

metrics["date"] = pd.to_datetime(metrics["date"])
metrics = metrics.sort_values("date")
latest = metrics.iloc[-1]

st.title(f"{selected_ticker} Research")
st.caption(
    f"{earnings.get('company_name', selected_ticker)}"
    + (f" · {earnings['sector']}" if earnings.get("sector") else "")
)
refresh_label = format_last_data_refresh(get_last_data_refresh_at())
if refresh_label:
    st.caption(refresh_label)
else:
    st.caption("Snapshot age unavailable")

summary, attention_col, earnings_col, volume_col = st.columns(4)
summary.metric(
    "Last close", f"${latest['close']:,.2f}" if pd.notna(latest["close"]) else "—"
)
attention_col.markdown(
    f'<div class="attention-card">'
    f'<div class="attention-card-label">Attention</div>'
    f'<div class="attention-card-value">{html.escape(str(headline))}</div>'
    f"</div>",
    unsafe_allow_html=True,
)
earnings_col.metric("Earnings date", earnings.get("earnings_date", "—"))
volume_col.metric(
    "Latest volume",
    format_share_volume(latest["volume"]) if pd.notna(latest["volume"]) else "—",
)

st.markdown("**Why it’s getting attention**")
st.caption("What moved over the last 7 days — not the earnings outcome.")
chip_html = "".join(
    f'<span class="why-chip{" active" if chip != "Quiet this week" else ""}">'
    f"{html.escape(str(chip))}</span>"
    for chip in why_chips
)
st.markdown(f'<div class="why-chips">{chip_html}</div>', unsafe_allow_html=True)

st.markdown("**Attention mix (0–100 points)**")
st.caption(
    "Each signal is scaled inside today’s upcoming-earnings batch, then weighted."
)
if not any(item["points"] is not None for item in components):
    st.info("No scored components for this ticker in the latest snapshot yet.")
else:
    cells = []
    for item in components:
        points = item["points"]
        value = f"{points:.0f}" if points is not None else "—"
        cells.append(
            f'<div class="score-cell">'
            f'<div class="score-cell-label">{html.escape(str(item["label"]))}</div>'
            f'<div class="score-cell-value">{html.escape(value)}</div>'
            f'<div class="score-cell-detail">{html.escape(str(item["detail"]))}</div>'
            f"</div>"
        )
    st.markdown(f'<div class="score-grid">{"".join(cells)}</div>', unsafe_allow_html=True)

st.divider()
chart_col, detail_col = st.columns([1.6, 1])

with chart_col:
    st.subheader("Price history")
    price = go.Figure(
        go.Scatter(
            x=metrics["date"],
            y=metrics["close"],
            mode="lines",
            line=dict(color="#60a5fa", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(96, 165, 250, 0.08)",
            hovertemplate="$%{y:,.2f}<extra></extra>",
        )
    )
    price.update_layout(**_chart_layout("Close price (USD)"))
    st.plotly_chart(price, use_container_width=True, config={"displayModeBar": False})

with detail_col:
    st.subheader("Report snapshot")
    st.metric("Est. EPS", _format_value(earnings.get("estimated_eps"), "$%.2f"))
    st.metric("Est. revenue", format_market_cap(earnings.get("estimated_revenue")))
    st.caption(
        "Weights: 40% mentions · 25% Yahoo · 20% volume · 15% price. "
        "See About for the full methodology."
    )

st.subheader("Same-sector peers")
if not peers:
    st.info("No same-sector peers with attention scores in this snapshot yet.")
else:
    peer_cols = st.columns(min(len(peers), 5))
    for col, peer in zip(peer_cols, peers):
        with col:
            st.page_link(
                _COMPANY_PAGE,
                label=str(peer["ticker"]),
                query_params={"ticker": str(peer["ticker"]).upper()},
            )

st.subheader("StockTwits mention history")
mention_history = metrics.dropna(subset=["social_mentions"])
if mention_history.empty:
    st.info("No StockTwits mention history for this ticker yet.")
else:
    mentions = go.Figure(
        go.Scatter(
            x=mention_history["date"],
            y=mention_history["social_mentions"],
            mode="lines",
            line=dict(color="#6ee7b7", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(110, 231, 183, 0.08)",
            hovertemplate="StockTwits mentions: %{y}<extra></extra>",
        )
    )
    mentions.update_layout(**_chart_layout("StockTwits mentions per day"))
    st.plotly_chart(mentions, use_container_width=True, config={"displayModeBar": False})
