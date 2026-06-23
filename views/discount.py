"""
Compatibility wrapper for Discounts dashboard
Migrated to views/commercial/discount.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.commercial.discount import render
