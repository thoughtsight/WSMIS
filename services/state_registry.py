"""
State Registry - Central registration of dashboard namespaces

Registers all dashboard namespaces with their defaults.
This module should be imported at app startup to initialize StateManager.
"""

from services.state_manager import StateManager, NamespaceConfig


def register_all_namespaces():
    """Register all dashboard namespaces with StateManager."""
    
    # Labour Dashboard
    StateManager.register_namespace(NamespaceConfig(
        prefix="lab_",
        defaults={
            "business_view": "All",
            "cross_month": None,
        },
        description="Labour Revenue Dashboard"
    ))
    
    # Parts Executive Dashboard
    StateManager.register_namespace(NamespaceConfig(
        prefix="parts_",
        defaults={
            "cross_month": None,
            "drill_location": None,
            "drill_category": None,
            "drill_from_page": None,
        },
        description="Parts Revenue Dashboard"
    ))
    
    # Cockpit Dashboard
    StateManager.register_namespace(NamespaceConfig(
        prefix="cockpit_",
        defaults={
            "alert_tab": "critical",
        },
        description="Executive Cockpit Dashboard"
    ))
    
    # Additional dashboards can be registered here as needed
    # Example:
    # StateManager.register_namespace(NamespaceConfig(
    #     prefix="expense_",
    #     defaults={},
    #     description="Expense Dashboard"
    # ))


# Auto-register on import
register_all_namespaces()
