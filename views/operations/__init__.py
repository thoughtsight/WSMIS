"""
Operations Dashboard Module
V2 Architecture - Advisor, Advisor MoM, Internal Audit, Audit Intelligence, Reports dashboards
Version: 1.0.0
"""

from .advisor import render as render_advisor
from .advisor_mom import render as render_advisor_mom
from .internal_audit import render as render_internal_audit
from .audit_intelligence import render as render_audit_intelligence
from .reports import render as render_reports

__all__ = ['render_advisor', 'render_advisor_mom', 'render_internal_audit', 'render_audit_intelligence', 'render_reports']
