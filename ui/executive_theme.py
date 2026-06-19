"""
WSMIS Executive Design Foundation
Centralized design system for all WSMIS reports.

This module provides the ExecutiveTheme class that centralizes:
- Typography scales
- Colour palettes
- Semantic colours
- Legend styles
- Margins
- Hover styling
- Grid styling
- Marker sizing
- Bar radius
- Number formatting
- Indian formatting
- Responsive scaling

All WSMIS reports should consume this design system for consistent visual language.
"""

from typing import Literal, Dict, Any
from dataclasses import dataclass


# Chart size definitions
ChartSize = Literal["small", "medium", "large", "full"]


@dataclass
class ColourPalette:
    """Executive colour palette for WSMIS."""
    primary: str = "#0071E3"      # Blue - Current Period
    secondary: str = "#8E8E93"    # Grey - Previous Period
    success: str = "#34C759"      # Green - Positive Growth
    danger: str = "#FF3B30"       # Red - Negative Growth
    warning: str = "#FF9500"      # Orange - Warning
    info: str = "#5AC8FA"         # Cyan - Information
    purple: str = "#AF52DE"       # Purple - Accent
    pink: str = "#FF2D55"         # Pink - Accent
    gold: str = "#C8860A"         # Gold - Accent
    
    # Background colours
    background: str = "#FFFFFF"
    surface: str = "#F5F5F7"
    border: str = "#E5E5EA"
    
    # Text colours
    text_primary: str = "#1D1D1F"
    text_secondary: str = "#6E6E73"
    text_tertiary: str = "#8E8E93"


@dataclass
class TypographyScale:
    """Typography scale for a specific chart size."""
    title: int
    axis_title: int
    axis_tick: int
    legend: int
    revenue_label: int
    growth_label: int
    tooltip: int
    marker: int
    line_width: float
    margin: Dict[str, int]


