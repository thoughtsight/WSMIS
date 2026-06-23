from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine

"""
Shared dashboard utilities for Executive, Labour, and Parts dashboards.
Extracted to eliminate code duplication and maintain consistency.
"""
from services.state_manager import StateManager


_CSS_INJECTED = {}

def inject_responsive_css():
    """Inject responsive CSS for dashboard KPI cards. Idempotent."""
    if _CSS_INJECTED.get("responsive"):
        return
    _CSS_INJECTED["responsive"] = True
    st.markdown("""<style>
@media (max-width: 1024px) {
    [data-testid="stHorizontalBlock"] > div { min-width: 100% !important; }
}
@media (min-width: 1800px) {
    .kpi-label { font-size: var(--type-sm) !important; }
}
.kpi-sub { color: var(--color-text-secondary) !important; }
.lab-summary { font-size: var(--type-sm); color: var(--color-text-secondary); padding: 2px 0 8px 0; }

/* === Streamlit button override — executive style === */
div[data-testid="stDownloadButton"] > button {
  background: var(--color-surface) !important;
  border: 1px solid var(--color-border) !important;
  color: var(--color-text-primary) !important;
  font-family: var(--font-family) !important;
  font-size: var(--type-sm) !important;
  font-weight: 500 !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-xs) !important;
  transition: box-shadow 150ms ease, border-color 150ms ease !important;
}
div[data-testid="stDownloadButton"] > button:hover {
  border-color: var(--color-border-hover) !important;
  box-shadow: var(--shadow-sm) !important;
}

/* === Streamlit spinner override — branded colour === */
div[data-testid="stSpinner"] > div {
  border-color: var(--color-border) var(--color-border) var(--color-primary) transparent !important;
}

/* === Streamlit selectbox override — match design system === */
div[data-testid="stSelectbox"] > div {
  font-family: var(--font-family) !important;
  font-size: var(--type-sm) !important;
}

/* === Focus state — WCAG 2.1 SC 2.4.7 compliance === */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
</style>""", unsafe_allow_html=True)


def apply_period_filters(df, active_pairs, cross_month_key):
    """
    Apply CP/PP period filters with optional cross-filter by month.
    
    Args:
        df: Source DataFrame
        active_pairs: List of (cp_month, pp_month, label) tuples
        cross_month_key: Session state key for cross-filter month
    
    Returns:
        (cp_df, pp_df): Filtered DataFrames for current and prior periods
    """
    cp_months_active = [p[0] for p in active_pairs]
    pp_months_active = [p[1] for p in active_pairs]
    click_month = st.session_state.get(cross_month_key)
    if click_month:
        paired_pm = next((p[1] for p in active_pairs if p[0] == click_month), None)
        cp_months_active = [click_month]
        pp_months_active = [paired_pm] if paired_pm else []

    cp = df[df["Month Name"].isin(cp_months_active)]
    pp = df[df["Month Name"].isin(pp_months_active)]
    return cp, pp


def render_kpi_card(title, cp_val, pp_val, g_val, delta_val=None, is_margin=False, margin_g=0):
    """
    Render a KPI card with delta badges.
    
    Args:
        title: Card title
        cp_val: Current period value (formatted string)
        pp_val: Prior period value (formatted string)
        g_val: Growth percentage
        delta_val: Absolute delta value (optional)
        is_margin: True if this is a margin card (uses percentage points)
        margin_g: Margin growth in percentage points (if is_margin=True)
    """
    if g_val > 0:
        badge = f'<div class="kpi-delta-pos">\u25b2 {g_val:.1f}% vs PP</div>'
    elif g_val < 0:
        badge = f'<div class="kpi-delta-neg">\u25bc {abs(g_val):.1f}% vs PP</div>'
    else:
        badge = '<div class="kpi-delta-new">0% vs PP</div>'
    
    delta_html = ""
    if delta_val is not None and not is_margin:
        delta_str = fmt_inr_short(abs(delta_val))
        if delta_val > 0:
            delta_html = f'<div class="kpi-delta-pos">\u25b2 {delta_str} \u20b9</div>'
        elif delta_val < 0:
            delta_html = f'<div class="kpi-delta-neg">\u25bc {delta_str} \u20b9</div>'
    
    if is_margin:
        if margin_g > 0:
            delta_html = f'<div class="kpi-delta-pos">\u25b2 {margin_g:+.1f}pp vs PP</div>'
        elif margin_g < 0:
            delta_html = f'<div class="kpi-delta-neg">\u25bc {abs(margin_g):.1f}pp vs PP</div>'
        else:
            delta_html = '<div class="kpi-delta-new">0pp vs PP</div>'
    
    return (
        f'<div class="kpi-card">'
        f'  <div class="kpi-label">{title}</div>'
        f'  <div class="kpi-value">{cp_val}</div>'
        f'  <div class="kpi-sub">{pp_val}</div>'
        f'  {badge}'
        f'  {delta_html}'
        f'</div>')


