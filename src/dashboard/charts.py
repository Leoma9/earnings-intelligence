"""Plotly chart helpers for the Streamlit dashboard."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable

import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components


_CHART_LAYOUT = {
    "height": 420,
    "margin": dict(l=0, r=0, t=10, b=0),
    "coloraxis_showscale": False,
    "paper_bgcolor": "#121c31",
    "plot_bgcolor": "#121c31",
    "font_color": "#dbeafe",
    "yaxis_title": "",
}


def render_linked_bar_chart(
    data: pd.DataFrame,
    x_column: str,
    x_title: str,
    ticker_url: Callable[[str], str],
    x_max: float | None = None,
) -> None:
    """Render a horizontal bar chart whose y-axis ticker labels link out."""
    chart_data = data.head(10).sort_values(x_column)
    if chart_data.empty:
        return

    if x_max is None:
        x_max = max(chart_data[x_column].max() * 1.15, 35)

    url_map = {
        str(row.ticker).upper(): ticker_url(str(row.ticker))
        for row in chart_data.itertuples(index=False)
    }

    figure = px.bar(
        chart_data,
        x=x_column,
        y="ticker",
        orientation="h",
        color=x_column,
        color_continuous_scale=["#273a66", "#4f8cff", "#6ee7b7"],
    )
    figure.update_layout(
        **_CHART_LAYOUT,
        xaxis_title=x_title,
        xaxis=dict(range=[0, x_max]),
    )

    chart_id = f"linked-chart-{uuid.uuid4().hex}"
    html_body = figure.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        div_id=chart_id,
        config={"displayModeBar": False, "responsive": True},
    )
    link_script = _tick_link_script(chart_id, url_map)
    components.html(html_body + link_script, height=440, scrolling=False)


def _tick_link_script(chart_id: str, url_map: dict[str, str]) -> str:
    """Return JS that turns y-axis ticker labels (and bars) into outbound links."""
    url_map_json = json.dumps(url_map)
    return f"""
<script>
(function() {{
  var chartId = {json.dumps(chart_id)};
  var urlMap = {url_map_json};

  function linkifyYTicks(gd) {{
    gd.querySelectorAll(".ytick text").forEach(function(textEl) {{
      if (textEl.dataset.linked === "1") return;
      var ticker = textEl.textContent.trim().toUpperCase();
      var url = urlMap[ticker];
      if (!url) return;
      var link = document.createElementNS("http://www.w3.org/2000/svg", "a");
      link.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", url);
      link.setAttribute("target", "_blank");
      link.style.cursor = "pointer";
      textEl.parentNode.insertBefore(link, textEl);
      link.appendChild(textEl);
      textEl.dataset.linked = "1";
    }});
  }}

  function attachHandlers(gd) {{
    if (!gd || !gd.on) {{
      setTimeout(function() {{ attachHandlers(document.getElementById(chartId)); }}, 100);
      return;
    }}
    gd.on("plotly_afterplot", function() {{ linkifyYTicks(gd); }});
    gd.on("plotly_click", function(event) {{
      var ticker = String(event.points[0].y).trim().toUpperCase();
      if (urlMap[ticker]) window.open(urlMap[ticker], "_blank");
    }});
    linkifyYTicks(gd);
  }}

  attachHandlers(document.getElementById(chartId));
}})();
</script>
"""
