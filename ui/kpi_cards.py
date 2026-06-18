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
    NEXA_LOCATIONS, PB_SERVICE_TYPES, MONTH_SORT_ORDER, FY_MONTHS, SERVICE_ACCOUNT,
    MP_COLORS
)
from utils.filters import (
    apply_month_filter, apply_location_filter, apply_location_group_filter,
    apply_service_type_filter, apply_advisor_filter, apply_mp_pb_filter, split_cp_pp
)

def kpi(label, value, sub=None, cp=None, pp=None, benchmark=None, target=None):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    delta_html = ""
    if cp is not None and pp is not None:
        if pp <= 0:
            delta_html = '<div class="kpi-delta-new">New ✦</div>'
        else:
            pct = calc_growth_pct(cp, pp, fill_value=0)
            cls = "kpi-delta-pos" if pct >= 0 else "kpi-delta-neg"
            arrow = "▲" if pct >= 0 else "▼"
            delta_html = f'<div class="{cls}">{arrow} {abs(pct):.1f}%</div>'
    meta_parts = []
    if benchmark is not None:
        meta_parts.append(f'□ Bench: {benchmark}')
    if target is not None:
        meta_parts.append(f'◦ Tgt: {target}')
    meta_html = f'<div class="kpi-meta">{" · ".join(meta_parts)}</div>' if meta_parts else ""
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>{sub_html}{delta_html}{meta_html}
    </div>""", unsafe_allow_html=True)


