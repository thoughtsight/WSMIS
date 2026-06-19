"""
WSMIS Executive Chart Design System
Global responsive chart theme for all WSMIS reports.

This module provides responsive typography and styling that scales
intelligently based on chart size (small, medium, large, full-width).

This module now consumes the ExecutiveTheme design foundation for
centralized design tokens and consistent visual language.
"""

import plotly.graph_objects as go
import plotly.io as pio
from typing import Literal, Dict, Any
from ui.executive_theme import ExecutiveTheme, ExecutiveChart, ChartSize


def get_chart_theme(size: ChartSize = "medium") -> Dict[str, Any]:
    """
    Get responsive chart theme configuration based on size.

    This function now consumes ExecutiveChart for centralized design tokens.

    Args:
        size: Chart size - "small", "medium", "large", or "full"

    Returns:
        Dictionary with theme configuration including:
        - title_font: Font configuration for chart title
        - axis_title_font: Font configuration for axis titles
        - axis_tick_font: Font configuration for axis tick labels
        - legend_font: Font configuration for legend
        - revenue_label_font: Font configuration for revenue data labels
        - growth_label_font: Font configuration for growth data labels
        - tooltip_font: Font configuration for hover tooltips
        - marker_size: Size of scatter markers
        - line_width: Width of line traces
        - margin: Chart margins

    Example:
        theme = get_chart_theme("large")
        fig.update_layout(title=dict(**theme["title_font"]))
    """
    return ExecutiveChart.get_theme(size)


def get_chart_height(size: ChartSize = "medium") -> int:
    """
    Get recommended chart height based on size.

    This function now consumes ExecutiveTheme for centralized design tokens.

    Args:
        size: Chart size - "small", "medium", "large", or "full"

    Returns:
        Recommended height in pixels
    """
    return ExecutiveTheme.get_chart_height(size)


def get_growth_color(value: float) -> str:
    """
    Get semantic color for growth values.

    This function now consumes ExecutiveTheme for centralized design tokens.

    Args:
        value: Growth percentage value

    Returns:
        Color hex code - green for positive, red for negative
    """
    return ExecutiveTheme.get_growth_color(value)


def get_marker_colors(values: list) -> list:
    """
    Get semantic colors for a list of growth values.

    This function now consumes ExecutiveTheme for centralized design tokens.

    Args:
        values: List of growth percentage values

    Returns:
        List of color hex codes
    """
    return ExecutiveTheme.get_marker_colors(values)


def apply_wsmis_theme():
    """
    Registers and applies the standard WSMIS Enterprise Plotly theme.
    """
    wsmis_template = go.layout.Template()

    # Base layout
    wsmis_template.layout = go.Layout(
        font=dict(family="Inter, Roboto, sans-serif", color="#1d1d1f"),
        title=dict(font=dict(size=16, color="#1d1d1f", weight="bold")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=20),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, Roboto, sans-serif",
            bordercolor="#e5e5ea"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color="#6E6E73")
        ),
        colorway=[
            "#007AFF", # Blue
            "#34C759", # Green
            "#FF9F0A", # Orange
            "#FF3B30", # Red
            "#5856D6", # Purple
            "#30B0C7"  # Cyan
        ]
    )

    # Axes
    wsmis_template.layout.xaxis = dict(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="#e5e5ea",
        tickfont=dict(color="#6E6E73", size=11)
    )

    wsmis_template.layout.yaxis = dict(
        showgrid=True,
        gridcolor="#f5f5f7",
        zeroline=True,
        zerolinecolor="#e5e5ea",
        showline=False,
        tickfont=dict(color="#6E6E73", size=11)
    )

    pio.templates["wsmis"] = wsmis_template
    pio.templates.default = "wsmis"
