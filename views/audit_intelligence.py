"""
Compatibility wrapper for Audit Intelligence dashboard
Migrated to views/operations/audit_intelligence.py in V2 architecture
This file maintains V1 compatibility by delegating to the new location
"""

from views.operations.audit_intelligence import render
