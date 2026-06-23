"""
WSMIS MetricCard v2 — Executive Light
Standardized KPI card using design tokens and CSS classes.
No inline hardcoded colours or sizes.
"""
import streamlit as st
from utils.calculations.common import calc_growth_pct
from ui.design_tokens import T


def _render_sparkline(values: list, color: str = None) -> str:
    """
    Render a simple SVG sparkline from a list of values.
    
    Args:
        values: List of numeric values (typically 6 months of data)
        color: Line color (defaults to primary token)
    
    Returns:
        SVG HTML string
    """
    if not values or len(values) < 2:
        return ""
    
    if color is None:
        color = T.COLOR_PRIMARY
    
    # Normalize values to 0-100 range for SVG
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val if max_val != min_val else 1
    
    # SVG dimensions
    width = 60
    height = 20
    padding = 2
    
    # Generate points
    points = []
    for i, val in enumerate(values):
        x = padding + (i / (len(values) - 1)) * (width - 2 * padding)
        y = height - padding - ((val - min_val) / range_val) * (height - 2 * padding)
        points.append(f"{x},{y}")
    
    points_str = " ".join(points)
    
    svg = f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <polyline
            points="{points_str}"
            fill="none"
            stroke="{color}"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
        />
    </svg>
    '''
    return svg


def MetricCard(
    label: str,
    value: str,
    sub: str = None,
    cp: float = None,
    pp: float = None,
    pp_label: str = None,
    benchmark: str = None,
    target: str = None,
    invert_trend: bool = False,
    sparkline: list = None,
    sparkline_color: str = None,
):
    """
    Executive Light KPI Card.

    Args:
        label:        Card label (e.g. "Labour Revenue")
        value:        Pre-formatted primary value string
        sub:          Optional sub-value or unit label
        cp:           Current period raw value (for growth calc)
        pp:           Previous period raw value (for growth calc)
        pp_label:     Pre-formatted PP label (e.g. "PP ₹3.64 Cr")
        benchmark:    Optional benchmark string
        target:       Optional target string
        invert_trend: If True, negative growth = good (Discounts page)
        sparkline:    Optional list of monthly values for sparkline chart
        sparkline_color: Optional color for sparkline line
    """
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""

    badge_html = ""
    if cp is not None and pp is not None:
        if pp <= 0 and cp > 0:
            badge_html = '<div class="kpi-delta-new">New ✦</div>'
        elif pp > 0:
            pct = calc_growth_pct(cp, pp, fill_value=0)
            effective = -pct if invert_trend else pct
            cls   = "kpi-delta-pos" if effective >= 0 else "kpi-delta-neg"
            arrow = "▲" if effective >= 0 else "▼"
            badge_html = f'<div class="{cls}">{arrow} {abs(pct):.1f}%</div>'

    pp_html = f'<div class="kpi-sub">{pp_label}</div>' if pp_label else ""

    sparkline_html = ""
    if sparkline:
        sparkline_html = f'<div class="kpi-sparkline">{_render_sparkline(sparkline, sparkline_color)}</div>'

    meta_parts = []
    if benchmark is not None:
        meta_parts.append(f'<span style="color:var(--color-text-tertiary)">Bench:</span> {benchmark}')
    if target is not None:
        meta_parts.append(f'<span style="color:var(--color-text-tertiary)">Target:</span> {target}')
    meta_html = (
        f'<div class="kpi-meta">{" · ".join(meta_parts)}</div>'
        if meta_parts else ""
    )

    html = (
        f'<div class="kpi-card">'
        f'  <div>'
        f'    <div class="kpi-label">{label}</div>'
        f'    <div class="kpi-value">{value}</div>'
        f'    {sub_html}'
        f'    {badge_html}'
        f'    {pp_html}'
        f'    {sparkline_html}'
        f'  </div>'
        f'  {meta_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def KPIGrid(metrics: list, cols: int = None):
    """
    Renders a responsive grid of MetricCards.

    Args:
        metrics: List of dicts — each dict maps to MetricCard kwargs.
        cols:    Column count override. Defaults to len(metrics).
    """
    if not metrics:
        return

    n = cols or len(metrics)
    columns = st.columns(n)
    for i, metric in enumerate(metrics):
        with columns[i % n]:
            MetricCard(**metric)
