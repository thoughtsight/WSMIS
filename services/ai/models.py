"""
services.ai.models — Typed containers for the Audit Intelligence pipeline.

These are plain dataclasses used to keep the context JSON and the generated
report well-structured and JSON-serializable. No business logic lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────────────────────────────────
# Context (input to the LLM)
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class PeriodKPIs:
    """Headline KPIs for a single period, all values already calculated."""
    total_revenue: float = 0.0
    net_labour: float = 0.0
    net_parts: float = 0.0
    total_margin: float = 0.0
    parts_margin: float = 0.0
    total_discount: float = 0.0
    labour_discount: float = 0.0
    parts_discount: float = 0.0
    labour_discount_pct: float = 0.0
    overall_discount_pct: float = 0.0
    job_cards: float = 0.0
    revenue_per_jc: float = 0.0
    margin_per_jc: float = 0.0


@dataclass
class RankedEntity:
    """A location or advisor summary row (already aggregated)."""
    name: str
    net_labour: float = 0.0
    net_parts: float = 0.0
    total_margin: float = 0.0
    job_cards: float = 0.0
    labour_discount_pct: float = 0.0


@dataclass
class LeakageItem:
    """One recoverable-leakage row, already computed by utils.calculations.leakage."""
    entity: str
    scope: str                # "Labour" | "Parts"
    level: str                # "Location" | "Advisor"
    revenue: float = 0.0
    discount_rs: float = 0.0
    discount_pct: float = 0.0
    benchmark_pct: float = 0.0
    recoverable: float = 0.0


@dataclass
class RiskItem:
    title: str
    entity: str = "Group"
    impact: str = ""
    detail: str = ""
    recommended_action: str = ""


@dataclass
class OpportunityItem:
    title: str
    estimated_value: float = 0.0
    owner: str = ""
    detail: str = ""


@dataclass
class ReportContext:
    """The complete, JSON-serializable context handed to the prompt builder."""
    meta: Dict[str, Any] = field(default_factory=dict)
    current_period: PeriodKPIs = field(default_factory=PeriodKPIs)
    prior_period: PeriodKPIs = field(default_factory=PeriodKPIs)
    growth: Dict[str, float] = field(default_factory=dict)
    business_health: Dict[str, Any] = field(default_factory=dict)
    pnl: Dict[str, Any] = field(default_factory=dict)
    top_locations: List[RankedEntity] = field(default_factory=list)
    top_advisors: List[RankedEntity] = field(default_factory=list)
    leakage: List[LeakageItem] = field(default_factory=list)
    risks: List[RiskItem] = field(default_factory=list)
    opportunities: List[OpportunityItem] = field(default_factory=list)
    benchmarks: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────────
# Report (output from the LLM)
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class ReportSection:
    """A single section definition for the report template."""
    key: str
    number: int
    title: str
    guidance: str = ""

    def heading(self) -> str:
        return f"## {self.number}. {self.title}"


@dataclass
class GeneratedReport:
    """Final output of report_generator.generate_report()."""
    markdown: str
    provider: str
    model: str
    context: Dict[str, Any] = field(default_factory=dict)
    prompt: str = ""
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
