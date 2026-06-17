"""
services.ai — Audit Intelligence Report Infrastructure (PR-025)

This package builds the *reporting* layer only. It does NOT contain business
calculations, KPIs, or dashboard code. It strictly CONSUMES already-calculated
values exposed by WSMIS (FinancialService, utils.calculations, utils.aggregations)
and turns them into:

    context (JSON)  ->  prompt  ->  LLM  ->  Markdown report

Public API
----------
    build_context(...)        -> dict          (context_builder)
    build_prompt(context)     -> str           (prompt_builder)
    generate_report(...)      -> GeneratedReport(report_generator)

Nothing here is wired into any existing page. WSMIS is feature-frozen; this is
purely additive infrastructure ready for a future Gemini-backed report page.
"""

from services.ai.context_builder import build_context
from services.ai.prompt_builder import build_prompt
from services.ai.report_generator import generate_report, AVAILABLE_PROVIDERS
from services.ai.models import (
    ReportContext, PeriodKPIs, LeakageItem, RankedEntity,
    RiskItem, OpportunityItem, ReportSection, GeneratedReport,
)

__all__ = [
    "build_context",
    "build_prompt",
    "generate_report",
    "AVAILABLE_PROVIDERS",
    "ReportContext",
    "PeriodKPIs",
    "LeakageItem",
    "RankedEntity",
    "RiskItem",
    "OpportunityItem",
    "ReportSection",
    "GeneratedReport",
]
