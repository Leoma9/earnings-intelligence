"""Earnings Intelligence Platform — Streamlit homepage."""

import html
from datetime import date

import pandas as pd
import streamlit as st

from src.dashboard.data import (
    CALENDAR_TICKERS_PER_DAY,
    attention_tier_label,
    build_anticipated_earnings_calendar,
    build_earnings_spillover,
    build_this_week_focus,
    build_weekly_postmortem,
    format_last_data_refresh,
    get_last_data_refresh_at,
    load_dashboard_data,
)

_COMPANY_PAGE = "pages/1_Company.py"


st.set_page_config(
    page_title="MarketsLite",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background-color: #0b1120 !important;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"] {
            padding-top: 2rem;
        }
        .stApp { background: #0b1120; }
        [data-testid="stMetric"] {
            background: #121c31; border: 1px solid #23304d; border-radius: 10px;
            padding: 14px;
        }
        [data-testid="stMetricLabel"] { color: #9fb0cc; }
        [data-testid="stMetricValue"] { color: #f3f7ff; }
        h1, h2, h3 { color: #f3f7ff; }
        .trending-column-title {
            color: #f3f7ff;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.5;
            margin: 0 0 0.5rem 0;
            min-height: 1.5rem;
        }
        .earnings-cal-signal {
            height: 3px;
            border-radius: 999px;
            margin: 1px 0 8px 0;
            max-width: 3.2rem;
        }
        .earnings-cal-signal.sent-bullish { background: #6ee7b7; }
        .earnings-cal-signal.sent-mixed { background: #fbbf24; }
        .earnings-cal-signal.sent-bearish { background: #f87171; }
        .earnings-cal-signal.sent-unknown { background: #64748b; }
        .earnings-cal-signal.heat-high {
            background: #6ee7b7;
            box-shadow: 0 0 8px rgba(110, 231, 183, 0.45);
        }
        .earnings-cal-signal.heat-mid { background: #93c5fd; }
        .earnings-cal-signal.heat-low,
        .earnings-cal-signal.heat-none { background: #475569; }
        .earnings-cal-legend {
            color: #9fb0cc;
            font-size: 0.82rem;
            margin: 0.55rem 0 0.15rem 0;
            line-height: 1.45;
        }
        .mobile-cal-hint {
            display: none;
            color: #9fb0cc;
            font-size: 0.85rem;
            margin: 0.4rem 0 0.2rem 0;
        }
        .this-week-list { margin: 0.35rem 0 0.6rem 0; }
        .this-week-row {
            display: flex;
            gap: 10px;
            align-items: baseline;
            flex-wrap: wrap;
            padding: 8px 10px;
            border-bottom: 1px solid #23304d;
        }
        .this-week-date { color: #9fb0cc; font-size: 0.82rem; min-width: 4.5rem; }
        .this-week-ticker {
            color: #f3f7ff;
            font-weight: 700;
            font-size: 1rem;
            text-decoration: none;
        }
        .this-week-ticker:hover { color: #93c5fd; }
        .this-week-meta { color: #9fb0cc; font-size: 0.85rem; }
        .this-week-heat-high { color: #6ee7b7; }
        .this-week-heat-mid { color: #93c5fd; }
        .this-week-heat-low, .this-week-heat-none { color: #94a3b8; }
        .why-chip-inline {
            color: #9fb0cc;
            font-size: 0.82rem;
        }
        .ranked-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            margin: 0.15rem 0 0.6rem 0;
        }
        .ranked-table th {
            color: #9fb0cc;
            font-weight: 600;
            text-align: left;
            padding: 8px 10px;
            border-bottom: 1px solid #23304d;
        }
        .ranked-table td {
            color: #cbd5e1;
            padding: 8px 10px;
            border-bottom: 1px solid #1a243a;
        }
        .ranked-table a {
            color: #f3f7ff;
            font-weight: 700;
            text-decoration: none;
        }
        .ranked-table a:hover { color: #93c5fd; }
        .postmortem-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin: 0.4rem 0 0.8rem 0;
        }
        .postmortem-col {
            background: #121c31;
            border: 1px solid #23304d;
            border-radius: 10px;
            padding: 12px 14px;
        }
        .postmortem-heading {
            font-weight: 700;
            margin-bottom: 8px;
        }
        .postmortem-heading.beat { color: #6ee7b7; }
        .postmortem-heading.miss { color: #f87171; }
        .postmortem-row {
            display: flex;
            justify-content: space-between;
            gap: 8px;
            padding: 4px 0;
            font-size: 0.92rem;
        }
        .postmortem-row a {
            color: #f3f7ff;
            font-weight: 700;
            text-decoration: none;
        }
        .postmortem-row a:hover { color: #93c5fd; }
        .postmortem-beat {
            color: #6ee7b7 !important;
            font-weight: 700;
            font-size: 1.02rem;
        }
        .postmortem-miss {
            color: #f87171 !important;
            font-weight: 700;
            font-size: 1.02rem;
        }
        .postmortem-ticker-beat,
        .postmortem-ticker-miss {
            font-weight: 700;
            font-size: 1.02rem;
            margin: 0 0 0.1rem 0;
        }
        .postmortem-ticker-beat { color: #6ee7b7; }
        .postmortem-ticker-miss { color: #f87171; }
        .spillover-card {
            background: #121c31;
            border: 1px solid #23304d;
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 8px;
        }
        .spillover-title {
            color: #f3f7ff;
            font-weight: 700;
            font-size: 0.95rem;
        }
        .spillover-title a {
            color: inherit;
            text-decoration: none;
        }
        .spillover-title a:hover { color: #93c5fd; }
        .spillover-meta { color: #9fb0cc; font-size: 0.82rem; margin-top: 2px; }
        .spillover-peers { color: #cbd5e1; font-size: 0.88rem; margin-top: 6px; }
        .spillover-peers a {
            color: #93c5fd;
            text-decoration: none;
            font-weight: 600;
        }
        .spillover-peers a:hover { text-decoration: underline; }
        .spillover-status-bullish { color: #6ee7b7; }
        .spillover-status-bearish { color: #f87171; }
        .spillover-status-mixed { color: #fbbf24; }
        .spillover-status-upcoming { color: #93c5fd; }
        .spillover-status-unknown { color: #94a3b8; }
        /* Native page_link tickers — keep the blue ticker look */
        [data-testid="stPageLink"] a,
        [data-testid="stPageLink-NavLink"] {
            color: #93c5fd !important;
            font-weight: 700 !important;
            text-decoration: none !important;
        }
        [data-testid="stPageLink"] a:hover {
            text-decoration: underline !important;
        }
        @media (max-width: 768px) {
            .earnings-cal-legend { display: none !important; }
            .mobile-cal-hint { display: block; }
            .postmortem-grid { grid-template-columns: 1fr; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def get_data() -> dict[str, pd.DataFrame]:
    """Cache database reads briefly to keep dashboard interactions fast."""
    return load_dashboard_data()


def _company_page_link(ticker: str, *, label: str | None = None) -> None:
    """Navigate to Companies with a ticker using Streamlit's own router."""
    st.page_link(
        _COMPANY_PAGE,
        label=label if label is not None else str(ticker).upper(),
        query_params={"ticker": str(ticker).upper()},
    )


def _render_ranked_table(
    data: pd.DataFrame,
    value_column: str,
    value_label: str,
    value_format: str,
    *,
    show_value: bool = True,
) -> None:
    """Render a numbered top-10 table shared by Yahoo and StockTwits sections."""
    display = data.head(10).copy()
    header_cols = st.columns([0.4, 0.9, 2.2, 1.1, 1.2] if show_value else [0.4, 0.9, 2.4, 1.3])
    headers = ["#", "Ticker", "Company", "Earnings"]
    if show_value:
        headers.append(value_label)
    for col, title in zip(header_cols, headers):
        col.caption(title)

    for index, row in enumerate(display.itertuples(index=False), start=1):
        cols = st.columns([0.4, 0.9, 2.2, 1.1, 1.2] if show_value else [0.4, 0.9, 2.4, 1.3])
        cols[0].write(str(index))
        with cols[1]:
            _company_page_link(str(row.ticker))
        cols[2].write(str(getattr(row, "company_name", row.ticker)))
        cols[3].write(str(getattr(row, "earnings_date", "—")))
        if show_value:
            raw = getattr(row, value_column, None)
            if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                formatted = "—"
            else:
                try:
                    formatted = value_format % float(raw)
                except (TypeError, ValueError):
                    formatted = str(raw)
            cols[4].write(formatted)


def _render_this_week(focus: list[dict[str, object]]) -> None:
    """Render the mobile-first This week’s prints list."""
    if not focus:
        st.info("No tracked prints in the next 7 days.")
        return
    for item in focus:
        heat = str(item.get("heat") or "none")
        headline = item.get("attention_headline") or attention_tier_label(
            item.get("attention_tier")
        )
        chips = item.get("why_chips") or []
        chip_text = " · ".join(str(chip) for chip in chips[:2])
        event_date = item["earnings_date"]
        date_text = (
            event_date.strftime("%b %d")
            if hasattr(event_date, "strftime")
            else str(event_date)
        )
        date_col, ticker_col, meta_col = st.columns([0.9, 0.9, 3.2])
        date_col.markdown(
            f'<span class="this-week-date">{html.escape(date_text)}</span>',
            unsafe_allow_html=True,
        )
        with ticker_col:
            _company_page_link(str(item["ticker"]))
        meta_col.markdown(
            f'<span class="this-week-meta this-week-heat-{html.escape(heat)}">'
            f"{html.escape(str(headline))}</span>"
            f'<span class="why-chip-inline">{html.escape(chip_text)}</span>',
            unsafe_allow_html=True,
        )


def _render_weekly_postmortem(postmortem: dict[str, list[dict[str, object]]]) -> None:
    """Render biggest post-report beats and misses from the last week."""
    beats = postmortem.get("beats") or []
    misses = postmortem.get("misses") or []
    if not beats and not misses:
        st.info("No post-report price reactions in the last 7 days yet.")
        return

    beat_col, miss_col = st.columns(2)
    with beat_col:
        st.markdown(
            '<div class="postmortem-heading beat">Biggest beats</div>',
            unsafe_allow_html=True,
        )
        if not beats:
            st.caption("None yet.")
        for item in beats:
            reaction = float(item["reaction_pct"])
            ticker = str(item["ticker"])
            name, move, link = st.columns([1.4, 1.0, 0.7])
            name.markdown(
                f'<div class="postmortem-ticker-beat">{html.escape(ticker)}</div>',
                unsafe_allow_html=True,
            )
            move.markdown(
                f'<div class="postmortem-beat">{reaction:+.1f}%</div>',
                unsafe_allow_html=True,
            )
            with link:
                _company_page_link(ticker, label="→")
    with miss_col:
        st.markdown(
            '<div class="postmortem-heading miss">Biggest misses</div>',
            unsafe_allow_html=True,
        )
        if not misses:
            st.caption("None yet.")
        for item in misses:
            reaction = float(item["reaction_pct"])
            ticker = str(item["ticker"])
            name, move, link = st.columns([1.4, 1.0, 0.7])
            name.markdown(
                f'<div class="postmortem-ticker-miss">{html.escape(ticker)}</div>',
                unsafe_allow_html=True,
            )
            move.markdown(
                f'<div class="postmortem-miss">{reaction:+.1f}%</div>',
                unsafe_allow_html=True,
            )
            with link:
                _company_page_link(ticker, label="→")
    st.caption(
        "Next-session move after the report (≥ +3% beat / ≤ −3% miss). "
        "Each ticker appears in only one column. BMO timing can understate the gap."
    )


def _render_earnings_calendar(calendar_data: dict[str, object]) -> None:
    """Render a month grid of the highest-attention earnings dates."""
    today = calendar_data["today"]
    days = calendar_data["days"]
    first_weekday = int(calendar_data["first_weekday"])
    days_in_month = int(calendar_data["days_in_month"])

    header = st.columns(7)
    for col, label in zip(header, ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
        col.caption(label)

    cells: list[tuple[int | None, list[dict[str, object]]]] = []
    for _ in range(first_weekday):
        cells.append((None, []))
    for day in range(1, days_in_month + 1):
        cells.append((day, list(days.get(day, [])[:CALENDAR_TICKERS_PER_DAY])))
    while len(cells) % 7:
        cells.append((None, []))

    for offset in range(0, len(cells), 7):
        week = cells[offset : offset + 7]
        cols = st.columns(7)
        for col, (day, tickers) in zip(cols, week):
            with col:
                if day is None:
                    st.write("")
                    continue
                day_date = date(
                    int(calendar_data["year"]), int(calendar_data["month"]), day
                )
                marker = " · today" if day_date == today else ""
                st.caption(f"{day}{marker}")
                for item in tickers:
                    label = str(item["ticker"])
                    if item.get("momentum"):
                        label = f"{label} {item['momentum']}"
                    _company_page_link(str(item["ticker"]), label=label)
                    if item.get("is_past"):
                        sentiment = str(item.get("sentiment") or "unknown")
                        reaction = item.get("reaction_pct")
                        tip = (
                            f"{float(reaction):+.1f}%"
                            if reaction is not None
                            else "n/a"
                        )
                        st.markdown(
                            f'<div class="earnings-cal-signal '
                            f'sent-{html.escape(sentiment)}" '
                            f'title="{html.escape(tip)}"></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        heat = str(item.get("heat") or "none")
                        st.markdown(
                            f'<div class="earnings-cal-signal '
                            f'heat-{html.escape(heat)}"></div>',
                            unsafe_allow_html=True,
                        )

    st.markdown(
        '<div class="earnings-cal-legend">'
        "<b>Past days:</b> colored bar = next-session reaction "
        "(green bullish / amber mixed / red bearish). "
        "<b>Upcoming:</b> bar = attention heat; ↑/↓ = pre-report momentum "
        "(not the earnings outcome)."
        "</div>"
        '<div class="mobile-cal-hint">'
        "Month calendar is easiest on desktop — use This week’s prints above."
        "</div>",
        unsafe_allow_html=True,
    )


def _render_earnings_spillover(spillover: list[dict[str, object]]) -> None:
    """Render mega-cap influencers and same-sector peers under the calendar."""
    if not spillover:
        st.caption("No mega-cap influencers on this month’s calendar yet.")
        return

    st.markdown("**Sector watch around big prints**")
    st.caption(
        "Large names on this month’s calendar and same-sector peers also on "
        "the radar — not measured co-movement."
    )
    for item in spillover:
        status = str(item.get("status") or "unknown")
        status_label = status.replace("_", " ")
        reaction = item.get("reaction_pct")
        reaction_bit = (
            f" · {reaction:+.1f}% after report" if reaction is not None else ""
        )
        peers = item.get("peers") or []
        top, _ = st.columns([2, 3])
        with top:
            _company_page_link(str(item["ticker"]))
        st.caption(
            f"({status_label}){reaction_bit} · {item.get('company_name')} · "
            f"{item.get('sector')} · {item.get('watch_note')}"
        )
        if peers:
            st.caption("Same-sector peers")
            peer_cols = st.columns(min(len(peers), 5))
            for col, peer in zip(peer_cols, peers):
                with col:
                    _company_page_link(str(peer["ticker"]))
        else:
            st.caption("No tracked same-sector peers yet")


data = get_data()
attention = data["attention"]
earnings = data["earnings"]
most_mentioned = data["most_mentioned"]
yahoo_rank_growth = data["yahoo_rank_growth"]

st.title("Most Watched Upcoming Earnings")
st.caption(
    "Companies ranked based on investor search activity and mentions "
    "ahead of earnings reports"
)
st.caption(
    "Attention mix: 40% StockTwits · 25% Yahoo trend · "
    "20% relative volume · 15% price"
)
refresh_label = format_last_data_refresh(get_last_data_refresh_at())
if refresh_label:
    st.caption(f"{refresh_label} · updates about every 3 hours")
else:
    st.caption("Snapshot age unavailable · updates about every 3 hours")

if attention.empty:
    st.info(
        "No dashboard data in this snapshot yet. "
        "Check back after the next automatic refresh."
    )
    st.stop()

next_earnings = earnings["earnings_date"].min() if not earnings.empty else "—"

metric_columns = st.columns(2)
metric_columns[0].metric("Tracked companies", f"{len(attention):,}")
metric_columns[1].metric("Next earnings", next_earnings)

st.divider()
st.subheader("This week’s prints")
st.caption("Highest-attention upcoming reports in the next 7 days.")
_render_this_week(build_this_week_focus(attention))

month_calendar = build_anticipated_earnings_calendar()
st.subheader("Last 7 days: biggest beats & misses")
_render_weekly_postmortem(build_weekly_postmortem())

st.divider()
st.subheader("Trending ahead of earnings")

yahoo_col, stocktwits_col = st.columns(2)

with yahoo_col:
    st.markdown(
        '<div class="trending-column-title">Most Searched</div>',
        unsafe_allow_html=True,
    )
    if yahoo_rank_growth.empty:
        st.info("No Yahoo rank climbers in this snapshot yet.")
    else:
        _render_ranked_table(
            yahoo_rank_growth,
            "yahoo_rank_change",
            "Ranks Climbed (7D)",
            "%+,.0f",
        )

with stocktwits_col:
    st.markdown(
        '<div class="trending-column-title">Most Mentioned</div>',
        unsafe_allow_html=True,
    )
    if most_mentioned.empty:
        st.info("No StockTwits mention counts in this snapshot yet.")
    else:
        _render_ranked_table(
            most_mentioned,
            "current_mentions",
            "Mentions",
            "%,.0f",
        )

st.divider()
st.subheader("Most anticipated earnings this month")
st.caption(
    f"{month_calendar['month_label']} · past days marked by post-report "
    "reaction color · upcoming by attention heat "
    "(On the radar / Warming up) · updates automatically each month"
)
if month_calendar["event_count"] == 0:
    st.info("No tracked earnings dates fall in this calendar month yet.")
else:
    _render_earnings_calendar(month_calendar)
    spillover = build_earnings_spillover(month_calendar, attention)
    st.subheader("Earnings spillover watch")
    _render_earnings_spillover(spillover)

st.divider()
st.caption(
    "MarketsLite is for informational purposes only and is not investment advice. "
    "Attention and social interest are not fundamentals."
)
st.page_link("about.py", label="How it works →")
