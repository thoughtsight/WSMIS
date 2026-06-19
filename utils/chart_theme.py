"""
WSMIS Executive Chart Design System
Global responsive chart theme for all WSMIS reports.

This module provides responsive typography and styling that scales
intelligently based on chart size (small, medium, large, full-width).
"""

import plotly.graph_objects as go
import plotly.io as pio
from typing import Literal, Dict, Any


# Chart size definitions
ChartSize = Literal["small", "medium", "large", "full"]


# Typography scaling configuration
TYPOGRAPHY_SCALES = {
    "small": {
        "title": 16,
        "axis_title": 12,
        "axis_tick": 11,
        "legend": 11,
        "revenue_label": 12,
        "growth_label": 11,
        "tooltip": 12,
        "marker": 6,
        "line_width": 2,
        "margin": {"t": 40, "b": 40, "l": 48, "r": 24},
    },
    "medium": {
        "title": 18,
        "axis_title": 14,
        "axis_tick": 12,
        "legend": 12,
        "revenue_label": 13,
        "growth_label": 12,
        "tooltip": 13,
        "marker": 8,
        "line_width": 2.5,
        "margin": {"t": 50, "b": 50, "l": 50, "r": 30},
    },
    "large": {
        "title": 20,
        "axis_title": 16,
        "axis_tick": 13,
        "legend": 13,
        "revenue_label": 15,
        "growth_label": 14,
        "tooltip": 14,
        "marker": 10,
        "line_width": 3,
        "margin": {"t": 60, "b": 60, "l": 60, "r": 40},
    },
    "full": {
        "title": 24,
        "axis_title": 18,
        "axis_tick": 15,
        "legend": 15,
        "revenue_label": 18,
        "growth_label": 16,
        "tooltip": 16,
        "marker": 12,
        "line_width": 4,
        "margin": {"t": 70, "b": 70, "l": 70, "r": 50},
    },
}


def get_chart_theme(size: ChartSize = "medium") -> Dict[str, Any]:
    """
    Get responsive chart theme configuration based on size.

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
    scale = TYPOGRAPHY_SCALES.get(size, TYPOGRAPHY_SCALES["medium"])

    return {
        "title_font": dict(size=scale["title"], family="Arial", weight=600, color="#1D1D1F"),
        "axis_title_font": dict(size=scale["axis_title"], family="Arial", weight=600, color="#1D1D1F"),
        "axis_tick_font": dict(size=scale["axis_tick"], family="Arial", weight=500, color="#1D1D1F"),
        "legend_font": dict(size=scale["legend"], family="Arial", weight=500, color="#1D1D1F"),
        "revenue_label_font": dict(size=scale["revenue_label"], family="Arial", weight=600, color="#1D1D1F"),
        "growth_label_font": dict(size=scale["growth_label"], family="Arial", weight=500, color="#1D1D1F"),
        "tooltip_font": dict(size=scale["tooltip"], family="Arial", weight=500, color="#1D1D1F"),
        "marker_size": scale["marker"],
        "line_width": scale["line_width"],
        "margin": scale["margin"],
    }


def get_chart_height(size: ChartSize = "medium") -> int:
    """
    Get recommended chart height based on size.

    Args:
        size: Chart size - "small", "medium", "large", or "full"

    Returns:
        Recommended height in pixels
    """
    heights = {
        "small": 250,
        "medium": 350,
        "large": 420,
        "full": 500,
    }
    return heights.get(size, heights["medium"])


def get_growth_color(value: float) -> str:
    """
    Get semantic color for growth values.

    Args:
        value: Growth percentage value

    Returns:
        Color hex code - green for positive, red for negative
    """
    return "#34C759" if value >= 0 else "#FF3B30"


def get_marker_colors(values: list) -> list:
    """
    Get semantic colors for a list of growth values.

    Args:
        values: List of growth percentage values

    Returns:
        List of color hex codes
    """
    return [get_growth_color(v) for v in values]


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
