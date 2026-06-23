"""
Compatibility wrapper for Advisor MoM dashboard
Migrated to views/operations/advisor_mom.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.operations.advisor_mom import render
