"""
Financial Dashboard Module
V2 Architecture - P&L, Expense dashboards
Version: 1.0.0
"""

from .pnl import render as render_pnl
from .expense import render as render_expense

__all__ = ['render_pnl', 'render_expense']
