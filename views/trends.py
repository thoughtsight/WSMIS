"""
Compatibility wrapper for Trends dashboard
Migrated to views/trend/trends.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.trend.trends import render
