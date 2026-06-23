"""
Trend Dashboard Module
V2 Architecture - Trends dashboard
Version: 1.0.0
"""

from .trends import render as render_trends

# Backward compatibility: export 'render' as alias for render_trends
# This maintains compatibility with existing imports in app.py
render = render_trends

__all__ = ['render_trends', 'render']
