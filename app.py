"""MarketsLite Streamlit entrypoint — sidebar labels and page routing."""

import streamlit as st

# Keep url_path="Company" so existing /Company?ticker=… deep links still work.
home = st.Page("home.py", title="Home", default=True)
companies = st.Page(
    "pages/1_Company.py",
    title="Companies",
    url_path="Company",
)
about = st.Page("about.py", title="About", url_path="About")

st.navigation([home, companies, about]).run()
