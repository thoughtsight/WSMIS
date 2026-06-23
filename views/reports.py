"""
Compatibility wrapper for Reports dashboard
Migrated to views/operations/reports.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.operations.reports import render
