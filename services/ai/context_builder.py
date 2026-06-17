"""
services.ai.context_builder — Collects ALREADY-CALCULATED WSMIS values into a
single clean, JSON-serializable context object.

IMPORTANT
---------
This module performs NO new business calculations and defines NO new KPIs. It is
a pure *collector / shaper* that calls the existing WSMIS calculation surface:

    - services.financial_service.FinancialService
    - utils.calculations.* (revenue, margin, discount, leakage, fact_metrics)
    - utils.aggregations.* (location_summary, advisor_summary)

Aggregations used here (location/advisor summaries, leakage tables) are the
canonical WSMIS summaries the dashboards already display — collecting them is
explicitly part of the report context ("Location Summary", "Advisor Summary",
"Revenue Leakage"). Richer, page-specific artefacts (Business Health Score,
Top Risks, Top Opportunities, P&L) are computed inside frozen pages, so they are
accepted here as OPTIONAL injected inputs. When not injected, sensible defaults
are derived purely by *selecting/ranking* existing computed columns.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from utils.calculations.revenue import (
    calculate_net_revenue, calculate_revenue_per_jobcard, calculate_revenue_growth,
)
from utils.calculations.margin import (
    calculate_total_margin, calculate_parts_margin, calculate_margin_per_jobcard,
    calculate_margin_growth,
)
from utils.calculations.discount import (
    calculate_total_discount, calculate_labour_discount, calculate_parts_discount,
    calculate_labour_discount_pct, calculate_overall_discount_pct,
)
from utils.calculations.fact_metrics import get_net_labour, get_net_parts, get_jobcard_count
from utils.calculations.leakage import compute_discount_aggregates, compute_parts_leakage
from utils.aggregations import location_summary, advisor_summary
from config.settings import LABOUR_DISC_BENCH, PARTS_DISC_BENCH

from services.ai.models import (
    ReportContext, PeriodKPIs, RankedEntity, LeakageItem, RiskItem, OpportunityItem,
)


# ──────────────────────────────────────────────────────────────────────────
# Serialization helpers (numpy/pandas -> native python)
# ──────────────────────────────────────────────────────────────────────────

def _py(value: Any) -> Any:
    """Coerce numpy / pandas scalars to JSON-safe native python types."""
    if value is None:
        return None
    if isinstance(value, (np.floating, np.integer)):
        value = value.item()
    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            return 0.0
        return round(value, 2)
    return value


def _f(value: Any) -> float:
    try:
        v = float(value)
        return 0.0 if (np.isnan(v) or np.isinf(v)) else round(v, 2)
    except (TypeError, ValueError):
        return 0.0


# ──────────────────────────────────────────────────────────────────────────
# Period KPIs (reads existing calculation functions only)
# ──────────────────────────────────────────────────────────────────────────

def _period_kpis(df: pd.DataFrame) -> PeriodKPIs:
    if df is None or df.empty:
        return PeriodKPIs()
    return PeriodKPIs(
        total_revenue=_f(calculate_net_revenue(df)),
        net_labour=_f(get_net_labour(df)),
        net_parts=_f(get_net_parts(df)),
        total_margin=_f(calculate_total_margin(df)),
        parts_margin=_f(calculate_parts_margin(df)),
        total_discount=_f(calculate_total_discount(df)),
        labour_discount=_f(calculate_labour_discount(df)),
        parts_discount=_f(calculate_parts_discount(df)),
        labour_discount_pct=_f(calculate_labour_discount_pct(df)),
        overall_discount_pct=_f(calculate_overall_discount_pct(df)),
        job_cards=_f(get_jobcard_count(df)),
        revenue_per_jc=_f(calculate_revenue_per_jobcard(df)),
        margin_per_jc=_f(calculate_margin_per_jobcard(df)),
    )


# ──────────────────────────────────────────────────────────────────────────
# Ranked entity summaries (canonical WSMIS aggregations)
# ──────────────────────────────────────────────────────────────────────────

def _ranked_entities(df: pd.DataFrame, level: str, group_col: str, top: int) -> List[RankedEntity]:
    if df is None or df.empty or group_col not in df.columns:
        return []

    if level == "Location":
        summ = location_summary(df, loc_col=group_col, as_index=False).agg(
            NL=("Net_Labour", "sum"), NP=("Net_Parts", "sum"),
            MAR=("Total Margin", "sum"), JC=("JC_Nos.", "sum"),
            PRE=("Pre-GST Labour", "sum"), DISC=("Labour Discount", "sum"),
        )
    else:
        summ = advisor_summary(df, adv_col=group_col, as_index=False).agg(
            NL=("Net_Labour", "sum"), NP=("Net_Parts", "sum"),
            MAR=("Total Margin", "sum"), JC=("JC_Nos.", "sum"),
            PRE=("Pre-GST Labour", "sum"), DISC=("Labour Discount", "sum"),
        )

    if summ.empty:
        return []

    summ["DPCT"] = np.where(summ["PRE"] > 0, summ["DISC"] / summ["PRE"] * 100, 0.0)
    summ = summ.sort_values("MAR", ascending=False).head(top)

    out: List[RankedEntity] = []
    for _, r in summ.iterrows():
        out.append(RankedEntity(
            name=str(r[group_col]),
            net_labour=_f(r["NL"]),
            net_parts=_f(r["NP"]),
            total_margin=_f(r["MAR"]),
            job_cards=_f(r["JC"]),
            labour_discount_pct=_f(r["DPCT"]),
        ))
    return out


# ──────────────────────────────────────────────────────────────────────────
# Leakage (existing utils.calculations.leakage functions)
# ──────────────────────────────────────────────────────────────────────────

def _leakage_items(df: pd.DataFrame, adv_col: str, top: int) -> List[LeakageItem]:
    items: List[LeakageItem] = []
    if df is None or df.empty:
        return items

    specs = [
        ("Labour", "Location", "Location Name", LABOUR_DISC_BENCH, compute_discount_aggregates),
        ("Parts", "Location", "Location Name", PARTS_DISC_BENCH, compute_parts_leakage),
        ("Labour", "Advisor", adv_col, LABOUR_DISC_BENCH, compute_discount_aggregates),
    ]

    for scope, level, col, bench, fn in specs:
        if col not in df.columns:
            continue
        g = fn(df, col, bench)
        if g is None or g.empty or "Recoverable" not in g.columns:
            continue
        g = g[g["Recoverable"] > 0].sort_values("Recoverable", ascending=False).head(top)
        for _, r in g.iterrows():
            items.append(LeakageItem(
                entity=str(r[col]),
                scope=scope,
                level=level,
                revenue=_f(r.get("Revenue", 0.0)),
                discount_rs=_f(r.get("DiscRs", 0.0)),
                discount_pct=_f(r.get("Disc_Pct", 0.0)),
                benchmark_pct=_f(bench),
                recoverable=_f(r.get("Recoverable", 0.0)),
            ))
    return items


def _default_risks(leakage: List[LeakageItem]) -> List[RiskItem]:
    """Derive risks purely by selecting top recoverable leakage (no new math)."""
    risks: List[RiskItem] = []
    for item in sorted(leakage, key=lambda x: x.recoverable, reverse=True)[:3]:
        risks.append(RiskItem(
            title=f"High {item.scope} Discount",
            entity=f"{item.entity} ({item.level})",
            impact=f"₹{item.recoverable:,.0f} recoverable",
            detail=f"{item.discount_pct:.1f}% vs {item.benchmark_pct:.0f}% benchmark",
            recommended_action="Review discount approvals",
        ))
    return risks


def _default_opportunities(leakage: List[LeakageItem]) -> List[OpportunityItem]:
    """Derive a single discount-recovery opportunity from existing leakage totals."""
    total = sum(i.recoverable for i in leakage if i.scope == "Labour" and i.level == "Location")
    if total <= 0:
        return []
    return [OpportunityItem(
        title="Discount Recovery",
        estimated_value=_f(total),
        owner="Group Service Head",
        detail="Bring above-benchmark labour discounts back to benchmark",
    )]


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────

def build_context(
    cp: pd.DataFrame,
    pp: pd.DataFrame,
    *,
    client_name: str = "",
    period_label: str = "",
    comparison_label: str = "YoY",
    adv_col: str = "Advisior Name",
    top_n: int = 5,
    business_health: Optional[Dict[str, Any]] = None,
    pnl: Optional[Dict[str, Any]] = None,
    risks: Optional[List[Dict[str, Any]]] = None,
    opportunities: Optional[List[Dict[str, Any]]] = None,
    as_dict: bool = True,
) -> Dict[str, Any]:
    """
    Assemble the Audit Intelligence context from already-calculated WSMIS values.

    Parameters
    ----------
    cp, pp : DataFrames already filtered to the current / prior comparison periods.
    business_health, pnl, risks, opportunities : OPTIONAL artefacts produced by the
        (frozen) dashboard pages. Injected verbatim when provided; otherwise
        defaults are derived from existing leakage aggregates.

    Returns
    -------
    dict (JSON-serializable) when as_dict=True, else a ReportContext instance.
    """
    cp = cp if cp is not None else pd.DataFrame()
    pp = pp if pp is not None else pd.DataFrame()

    cp_kpis = _period_kpis(cp)
    pp_kpis = _period_kpis(pp)

    growth = {
        "revenue_pct": _f(calculate_revenue_growth(cp, pp)) if not cp.empty else 0.0,
        "margin_pct": _f(calculate_margin_growth(cp, pp)) if not cp.empty else 0.0,
        "jc_pct": _f(((cp_kpis.job_cards - pp_kpis.job_cards) / pp_kpis.job_cards * 100)
                     if pp_kpis.job_cards else 0.0),
    }

    leakage = _leakage_items(cp, adv_col=adv_col, top=top_n)

    risk_items = (
        [RiskItem(**r) for r in risks] if risks is not None
        else _default_risks(leakage)
    )
    opp_items = (
        [OpportunityItem(**o) for o in opportunities] if opportunities is not None
        else _default_opportunities(leakage)
    )

    ctx = ReportContext(
        meta={
            "report_type": "Audit Intelligence Report",
            "client": client_name,
            "period": period_label,
            "comparison": comparison_label,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "rows_current": int(len(cp)),
            "rows_prior": int(len(pp)),
            "currency": "INR",
        },
        current_period=cp_kpis,
        prior_period=pp_kpis,
        growth=growth,
        business_health=business_health or {},
        pnl=pnl or {},
        top_locations=_ranked_entities(cp, "Location", "Location Name", top_n),
        top_advisors=_ranked_entities(cp, "Advisor", adv_col, top_n),
        leakage=leakage,
        risks=risk_items,
        opportunities=opp_items,
        benchmarks={
            "labour_discount_pct": float(LABOUR_DISC_BENCH),
            "parts_discount_pct": float(PARTS_DISC_BENCH),
        },
    )

    return ctx.to_dict() if as_dict else ctx
