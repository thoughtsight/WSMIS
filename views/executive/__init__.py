"""
Executive Dashboard Module
V2 Architecture - Unified Executive Command Center
Version: 2.0.0
"""

from .cockpit import render_cockpit, render as render_cockpit_alias
from .overview import render_overview, render as render_overview_alias
from .executive import render_executive, render as render_executive_alias
from .command_center import render

# Backward compatibility: export 'render' as alias for command center render
# This maintains compatibility with existing imports in app.py if any

__all__ = ['render_cockpit', 'render_overview', 'render_executive', 'render']
