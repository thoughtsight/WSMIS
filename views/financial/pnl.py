from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine
from views.dashboard_common import inject_responsive_css

import streamlit as st




# Import shared UI helpers from app
from ui.traffic import yoy_badge, traffic_light, tgt_badge

def render(df_filtered, exp_df_filtered, selected_months):
    """Profit & Loss Executive Dashboard - uses existing filtered WSMIS and EXP dataframes."""
    inject_responsive_css()
    PageBreadcrumb(["Finance", "Profit & Loss"])
    import pnl_report

    # Build period label
    period_label = ", ".join(sorted(selected_months)) if selected_months else "All Periods"

    # Generate P&L report using pnl_report module
    try:
        pnl_report.render_in_streamlit(
            df=df_filtered,
            exp_df=exp_df_filtered,
            selected_months=selected_months,
            locations=None,
            report_period=period_label
        )
    except Exception as e:
        st.error(f"Error generating Profit & Loss dashboard: {e}")
    UniversalFooter()

