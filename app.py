"""MarketsLite Streamlit entrypoint — sidebar labels and page routing."""

import streamlit as st

# Keep url_path="Company" so existing /Company?ticker=… deep links still work.
home = st.Page("home.py", title="Home", default=True)
companies = st.Page(
    "pages/1_Company.py",
    title="Companies",
    url_path="Company",
)

st.navigation([home, companies]).run()
