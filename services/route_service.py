"""
WSMIS Route Service
Route Registry, Validation, and Navigation
Version: 2.0.0
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class AppContext:
    """Immutable application context containing ephemeral state for the active page."""
    df_filtered_full: pd.DataFrame
    df_filtered_cp: pd.DataFrame
    df_filtered: pd.DataFrame
    pairs: list
    alerts: list
    comparison_mode: bool
    selected_months: list
    targets_df: pd.DataFrame
    client_config: dict
    exp_df_filtered_cp: pd.DataFrame


class RouteRegistry:
    """Central registry for all application routes supporting st.navigation."""
    
    @staticmethod
    def _wrap_cockpit():
        ctx: AppContext = st.session_state.app_context
        from views.cockpit import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.pairs, ctx.alerts, ctx.comparison_mode, ctx.selected_months, ctx=ctx)

    @staticmethod
    def _wrap_overview():
        ctx: AppContext = st.session_state.app_context
        from views.overview import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.pairs, ctx.alerts, ctx.comparison_mode, ctx.selected_months, ctx=ctx)

    @staticmethod
    def _wrap_executive():
        with st.status("📊 Building executive summary...", expanded=False) as _s:
            ctx: AppContext = st.session_state.app_context
            from views.executive import render
            from app import safe_render
            # NOTE: ctx.alerts MUST be the third positional arg to match render() signature.
            # Previously missing ctx.alerts caused comparison_mode and selected_months to shift.
            safe_render(render, ctx.df_filtered_full, ctx.pairs, ctx.alerts, ctx.comparison_mode, ctx.selected_months, ctx=ctx)
            _s.update(label="Executive summary ready", state="complete", expanded=False)

    @staticmethod
    def _wrap_margin():
        ctx: AppContext = st.session_state.app_context
        from views.margin import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_cp, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_discounts():
        ctx: AppContext = st.session_state.app_context
        from views.discount import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_cp, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_sales_mix():
        ctx: AppContext = st.session_state.app_context
        from views.sales_mix import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_cp, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_labour():
        ctx: AppContext = st.session_state.app_context
        from views.labour import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_parts_executive():
        ctx: AppContext = st.session_state.app_context
        from views.parts_executive import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.targets_df, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_parts_detail():
        ctx: AppContext = st.session_state.app_context
        from views.parts_detail import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_leakage_center():
        ctx: AppContext = st.session_state.app_context
        from views.leakage import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_advisors():
        ctx: AppContext = st.session_state.app_context
        from views.advisor import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_cp, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_advisor_mom():
        ctx: AppContext = st.session_state.app_context
        from views.advisor_mom import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_locations():
        ctx: AppContext = st.session_state.app_context
        from views.locations import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_cp, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_trends():
        ctx: AppContext = st.session_state.app_context
        from views.trends import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.pairs, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_targets():
        ctx: AppContext = st.session_state.app_context
        from views.targets import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_cp, ctx.targets_df, ctx.pairs)

    @staticmethod
    def _wrap_reports():
        with st.status("📄 Generating reports...", expanded=False) as _s:
            ctx: AppContext = st.session_state.app_context
            from views.reports import render
            from app import safe_render
            safe_render(render, ctx.df_filtered_cp, ctx.pairs, ctx.comparison_mode, ctx.selected_months)
            _s.update(label="Reports ready", state="complete", expanded=False)

    @staticmethod
    def _wrap_expense_analysis():
        ctx: AppContext = st.session_state.app_context
        from views.expense import render
        from app import safe_render
        safe_render(render, ctx.exp_df_filtered_cp, ctx.selected_months)

    @staticmethod
    def _wrap_profit_and_loss():
        ctx: AppContext = st.session_state.app_context
        from views.pnl import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_cp, ctx.exp_df_filtered_cp, ctx.selected_months)

    @staticmethod
    def _wrap_internal_audit():
        with st.status("🔍 Running audit analysis...", expanded=False) as _s:
            st.caption("⏳ Exception scan · Leakage detection · Risk register")
            ctx: AppContext = st.session_state.app_context
            from views.internal_audit import render
            from app import safe_render
            safe_render(render, ctx.df_filtered, ctx.client_config, cp=ctx.df_filtered_cp)
            _s.update(label="Audit analysis complete", state="complete", expanded=False)

    @staticmethod
    def _wrap_audit_intelligence():
        ctx: AppContext = st.session_state.app_context
        from views.audit_intelligence import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.pairs, ctx.alerts, ctx.comparison_mode, ctx.selected_months)

    @staticmethod
    def _wrap_system_health():
        ctx: AppContext = st.session_state.app_context
        from views.system_health import render
        from app import safe_render
        safe_render(render, ctx.df_filtered_full, ctx.exp_df_filtered_cp)

    def __init__(self):
        # We store the base st.Page definitions here.
        # URL paths must match the old legacy slugs where possible to preserve bookmarks.
        self.pages = {
            "Executive": [
                st.Page(self._wrap_cockpit, title="Cockpit", url_path="cockpit", icon="📊"),
            ],
            "Commercial": [
                st.Page(self._wrap_margin, title="Margin", url_path="margin", icon="💰"),
                st.Page(self._wrap_discounts, title="Discounts", url_path="discounts", icon="🏷️"),
            ],
            "Operations": [
                st.Page(self._wrap_labour, title="Labour", url_path="labour", icon="🔧"),
                st.Page(self._wrap_parts_executive, title="Parts Executive", url_path="parts-executive", icon="⚙️"),
                st.Page(self._wrap_parts_detail, title="Parts Detail", url_path="parts-detail", icon="📦"),
                st.Page(self._wrap_sales_mix, title="Sales Mix", url_path="sales-mix", icon="📊"),
                st.Page(self._wrap_advisors, title="Advisors", url_path="advisors", icon="👔"),
                st.Page(self._wrap_advisor_mom, title="Advisor MoM", url_path="advisor-mom", icon="📅"),
                st.Page(self._wrap_locations, title="Locations", url_path="locations", icon="📍"),
            ],
            "Performance": [
                st.Page(self._wrap_trends, title="Trends", url_path="trends", icon="📈"),
                st.Page(self._wrap_targets, title="Targets", url_path="targets", icon="🎯"),
                st.Page(self._wrap_reports, title="Reports", url_path="reports", icon="📄"),
            ],
            "Finance": [
                st.Page(self._wrap_expense_analysis, title="Expense Analysis", url_path="expense-analysis", icon="💸"),
                st.Page(self._wrap_profit_and_loss, title="Profit & Loss", url_path="profit-and-loss", icon="⚖️"),
            ],
            "Audit": [
                st.Page(self._wrap_internal_audit, title="Internal Audit", url_path="internal-audit", icon="🔍"),
                st.Page(self._wrap_audit_intelligence, title="Audit Intelligence", url_path="audit-intelligence", icon="🧠"),
                st.Page(self._wrap_leakage_center, title="Leakage Center", url_path="leakage-centre", icon="💧"),
            ],
            "Administration": [
                st.Page(self._wrap_system_health, title="System Health", url_path="system-health", icon="🖥️"),
            ]
        }
        
        # Flat lookup dictionary for easy resolution by title
        self.pages_by_title = {}
        for category, page_list in self.pages.items():
            for page in page_list:
                self.pages_by_title[page.title] = page

    def get_blueprint_pages(self, user_role: str = "admin") -> Dict[str, List[st.Page]]:
        """
        Returns the dictionary of pages categorized by the blueprint.
        Future RBAC logic can be implemented here by filtering the lists.
        """
        return self.pages

    def get_page_by_title(self, title: str) -> Optional[st.Page]:
        """Returns the st.Page object for a given exact title string."""
        return self.pages_by_title.get(title)


class RouteService:
    """Main service for route management and navigation."""
    
    def __init__(self):
        self.registry = RouteRegistry()
    
    def get_registry(self) -> RouteRegistry:
        """Get the route registry."""
        return self.registry
    
    def sync_url_to_session(self):
        """Legacy stub to prevent breakages during migration."""
        pass
    
    def sync_session_to_url(self):
        """Legacy stub to prevent breakages during migration."""
        pass


# Global route service instance
_route_service = None

def get_route_service() -> RouteService:
    """Get or create the global route service instance."""
    global _route_service
    if _route_service is None:
        _route_service = RouteService()
    return _route_service
