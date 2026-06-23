"""
WSMIS UI Components Library v2.0 — Executive Light
Enforces consistent layout, typography and UX across all reports.
"""
from .core import UniversalHeader, UniversalFooter, EmptyState, AlertBanner
from .metrics import MetricCard, KPIGrid
from .tables import TableCard

__all__ = [
    # Header / Footer
    "UniversalHeader",
    "UniversalFooter",
    # Feedback
    "EmptyState",
    "AlertBanner",
    # KPI
    "MetricCard",
    "KPIGrid",
    # Tables
    "TableCard",
]
