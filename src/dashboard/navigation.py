"""Helpers for in-app navigation that Streamlit's embed iframe otherwise breaks."""

from __future__ import annotations

import streamlit.components.v1 as components


def inject_company_link_nav() -> None:
    """Make ticker ``/Company?ticker=…`` links navigate the Streamlit shell.

    Markdown ``<script>`` tags are unreliable under Streamlit, and ``target=_parent``
    alone is intercepted. ``components.html`` runs real JS in a child frame;
    from there the app document is ``window.parent`` and the embed shell is
    ``window.parent.parent``.
    """
    components.html(
        """
        <script>
        (function () {
          var app = window.parent;
          if (!app || !app.document) return;
          var appDoc = app.document;
          if (appDoc.documentElement.getAttribute("data-ml-company-nav") === "1") {
            return;
          }
          appDoc.documentElement.setAttribute("data-ml-company-nav", "1");
          appDoc.addEventListener(
            "click",
            function (event) {
              var anchor =
                event.target && event.target.closest
                  ? event.target.closest('a[href*="Company"]')
                  : null;
              if (!anchor) return;
              var href = anchor.getAttribute("href") || "";
              if (href.indexOf("ticker=") === -1) return;
              event.preventDefault();
              event.stopPropagation();
              var shell = app;
              try {
                if (app.parent && app.parent !== app) {
                  shell = app.parent;
                }
              } catch (err) {}
              try {
                shell.location.assign(href);
              } catch (err) {
                try {
                  app.location.assign(href);
                } catch (err2) {}
              }
            },
            true
          );
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )
