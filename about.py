"""About / methodology page for MarketsLite."""

import streamlit as st

from src.dashboard.data import format_last_data_refresh, get_last_data_refresh_at

st.set_page_config(
    page_title="About | MarketsLite",
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
        [data-testid="stMainBlockContainer"],
        [data-testid="stMain"],
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"],
        section.main,
        .block-container,
        .stApp > header,
        .stApp > div {
            border-radius: 0 !important;
        }
        [data-testid="stMainBlockContainer"] {
            padding-bottom: 5rem;
        }
        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 1.35rem !important;
                padding-right: 1.35rem !important;
                padding-bottom: 6rem !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("How MarketsLite works")
st.caption(
    "Ranks companies by investor attention before earnings — "
    "not by predicting the print."
)
refresh_label = format_last_data_refresh(get_last_data_refresh_at())
if refresh_label:
    st.caption(refresh_label)
else:
    st.caption("Snapshot age unavailable")

st.subheader("What we track")
st.markdown(
    """
- **StockTwits mentions** — how discussion volume is changing for each ticker
- **Yahoo Finance trending** — climbs on Yahoo’s search / interest list
- **Relative trading volume** — unusual activity vs each name’s own baseline
- **Price momentum** — recent percentage move into the report
"""
)

st.subheader("How attention is scored")
st.markdown(
    """
Each signal is scaled 0–100 within today’s upcoming-earnings batch, then combined:

- **40%** StockTwits mentions gained
- **25%** Yahoo trend-rank climb
- **20%** relative volume
- **15%** price momentum

The dashboard shows relative tiers (**On the radar**, **Warming up**,
**Background**) rather than raw scores as the primary label — so ranking
stays meaningful even when the whole batch is quiet or loud.
"""
)

st.subheader("How often data updates")
st.markdown(
    "A background job refreshes the snapshot about **every three hours** and "
    "publishes it to the live dashboard. There is no in-app refresh button — "
    "Home, Company pages, and the marketing site show when the current "
    "snapshot was last written. If the stamp looks stale, the next scheduled "
    "run (or a manual **Run workflow** on GitHub Actions) publishes a new one."
)

st.subheader("Calendar colors")
st.markdown(
    "Past dates show a colored reaction bar under each ticker "
    "(bullish / mixed / bearish) from the next-session price move after the "
    "report. Upcoming dates use attention-heat bars. That reaction measure is "
    "an approximation and does not distinguish before-the-open vs after-close "
    "timing."
)

st.subheader("Contact")
st.markdown("Questions or feedback: [Leoma4559@gmail.com](mailto:Leoma4559@gmail.com)")

st.divider()
st.caption(
    "MarketsLite is for informational purposes only and is not investment advice. "
    "Attention and social interest are not fundamentals. Do your own research."
)
st.page_link("home.py", label="← Back to Home")
