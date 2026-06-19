"""
WSMIS Executive Tooltip Templates
Reusable tooltip templates for all WSMIS charts.

This module provides consistent, executive-friendly tooltip templates
with Indian number formatting for all chart types.
"""

from typing import List, Tuple, Any
from .chart_formatters import fmt_inr_full, fmt_pct


def get_revenue_tooltip(
    months: List[str],
    cp_values: List[float],
    pp_values: List[float],
    growth_values: List[float],
    currency_symbol: str = "₹"
) -> str:
    """
    Generate executive tooltip template for revenue comparison charts.

    Displays:
    - Month
    - Current Period Revenue
    - Previous Period Revenue
    - Difference
    - Growth %

    Args:
        months: List of month labels
        cp_values: List of current period revenue values
        pp_values: List of previous period revenue values
        growth_values: List of growth percentage values
        currency_symbol: Currency symbol to use (default: ₹)

    Returns:
        Plotly hovertemplate string

    Example:
        tooltip = get_revenue_tooltip(months, cp_vals, pp_vals, growth)
        fig.add_trace(go.Bar(..., hovertemplate=tooltip))
    """
    return (
        "<b>%{customdata[0]}</b><br><br>"
        f"<b>Current Period:</b> {currency_symbol}%{{customdata[1]:,.0f}}<br>"
        f"<b>Previous Period:</b> {currency_symbol}%{{customdata[2]:,.0f}}<br>"
        f"<b>Difference:</b> {currency_symbol}%{{customdata[3]:,.0f}}<br>"
        "<b>Growth:</b> %{customdata[4]:.1f}%<extra></extra>"
    )


def get_simple_tooltip(
    label: str,
    value: float,
    formatter: str = "number"
) -> str:
    """
    Generate simple tooltip for single-value charts.
    
    Args:
        label: Label for the value (e.g., "Revenue", "Jobs")
        value: The value to display
        formatter: Format type - "number", "currency", "percentage"
    
    Returns:
        Tooltip string
    """
    if formatter == "currency":
        formatted = fmt_inr_full(value)
    elif formatter == "percentage":
        formatted = fmt_pct(value)
    else:
        formatted = f"{value:,.0f}"
    
    return f"<b>{label}</b><br>{formatted}"


def get_comparison_tooltip(
    label: str,
    cp_value: float,
    pp_value: float,
    growth: float,
    currency_symbol: str = "₹"
) -> str:
    """
    Generate tooltip for comparison charts (CP vs PP).
    
    Args:
        label: Label for the data point (e.g., month, location)
        cp_value: Current period value
        pp_value: Previous period value
        growth: Growth percentage
        currency_symbol: Currency symbol to use (default: ₹)
    
    Returns:
        Tooltip string
    """
    return (
        f"<b>{label}</b><br><br>"
        f"Current: {currency_symbol}{fmt_inr_full(cp_value)}<br>"
        f"Previous: {currency_symbol}{fmt_inr_full(pp_value)}<br>"
        f"Difference: {currency_symbol}{fmt_inr_full(cp_value - pp_value)}<br>"
        f"Growth: {fmt_pct(growth)}"
    )


def get_kpi_tooltip(
    label: str,
    cp_value: float,
    pp_value: float,
    growth: float,
    unit: str = ""
) -> str:
    """
    Generate tooltip for KPI cards.
    
    Args:
        label: KPI label
        cp_value: Current period value
        pp_value: Previous period value
        growth: Growth percentage
        unit: Unit to append (e.g., "Jobs", "₹")
    
    Returns:
        Tooltip string
    """
    return (
        f"<b>{label}</b><br><br>"
        f"Current: {cp_value:,.0f} {unit}<br>"
        f"Previous: {pp_value:,.0f} {unit}<br>"
        f"Growth: {fmt_pct(growth)}"
    )


def prepare_customdata(
    months: List[str],
    cp_values: List[float],
    pp_values: List[float],
    growth_values: List[float]
) -> List[Tuple[str, float, float, float, float]]:
    """
    Prepare customdata for use with revenue tooltip template.

    Args:
        months: List of month labels
        cp_values: List of current period values
        pp_values: List of previous period values
        growth_values: List of growth values

    Returns:
        List of tuples (month, cp, pp, difference, growth) for customdata
    """
    differences = [cp - pp for cp, pp in zip(cp_values, pp_values)]
    return list(zip(months, cp_values, pp_values, differences, growth_values))