class ExecutiveTheme:
    """
    Centralized executive design system for WSMIS.
    
    This class provides all design tokens and styling configurations
    for consistent visual language across all reports.
    """
    
    # Colour palette
    colours = ColourPalette()
    
    # Typography scales for different chart sizes
    _typography_scales = {
        "small": TypographyScale(
            title=16,
            axis_title=12,
            axis_tick=11,
            legend=11,
            revenue_label=12,
            growth_label=11,
            tooltip=12,
            marker=6,
            line_width=2,
            margin={"t": 40, "b": 40, "l": 48, "r": 24},
        ),
        "medium": TypographyScale(
            title=18,
            axis_title=14,
            axis_tick=12,
            legend=12,
            revenue_label=13,
            growth_label=12,
            tooltip=13,
            marker=8,
            line_width=2.5,
            margin={"t": 50, "b": 50, "l": 50, "r": 30},
        ),
        "large": TypographyScale(
            title=20,
            axis_title=16,
            axis_tick=13,
            legend=13,
            revenue_label=15,
            growth_label=14,
            tooltip=14,
            marker=10,
            line_width=3,
            margin={"t": 60, "b": 60, "l": 60, "r": 40},
        ),
        "full": TypographyScale(
            title=24,
            axis_title=18,
            axis_tick=15,
            legend=15,
            revenue_label=18,
            growth_label=16,
            tooltip=16,
            marker=12,
            line_width=4,
            margin={"t": 70, "b": 70, "l": 70, "r": 50},
        ),
    }
    
    # Chart heights
    _chart_heights = {
        "small": 250,
        "medium": 350,
        "large": 420,
        "full": 500,
    }
    
    # Font family
    font_family = "Arial"
    
    # Font weights
    font_weight_bold = 600
    font_weight_medium = 500
    font_weight_regular = 400
    
    # Bar radius
    bar_radius = 4
    
    # Grid styling
    grid_color = "#F0F0F5"
    grid_width = 1
    
    # Axis line styling
    axis_line_color = "#E5E5EA"
    axis_line_width = 1
    
    # Hover styling
    hover_bg_color = "#FFFFFF"
    hover_border_color = "#E5E5EA"
    hover_border_width = 1
    
    # Legend styling
    legend_bg_color = "rgba(255, 255, 255, 0.9)"
    legend_border_color = "#E5E5EA"
    legend_border_width = 1
    legend_orientation = "h"
    legend_y_position = 1.02
    legend_y_anchor = "bottom"
    
    @classmethod
    def get_typography_scale(cls, size: ChartSize = "medium") -> TypographyScale:
        """
        Get typography scale for a specific chart size.
        
        Args:
            size: Chart size - "small", "medium", "large", or "full"
        
        Returns:
            TypographyScale dataclass with all typography values
        """
        return cls._typography_scales.get(size, cls._typography_scales["medium"])
    
    @classmethod
    def get_chart_height(cls, size: ChartSize = "medium") -> int:
        """
        Get recommended chart height for a specific size.
        
        Args:
            size: Chart size - "small", "medium", "large", or "full"
        
        Returns:
            Recommended height in pixels
        """
        return cls._chart_heights.get(size, cls._chart_heights["medium"])
    
    @classmethod
    def get_growth_color(cls, value: float) -> str:
        """
        Get semantic color for growth values.
        
        Args:
            value: Growth percentage value
        
        Returns:
            Color hex code - green for positive, red for negative
        """
        return cls.colours.success if value >= 0 else cls.colours.danger
    
    @classmethod
    def get_marker_colors(cls, values: list) -> list:
        """
        Get semantic colors for a list of growth values.
        
        Args:
            values: List of growth percentage values
        
        Returns:
            List of color hex codes
        """
        return [cls.get_growth_color(v) for v in values]
    
    @classmethod
    def get_title_font(cls, size: ChartSize = "medium") -> Dict[str, Any]:
        """
        Get title font configuration.
        
        Args:
            size: Chart size
        
        Returns:
            Font configuration dictionary
        """
        scale = cls.get_typography_scale(size)
        return {
            "size": scale.title,
            "family": cls.font_family,
            "weight": cls.font_weight_bold,
            "color": cls.colours.text_primary,
        }
    
    @classmethod
    def get_axis_title_font(cls, size: ChartSize = "medium") -> Dict[str, Any]:
        """
        Get axis title font configuration.
        
        Args:
            size: Chart size
        
        Returns:
            Font configuration dictionary
        """
        scale = cls.get_typography_scale(size)
        return {
            "size": scale.axis_title,
            "family": cls.font_family,
            "weight": cls.font_weight_bold,
            "color": cls.colours.text_primary,
        }
    
    @classmethod
    def get_axis_tick_font(cls, size: ChartSize = "medium") -> Dict[str, Any]:
        """
        Get axis tick font configuration.
        
        Args:
            size: Chart size
        
        Returns:
            Font configuration dictionary
        """
        scale = cls.get_typography_scale(size)
        return {
            "size": scale.axis_tick,
            "family": cls.font_family,
            "weight": cls.font_weight_medium,
            "color": cls.colours.text_primary,
        }
    
    @classmethod
    def get_legend_font(cls, size: ChartSize = "medium") -> Dict[str, Any]:
        """
        Get legend font configuration.
        
        Args:
            size: Chart size
        
        Returns:
            Font configuration dictionary
        """
        scale = cls.get_typography_scale(size)
        return {
            "size": scale.legend,
            "family": cls.font_family,
            "weight": cls.font_weight_medium,
            "color": cls.colours.text_primary,
        }
    
    @classmethod
    def get_revenue_label_font(cls, size: ChartSize = "medium") -> Dict[str, Any]:
        """
        Get revenue label font configuration.
        
        Args:
            size: Chart size
        
        Returns:
            Font configuration dictionary
        """
        scale = cls.get_typography_scale(size)
        return {
            "size": scale.revenue_label,
            "family": cls.font_family,
            "weight": cls.font_weight_bold,
            "color": cls.colours.text_primary,
        }
    
    @classmethod
    def get_growth_label_font(cls, size: ChartSize = "medium") -> Dict[str, Any]:
        """
        Get growth label font configuration.
        
        Args:
            size: Chart size
        
        Returns:
            Font configuration dictionary
        """
        scale = cls.get_typography_scale(size)
        return {
            "size": scale.growth_label,
            "family": cls.font_family,
            "weight": cls.font_weight_medium,
            "color": cls.colours.text_primary,
        }
    
    @classmethod
    def get_tooltip_font(cls, size: ChartSize = "medium") -> Dict[str, Any]:
        """
        Get tooltip font configuration.
        
        Args:
            size: Chart size
        
        Returns:
            Font configuration dictionary
        """
        scale = cls.get_typography_scale(size)
        return {
            "size": scale.tooltip,
            "family": cls.font_family,
            "weight": cls.font_weight_medium,
            "color": cls.colours.text_primary,
        }
    
    @classmethod
    def get_margin(cls, size: ChartSize = "medium") -> Dict[str, int]:
        """
        Get chart margin configuration.
        
        Args:
            size: Chart size
        
        Returns:
            Margin dictionary
        """
        scale = cls.get_typography_scale(size)
        return scale.margin
    
    @classmethod
    def get_marker_size(cls, size: ChartSize = "medium") -> int:
        """
        Get marker size for a specific chart size.
        
        Args:
            size: Chart size
        
        Returns:
            Marker size in pixels
        """
        scale = cls.get_typography_scale(size)
        return scale.marker
    
    @classmethod
    def get_line_width(cls, size: ChartSize = "medium") -> float:
        """
        Get line width for a specific chart size.
        
        Args:
            size: Chart size
        
        Returns:
            Line width in pixels
        """
        scale = cls.get_typography_scale(size)
        return scale.line_width


