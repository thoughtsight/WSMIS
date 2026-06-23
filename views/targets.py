"""
Compatibility wrapper for Targets dashboard
Migrated to views/performance/targets.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.performance.targets import render
