"""
Compatibility wrapper for P&L dashboard
Migrated to views/financial/pnl.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.financial.pnl import render
