"""
Performance Dashboard Module
V2 Architecture - Locations, Targets dashboards (branch comparison, rankings, target achievement)
Version: 1.0.0
"""

from .locations import render as render_locations
from .targets import render as render_targets

__all__ = ['render_locations', 'render_targets']
