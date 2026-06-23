"""
Compatibility wrapper for Expense dashboard
Migrated to views/financial/expense.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.financial.expense import render
