"""
Compatibility wrapper for Internal Audit dashboard
Migrated to views/operations/internal_audit.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.operations.internal_audit import render
