import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from services.financial_service import FinancialService
from utils.calculations.fact_metrics import (
    get_labour_sales, get_parts_sales, get_net_labour, get_net_parts,
    get_labour_discount, get_parts_discount, get_oil_sales, get_tyre_sales,
    get_battery_sales, get_accessory_sales, get_total_margin, get_parts_profit,
    get_jobcard_count
)
from utils.calculations.revenue import (
    calculate_gross_revenue, calculate_net_revenue, calculate_total_revenue,
    calculate_revenue_per_jobcard, calculate_revenue_growth
)
from utils.calculations.margin import (
    calculate_total_margin, calculate_parts_margin, calculate_margin_per_jobcard,
    calculate_margin_growth, calculate_margin_kpis
)
from utils.calculations.discount import (
    calculate_labour_discount, calculate_parts_discount, calculate_total_discount,
    calculate_labour_discount_pct, calculate_parts_discount_pct,
    calculate_overall_discount_pct, calculate_discount_per_jobcard,
    calculate_discount_growth
)
from utils.calculations.leakage import (
    compute_discount_aggregates, compute_parts_leakage, compute_leakage_delta
)
from utils.calculations.common import (
    safe_divide, calc_ratio, calc_growth_pct, calc_contribution_pct,
    calc_achievement_pct, calc_variance
)
from utils.aggregations import (
    group_summary, location_summary, advisor_summary, monthly_summary,
    service_summary, dealer_summary, pivot_summary, top_n
)
from utils.constants import (
    ADV_COL, CLIENTS, EXCLUDE_SERVICE_TYPES, ARENA_LOCATIONS,
    NEXA_LOCATIONS, BS_SERVICE_TYPES, MONTH_SORT_ORDER, FY_MONTHS, SERVICE_ACCOUNT,
    WS_COLORS
)
from utils.filters import (
    apply_month_filter, apply_location_filter, apply_location_group_filter,
    apply_service_type_filter, apply_advisor_filter, apply_ws_bs_filter, split_cp_pp
)

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


