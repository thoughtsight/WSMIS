"""
WSMIS Executive Chart Design System
Global responsive chart theme for all WSMIS reports.

This module provides responsive typography and styling that scales
intelligently based on chart size (small, medium, large, full-width).

This module uses design tokens for centralized visual language.
"""

import plotly.graph_objects as go
import plotly.io as pio
from typing import Literal, Dict, Any
from ui.design_tokens import T

ChartSize = Literal["small", "medium", "large", "full"]

def get_chart_theme(size: ChartSize = "medium") -> Dict[str, Any]:
    """
    Get responsive chart theme configuration based on size.
    """
    sizes = {
        "small":  {"title": 14, "tick": 11, "label": 11, "legend": 11, "margin": dict(l=48, r=20, t=40, b=40)},
        "medium": {"title": 16, "tick": 12, "label": 12, "legend": 12, "margin": dict(l=52, r=24, t=52, b=44)},
        "large":  {"title": 18, "tick": 13, "label": 13, "legend": 13, "margin": dict(l=60, r=32, t=60, b=52)},
        "full":   {"title": 22, "tick": 14, "label": 14, "legend": 14, "margin": dict(l=72, r=40, t=72, b=60)},
    }
    s = sizes.get(size, sizes["medium"])
    font_stack = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
    return {
        "title_font": dict(size=s["title"], family=font_stack, color=T.COLOR_TEXT_PRIMARY, weight=700),
        "axis_title_font": dict(size=s["tick"] + 1, family=font_stack, color=T.COLOR_TEXT_SECONDARY),
        "axis_tick_font": dict(size=s["tick"], family=font_stack, color=T.COLOR_TEXT_SECONDARY),
        "legend_font": dict(size=s["legend"], family=font_stack, color=T.COLOR_TEXT_SECONDARY),
        "revenue_label_font": dict(size=s["label"], family=font_stack, color=T.COLOR_TEXT_PRIMARY),
        "growth_label_font": dict(size=s["label"], family=font_stack, color=T.COLOR_TEXT_PRIMARY),
        "tooltip_font": dict(size=13, family=font_stack),
        "margin": s["margin"]
    }

def get_chart_height(size: ChartSize = "medium") -> int:
    """
    Get recommended chart height based on size.
    """
    heights = {
        "small": 280,
        "medium": 360,
        "large": 420,
        "full": 500
    }
    return heights.get(size, 360)

def get_growth_color(value: float) -> str:
    """
    Get semantic color for growth values (for fills).
    """
    return T.COLOR_SUCCESS_FILL if value >= 0 else T.COLOR_DANGER_FILL

def get_marker_colors(values: list) -> list:
    """
    Get semantic colors for a list of growth values.
    """
    return [get_growth_color(v) for v in values]



def apply_wsmis_theme():
    """
    Registers and applies the standard WSMIS Enterprise Plotly theme.
    """
    wsmis_template = go.layout.Template()

    # Base layout
    wsmis_template.layout = go.Layout(
        font=dict(family=T.FONT_FAMILY, color=T.COLOR_TEXT_PRIMARY),
        title=dict(font=dict(size=16, color=T.COLOR_TEXT_PRIMARY, weight="bold")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=20),
        hoverlabel=dict(
            bgcolor=T.COLOR_SURFACE,
            font_size=13,
            font_family=T.FONT_FAMILY,
            bordercolor=T.COLOR_BORDER
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color=T.COLOR_TEXT_SECONDARY)
        ),
        colorway=[
            T.COLOR_PRIMARY,
            T.COLOR_SUCCESS_FILL,
            T.COLOR_WARNING,
            T.COLOR_DANGER_FILL,
            "#5856D6", # Purple fallback
            "#30B0C7"  # Cyan fallback
        ]
    )

    # Axes
    wsmis_template.layout.xaxis = dict(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=T.COLOR_BORDER,
        tickfont=dict(color=T.COLOR_TEXT_SECONDARY, size=11)
    )

    wsmis_template.layout.yaxis = dict(
        showgrid=True,
        gridcolor=T.COLOR_SURFACE2,
        zeroline=True,
        zerolinecolor=T.COLOR_BORDER,
        showline=False,
        tickfont=dict(color=T.COLOR_TEXT_SECONDARY, size=11)
    )

    pio.templates["wsmis"] = wsmis_template
    pio.templates.default = "wsmis"
