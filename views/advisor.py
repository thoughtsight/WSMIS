"""
Compatibility wrapper for Advisor dashboard
Migrated to views/operations/advisor.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.operations.advisor import render
