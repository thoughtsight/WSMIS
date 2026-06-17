"""
services.ai.templates — Report section definitions for the Audit Intelligence Report.

This is configuration only: the ordered list of sections, their titles, and the
guidance the LLM should follow for each. No business logic, no calculations.
"""

from __future__ import annotations

from typing import List

from services.ai.models import ReportSection


# The 9 canonical sections of the Audit Intelligence Report, in order.
REPORT_SECTIONS: List[ReportSection] = [
    ReportSection(
        key="executive_summary",
        number=1,
        title="Executive Summary",
        guidance=(
            "3-5 sentences for a CEO. State overall business health, the single "
            "most important win, and the single most important concern this period. "
            "Use the Business Health Score if present."
        ),
    ),
    ReportSection(
        key="business_performance",
        number=2,
        title="Business Performance",
        guidance=(
            "Summarise revenue, margin, job cards and discount % for the current "
            "period vs the prior period. Quote the growth figures provided. Do not "
            "invent numbers; only use values present in the context."
        ),
    ),
    ReportSection(
        key="profit_drivers",
        number=3,
        title="Profit Drivers",
        guidance=(
            "Identify what is driving margin positively (e.g. top locations / "
            "advisors by margin, parts margin contribution). Reference the ranked "
            "entities provided."
        ),
    ),
    ReportSection(
        key="loss_drivers",
        number=4,
        title="Loss Drivers",
        guidance=(
            "Identify what is eroding profit (high discounting, YoY declines, "
            "elevated VOR charges). Reference the risks list and leakage data."
        ),
    ),
    ReportSection(
        key="revenue_leakage",
        number=5,
        title="Revenue Leakage",
        guidance=(
            "Summarise recoverable leakage above benchmark by location and advisor. "
            "Quote the recoverable amounts and discount % vs benchmark from the "
            "leakage list. Total the recoverable figures already provided."
        ),
    ),
    ReportSection(
        key="top_risks",
        number=6,
        title="Top Risks",
        guidance=(
            "List the highest-priority risks from the risks array, each with its "
            "entity, quantified impact and why it matters."
        ),
    ),
    ReportSection(
        key="top_opportunities",
        number=7,
        title="Top Opportunities",
        guidance=(
            "List the opportunities from the opportunities array with their "
            "estimated value and accountable owner."
        ),
    ),
    ReportSection(
        key="priority_actions",
        number=8,
        title="Priority Actions",
        guidance=(
            "Produce a numbered, prioritised action list (max 5). Each action must "
            "map to a risk or opportunity above and name an owner. Be specific and "
            "actionable; do not restate generic advice."
        ),
    ),
    ReportSection(
        key="financial_recovery",
        number=9,
        title="Estimated Financial Recovery",
        guidance=(
            "Give a single consolidated recovery estimate by summing the recoverable "
            "leakage and opportunity values already present in the context. Present "
            "as a short table: Source | Estimated Recovery (₹). Add a one-line "
            "disclaimer that figures are indicative, based on benchmark gaps."
        ),
    ),
]


def section_skeleton() -> str:
    """Return a Markdown skeleton of all sections (used by the offline provider)."""
    lines = []
    for s in REPORT_SECTIONS:
        lines.append(s.heading())
        lines.append("")
        lines.append(f"_{s.guidance}_")
        lines.append("")
    return "\n".join(lines).strip()
