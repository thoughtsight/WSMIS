import streamlit as st
import pandas as pd
import numpy as np
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def searchable_table(df: pd.DataFrame, key: str, height: str = "400px", placeholder: str = "🔍 Search...") -> None:
    """Renders html_table with a live search filter and sort selector."""
    sc, ss = st.columns([3, 1])
    with sc:
        search = st.text_input("", placeholder=placeholder, key=f"{key}_search", label_visibility="collapsed")
    with ss:
        sort_cols = [c for c in df.columns if c.strip()]
        sort_col  = st.selectbox("", options=["— Sort by —"] + sort_cols, key=f"{key}_sort", label_visibility="collapsed")

    filtered = df.copy()
    if search:
        mask = filtered.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]
    if sort_col and sort_col != "— Sort by —":
        filtered = filtered.sort_values(sort_col, na_position="last")

    html_table(filtered, height=height)


def html_table(df, total_row=False, height="500px"):
    hdr = "".join(f"<th>{c}</th>" for c in df.columns)
    body = ""
    for i, (_, row) in enumerate(df.iterrows()):
        is_t = total_row and i == len(df) - 1
        cls = ' class="total-row"' if is_t else ""
        cells = ""
        for j, v in enumerate(row):
            sv = str(v)
            cc = ""
            if "badge-" not in sv and "traffic-light" not in sv and j > 0 and sv != "—":
                try:
                    nv = float(sv.replace(",", "").replace("₹", "").replace(" Cr", "").replace(" L", "").replace(" K", "").replace("%", "").replace("+", "").replace("▲", "").replace("▼", "").strip())
                    if nv < 0: cc = ' class="cell-neg"'
                except: pass
            cells += f"<td{cc}>{sv}</td>"
        body += f"<tr{cls}>{cells}</tr>"
    st.markdown(f"""<div style="max-height:{height};overflow:auto;border-radius:12px;border:1px solid #E5E5EA;">
        <table class="styled-table"><thead><tr>{hdr}</tr></thead><tbody>{body}</tbody></table>
    </div>""", unsafe_allow_html=True)


