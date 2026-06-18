import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from io import BytesIO
from datetime import datetime



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
from utils.filters import (
    apply_month_filter, apply_location_filter, apply_location_group_filter,
    apply_service_type_filter, apply_advisor_filter, apply_mp_pb_filter, split_cp_pp
)
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from utils.constants import ADV_COL, MP_COLORS

# Import shared UI helpers from app
from ui.kpi_cards import kpi
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def render(exp_df, selected_months):
    """Expense Analysis Executive Dashboard - uses EXP worksheet."""
    import streamlit.components.v1 as components
    import exp_report

    if exp_df is None or exp_df.empty:
        st.warning("No expense data available for the selected period/location.")
        return

    # Ensure required columns exist
    required_cols = ['Location', 'Month Name', 'Expenses Name', 'Expenses Rs.']
    missing_cols = [col for col in required_cols if col not in exp_df.columns]
    if missing_cols:
        st.warning(f"Missing required columns in EXP sheet: {missing_cols}")
        return

    # Filter to only expense-related rows if there's a category column
    if 'Expenses Group' in exp_df.columns:
        exp_df = exp_df[exp_df['Expenses Group'].notna()]
    
    if exp_df.empty:
        st.warning("No expense data available for the selected period.")
        return
    
    if exp_df.empty:
        st.warning("No expense data available for the selected period.")
        return

    # Get unique locations
    locations = sorted(exp_df['Location'].dropna().unique().tolist())
    
    # Build period label
    period_label = ", ".join(sorted(selected_months)) if selected_months else "All Periods"
    
    # Generate expense report HTML
    try:
        exp_html = exp_report.render_in_streamlit(
            df_raw=exp_df,
            locations=locations,
            loc_map=None,
            report_period=period_label
        )
        components.html(exp_html, height=2800, scrolling=True)
    except Exception as e:
        st.error(f"Error generating Expense Analysis dashboard: {e}")
