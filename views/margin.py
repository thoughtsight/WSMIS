"""
Compatibility wrapper for Margin dashboard
Migrated to views/commercial/margin.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.commercial.margin import render
