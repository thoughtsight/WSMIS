"""
Compatibility wrapper for Locations dashboard
Migrated to views/performance/locations.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.performance.locations import render