class ExecutiveChart:
    """
    Chart-specific styling using ExecutiveTheme.
    
    This class provides chart-specific styling configurations
    that consume the ExecutiveTheme design tokens.
    """
    
    @staticmethod
    def get_theme(size: ChartSize = "medium") -> Dict[str, Any]:
        """
        Get complete chart theme configuration.
        
        Args:
            size: Chart size - "small", "medium", "large", or "full"
        
        Returns:
            Dictionary with all chart styling configurations
        """
        return {
            "title_font": ExecutiveTheme.get_title_font(size),
            "axis_title_font": ExecutiveTheme.get_axis_title_font(size),
            "axis_tick_font": ExecutiveTheme.get_axis_tick_font(size),
            "legend_font": ExecutiveTheme.get_legend_font(size),
            "revenue_label_font": ExecutiveTheme.get_revenue_label_font(size),
            "growth_label_font": ExecutiveTheme.get_growth_label_font(size),
            "tooltip_font": ExecutiveTheme.get_tooltip_font(size),
            "marker_size": ExecutiveTheme.get_marker_size(size),
            "line_width": ExecutiveTheme.get_line_width(size),
            "margin": ExecutiveTheme.get_margin(size),
            "height": ExecutiveTheme.get_chart_height(size),
        }
    
    @staticmethod
    def get_grid_config() -> Dict[str, Any]:
        """
        Get grid configuration.
        
        Returns:
            Grid styling dictionary
        """
        return {
            "gridcolor": ExecutiveTheme.grid_color,
            "gridwidth": ExecutiveTheme.grid_width,
        }
    
    @staticmethod
    def get_axis_config() -> Dict[str, Any]:
        """
        Get axis line configuration.
        
        Returns:
            Axis line styling dictionary
        """
        return {
            "linecolor": ExecutiveTheme.axis_line_color,
            "linewidth": ExecutiveTheme.axis_line_width,
        }
    
    @staticmethod
    def get_hover_config() -> Dict[str, Any]:
        """
        Get hover tooltip configuration.
        
        Returns:
            Hover styling dictionary
        """
        return {
            "bgcolor": ExecutiveTheme.hover_bg_color,
            "bordercolor": ExecutiveTheme.hover_border_color,
            "borderwidth": ExecutiveTheme.hover_border_width,
        }
    
    @staticmethod
    def get_legend_config(size: ChartSize = "medium") -> Dict[str, Any]:
        """
        Get legend configuration.
        
        Args:
            size: Chart size
        
        Returns:
            Legend styling dictionary
        """
        return {
            "font": ExecutiveTheme.get_legend_font(size),
            "bgcolor": ExecutiveTheme.legend_bg_color,
            "bordercolor": ExecutiveTheme.legend_border_color,
            "borderwidth": ExecutiveTheme.legend_border_width,
            "orientation": ExecutiveTheme.legend_orientation,
            "y": ExecutiveTheme.legend_y_position,
            "yanchor": ExecutiveTheme.legend_y_anchor,
        }
