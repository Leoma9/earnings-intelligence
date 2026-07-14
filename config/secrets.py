"""Read configuration from Streamlit secrets or environment variables.

On Streamlit Community Cloud, secrets are configured in the app's dashboard
and exposed via ``st.secrets``. Locally, the same names can be set in
``.streamlit/secrets.toml`` or as plain environment variables — useful for
scripts (``scripts/refresh_data.py``, ``scripts/scheduler.py``) that run
outside a Streamlit session where ``st.secrets`` is unavailable.
"""

from __future__ import annotations

import os


def get_setting(key: str, default: str | None = None) -> str | None:
    """Look up ``key`` in Streamlit secrets first, then environment variables."""
    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # No secrets.toml, not running inside Streamlit, or key not set.
        pass

    return os.environ.get(key, default)
