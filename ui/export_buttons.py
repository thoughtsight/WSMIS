"""
Reusable export button components for WSMIS dashboards.

Provides render_export_buttons() — a single drop-in helper that renders
CSV, Excel, and PDF download buttons with consistent styling, metadata,
and filename conventions.

Usage:
    from ui.export_buttons import render_export_buttons
    from services.export_service import ExportMeta

    meta = ExportMeta(
        report_title="Margin Analysis",
        location=selected_location or "All Locations",
        date_range=", ".join(selected_months) if selected_months else "",
    )
    render_export_buttons(df, meta, key_prefix="margin")

    # Selective formats only:
    render_export_buttons(df, meta, formats=["csv", "excel"], key_prefix="margin")
"""
from __future__ import annotations

from typing import List, Literal, Optional

import pandas as pd
import streamlit as st

from services.export_service import (
    ExportMeta,
    build_filename,
    export_csv,
    export_excel,
    export_pdf,
)

ExportFormat = Literal["csv", "excel", "pdf"]

_FORMAT_LABELS = {
    "csv":   "⬇️ CSV",
    "excel": "⬇️ Excel",
    "pdf":   "⬇️ PDF",
}
_FORMAT_MIME = {
    "csv":   "text/csv",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf":   "application/pdf",
}
_FORMAT_EXT = {
    "csv":   "csv",
    "excel": "xlsx",
    "pdf":   "pdf",
}


def render_export_buttons(
    df: pd.DataFrame,
    meta: ExportMeta,
    formats: Optional[List[ExportFormat]] = None,
    key_prefix: str = "export",
    label: str = "Export",
    collapsed: bool = False,
) -> None:
    """
    Render download buttons for one or more export formats.

    Each button generates the export on-demand and triggers a browser download.
    Filenames follow the convention: <Location>_<ReportName>_<YYYY-MM-DD>.<ext>

    Args:
        df:          DataFrame to export. Must not be None.
        meta:        ExportMeta with report_title, location, date_range.
        formats:     Formats to render. Defaults to ["csv", "excel", "pdf"].
                     Valid values: "csv", "excel", "pdf".
        key_prefix:  Unique Streamlit widget key prefix — use a distinct value
                     per page to avoid duplicate-key errors.
        label:       Section label shown above the buttons.
        collapsed:   If True, wrap buttons inside an st.expander.
    """
    if formats is None:
        formats = ["csv", "excel", "pdf"]

    if df is None or df.empty:
        st.caption("⚠ No data available to export.")
        return

    report_name = meta.report_title.replace(" ", "")
    location    = meta.location.replace(" ", "")

    def _render():
        cols = st.columns(len(formats))
        for i, fmt in enumerate(formats):
            with cols[i]:
                _render_single_button(df, meta, fmt, location, report_name, key_prefix)

    if collapsed:
        with st.expander(label, expanded=False):
            _render()
    else:
        st.caption(label)
        _render()


def _render_single_button(
    df: pd.DataFrame,
    meta: ExportMeta,
    fmt: ExportFormat,
    location: str,
    report_name: str,
    key_prefix: str,
) -> None:
    """Render one download button for the given format."""
    filename = build_filename(location, report_name, _FORMAT_EXT[fmt])
    btn_label = _FORMAT_LABELS[fmt]
    mime      = _FORMAT_MIME[fmt]
    key       = f"{key_prefix}_{fmt}"

    if fmt == "csv":
        data = export_csv(df, meta)
        st.download_button(
            label=btn_label,
            data=data,
            file_name=filename,
            mime=mime,
            key=key,
            use_container_width=True,
        )

    elif fmt == "excel":
        data = export_excel(df, meta)
        st.download_button(
            label=btn_label,
            data=data,
            file_name=filename,
            mime=mime,
            key=key,
            use_container_width=True,
        )

    elif fmt == "pdf":
        try:
            data = export_pdf(df, meta)
            st.download_button(
                label=btn_label,
                data=data,
                file_name=filename,
                mime=mime,
                key=key,
                use_container_width=True,
            )
        except ImportError:
            st.button(
                "⬇️ PDF (unavailable)",
                key=key,
                disabled=True,
                use_container_width=True,
                help="Install reportlab to enable PDF export: pip install reportlab",
            )
