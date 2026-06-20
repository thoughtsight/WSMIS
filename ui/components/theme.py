"""
WSMIS Executive Light — CSS Injection Helper
Phase 2 of Design System v2.0

The charcoal dark theme has been retired.
All pages now use Executive Light (see static/style.css and ui/design_tokens.py).

This module provides helper functions for injecting inline styles that
cannot be expressed through global CSS (e.g. dynamic colour based on data values).
"""

from ui.design_tokens import T


def growth_color(value: float, text: bool = True) -> str:
    """
    Returns the correct WCAG-AA-compliant colour for a growth value.

    Args:
        value: Growth percentage (positive = good, negative = bad)
        text:  If True, returns accessible on-light text colour.
               If False, returns fill colour for dark backgrounds / icons.
    """
    if value >= 0:
        return T.COLOR_SUCCESS if text else T.COLOR_SUCCESS_FILL
    return T.COLOR_DANGER if text else T.COLOR_DANGER_FILL


def growth_badge_html(value: float, label: str = None, new_marker: bool = False) -> str:
    """
    Returns an HTML growth badge (<span>) with correct colour and arrow.

    Args:
        value:      Growth percentage value
        label:      Optional override label (e.g. "New ✦")
        new_marker: If True, renders a "New ✦" info badge (no value)
    """
    if new_marker:
        return (
            f'<span class="badge-new">New ✦</span>'
        )

    arrow = "▲" if value >= 0 else "▼"
    cls   = "badge-pos" if value >= 0 else "badge-neg"
    text  = label if label else f"{arrow} {abs(value):.1f}%"
    return f'<span class="{cls}">{text}</span>'


def kpi_card_html(
    label: str,
    value: str,
    sub: str = None,
    growth: float = None,
    pp_label: str = None,
    new_location: bool = False,
    invert_trend: bool = False,
) -> str:
    """
    Returns Executive Light KPI card HTML.
    Uses CSS classes from style.css (no inline styles).

    Args:
        label:        Card label (e.g. "Labour Revenue")
        value:        Formatted primary value (e.g. "₹4.27 Cr")
        sub:          Optional sub-label below value
        growth:       Growth percentage (float)
        pp_label:     Previous period formatted value (e.g. "PP ₹3.64 Cr")
        new_location: Show "New ✦" badge instead of growth
        invert_trend: If True, negative growth is good (e.g. Discounts)
    """
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""

    badge_html = ""
    if new_location:
        badge_html = '<div class="kpi-delta-new">New ✦</div>'
    elif growth is not None:
        effective = -growth if invert_trend else growth
        cls = "kpi-delta-pos" if effective >= 0 else "kpi-delta-neg"
        arrow = "▲" if effective >= 0 else "▼"
        badge_html = f'<div class="{cls}">{arrow} {abs(growth):.1f}%</div>'

    pp_html = f'<div class="kpi-sub">{pp_label}</div>' if pp_label else ""

    return (
        f'<div class="kpi-card">'
        f'  <div class="kpi-label">{label}</div>'
        f'  <div class="kpi-value">{value}</div>'
        f'  {sub_html}'
        f'  {badge_html}'
        f'  {pp_html}'
        f'</div>'
    )
