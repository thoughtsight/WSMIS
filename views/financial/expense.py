from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine
from views.dashboard_common import inject_responsive_css





# Import shared UI helpers from app
from ui.traffic import yoy_badge, traffic_light, tgt_badge

def render(exp_df, selected_months):
    """Expense Analysis Executive Dashboard - uses EXP worksheet."""
    inject_responsive_css()
    PageBreadcrumb(["Finance", "Expense Analysis"])
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
    UniversalFooter()
