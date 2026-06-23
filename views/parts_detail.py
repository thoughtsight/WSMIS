"""
Compatibility wrapper for Parts Detail dashboard
Migrated to views/commercial/parts_detail.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.commercial.parts_detail import render