def render_svc_row_with_delta(label, cp_v, pp_v, cp_raw, pp_raw):
    """
    Render a service panel row with delta pill.
    
    Args:
        label: Row label
        cp_v: Current period value (formatted string)
        pp_v: Prior period value (formatted string)
        cp_raw: Current period raw value for growth calculation
        pp_raw: Prior period raw value for growth calculation
    """
    growth = calc_growth_pct(cp_raw, pp_raw, fill_value=0) if pp_raw > 0 else 0
    if growth > 0:
        pill = f'<span class="delta-pill pos" style="font-size:10px;">▲{growth:.1f}%</span>'
    elif growth < 0:
        pill = f'<span class="delta-pill neg" style="font-size:10px;">▼{abs(growth):.1f}%</span>'
    else:
        pill = ""
    return (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:var(--space-1) 0;border-bottom:1px solid var(--color-border-sub);">'
        f'  <div style="color:var(--color-text-secondary);font-size:var(--type-xs);font-weight:600;">{label}</div>'
        f'  <div style="display:flex;align-items:baseline;gap:var(--space-2);">'
        f'    <span style="color:var(--color-text-primary);font-weight:700;font-size:var(--type-md);">{cp_v}</span>'
        f'    <span style="color:var(--color-text-secondary);font-size:var(--type-sm);font-weight:500;">PP {pp_v}</span>'
        f'    {pill}'
        f'  </div>'
        f'</div>'
    )


def render_svc_panel(title, stats, delta_pill=""):
    """
    Render a service panel with rows and optional delta pill in title.
    
    Args:
        title: Panel title
        stats: Dict with cp_rev, pp_rev, cp_jobs, pp_jobs, cp_rpc, pp_rpc
        delta_pill: Optional HTML delta pill string for title
    """
    cp_jobs = str(int(stats['cp_jobs'])) if stats['cp_jobs'] > 0 else "0"
    pp_jobs = str(int(stats['pp_jobs'])) if stats['pp_jobs'] > 0 else "0"
    cp_rpc = "\u2014" if stats["cp_rpc"] == 0 and stats["cp_jobs"] == 0 else fmt_inr_short(stats["cp_rpc"])
    pp_rpc = "\u2014" if stats["pp_rpc"] == 0 and stats["pp_jobs"] == 0 else fmt_inr_short(stats["pp_rpc"])
    cp_rev = fmt_inr_short(stats["cp_rev"])
    pp_rev = fmt_inr_short(stats["pp_rev"])
    
    return (
        f'<div class="section-card" style="padding:var(--space-4);margin:0;">'
        f'  <div class="kpi-label" style="margin-bottom:var(--space-2);display:flex;align-items:center;">{title}{delta_pill}</div>'
        f'  {render_svc_row_with_delta("Jobs", cp_jobs, pp_jobs, stats["cp_jobs"], stats["pp_jobs"])}'
        f'  {render_svc_row_with_delta("Avg /JC", cp_rpc, pp_rpc, stats["cp_rpc"], stats["pp_rpc"])}'
        f'  {render_svc_row_with_delta("Revenue", cp_rev, pp_rev, stats["cp_rev"], stats["pp_rev"])}'
        f'</div>'
    )


def render_cross_filter_bar(cross_month_key, month_label=None):
    """
    Render cross-filter chip bar with clear buttons.
    
    Args:
        cross_month_key: Session state key for cross-filter month
        month_label: Optional custom label for the month (defaults to month name)
    """
    chips = []
    cross_month = StateManager.get(cross_month_key)
    if cross_month:
        label = month_label or cross_month
        chips.append(("\U0001f4c5 " + label, cross_month_key))
    if not chips:
        return
    
    html = f'<div style="display:flex;gap:{T.SPACE_2}px;align-items:center;padding:4px 0 8px 0;flex-wrap:wrap">'
    html += f'<span style="font-size:{T.TYPE_XS}px;color:var(--color-text-secondary);font-weight:600">Filtered by:</span>'
    for label, key in chips:
        html += (f'<span style="background:{T.COLOR_INFO_BG};color:{T.COLOR_PRIMARY};border:1px solid {T.COLOR_BORDER};'
                 f'border-radius:{T.RADIUS_FULL}px;padding:{T.SPACE_1}px {T.SPACE_2}px;font-size:{T.TYPE_XS}px;font-weight:600">'
                 f'{label} \u2715</span>')
    html += (f'<span style="font-size:{T.TYPE_XS}px;color:{T.COLOR_DANGER};cursor:pointer;margin-left:{T.SPACE_1}px;'
             f'font-weight:600">Clear all filters</span></div>')
    st.markdown(html, unsafe_allow_html=True)

    for label, key in chips:
        if st.button(label + " \u2715", key=f"chip_{key}", label_visibility="visible"):
            StateManager.set(key, None)
            st.rerun()
    if st.button("Clear all filters", key=f"chip_clear_all_{cross_month_key}", label_visibility="visible"):
        StateManager.set(cross_month_key, None)
        st.rerun()


def style_table_bold_total(row, location_col="Location"):
    """Style function for tables: bold and highlight TOTAL row."""
    is_total = row[location_col] == "TOTAL"
    is_odd = getattr(row, "name", 0) % 2 == 1 if isinstance(getattr(row, "name", None), int) else False
    styles = []
    for _ in row:
        style = ""
        if is_total:
            style += f"font-weight: 700; background-color: {T.COLOR_INFO_BG};"
        elif is_odd:
            style += f"background-color: {T.COLOR_SURFACE2};"
        styles.append(style)
    return styles


def style_color_growth(val):
    """Style function: color growth values green/red."""
    if pd.isna(val) or val == 0: return ""
    return f"color: {T.COLOR_SUCCESS};" if val > 0 else f"color: {T.COLOR_DANGER};"


def style_margin_color(val):
    """Style function: color margin values based on thresholds (13%/11%)."""
    if pd.isna(val) or val == 0: return ""
    if val >= 13.0: return f"color:{T.COLOR_SUCCESS};font-weight:700"
    if val >= 11.0: return f"color:{T.COLOR_WARNING};font-weight:700"
    return f"color:{T.COLOR_DANGER};font-weight:700"


def format_rank_movement(val):
    """Format rank movement with CSS classes."""
    if val == "—" or val is None: return "—"
    if not isinstance(val, str):
        return str(val)
    if "▲" in val: return f'<span class="rank-up">{val}</span>'
    if "▼" in val: return f'<span class="rank-dn">{val}</span>'
    if "=" in val: return f'<span class="rank-eq">{val}</span>'
    return val


def compute_rank_movement(loc, cp_ranks, pp_ranks):
    """Compute rank movement between CP and PP periods."""
    cp_r = cp_ranks.get(loc)
    pp_r = pp_ranks.get(loc)
    if cp_r is None or pp_r is None:
        return "—"
    diff = pp_r - cp_r
    if diff > 0:
        return f"▲{diff}"
    elif diff < 0:
        return f"▼{abs(diff)}"
    else:
        return "="


def navigate_to_page(page_name: str, drill_params: dict = None) -> None:
    """
    Navigate to a page with optional drill-through parameters.
    
    Args:
        page_name: Target page name (e.g., "Parts Detail", "Sales Mix")
        drill_params: Optional dict of drill-through parameters (location, category, etc.)
    """
    from services.state_manager import StateManager
    from services.route_service import get_route_service
    
    # Set drill-through parameters in parts_ namespace
    if drill_params:
        for key, value in drill_params.items():
            StateManager.set(f"parts_{key}", value)
        
        # In the new architecture, the active page's title could be retrieved from st.context if available,
        # but for simplicity we rely on the drill params from page string or default "Previous Page"
        StateManager.set("parts_drill_from_page", "Previous Page")
    
    # Navigate to target page using native st.switch_page
    target_page_obj = get_route_service().get_registry().get_page_by_title(page_name)
    if target_page_obj:
        st.switch_page(target_page_obj)
    else:
        st.error(f"Cannot navigate: Page '{page_name}' not found in registry.")


def get_drill_params() -> dict:
    """
    Get current drill-through parameters from parts_ namespace.
    
    Returns:
        Dict with drill_location, drill_category, drill_from_page (if set)
    """
    from services.state_manager import StateManager
    
    return {
        "location": StateManager.get("parts_drill_location"),
        "category": StateManager.get("parts_drill_category"),
        "from_page": StateManager.get("parts_drill_from_page"),
    }


def clear_drill_params() -> None:
    """Clear all drill-through parameters from parts_ namespace."""
    from services.state_manager import StateManager
    
    StateManager.set("parts_drill_location", None)
    StateManager.set("parts_drill_category", None)
    StateManager.set("parts_drill_from_page", None)
