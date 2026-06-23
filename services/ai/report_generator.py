"""
services.ai.report_generator — Orchestrates the Audit Intelligence pipeline:

        context (JSON)  ->  prompt  ->  LLM  ->  Markdown report

Providers are pluggable. "gemini" is the intended production backend; "anthropic"
is supported (the dependency already ships with WSMIS); "offline" renders a fully
populated deterministic Markdown report from the context with NO network call, so
the pipeline is always runnable and testable.

No PDF rendering here (per PR-025 scope) — Markdown only.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from services.ai.context_builder import build_context
from services.ai.prompt_builder import build_prompt, SYSTEM_INSTRUCTION
from services.ai.templates import REPORT_SECTIONS
from services.ai.models import GeneratedReport
from services.logger import app_logger as logger

AVAILABLE_PROVIDERS = ("auto", "gemini", "anthropic", "offline")

# Default models per provider (overridable via generate_report(model=...)).
_DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash",
    "anthropic": "claude-3-5-sonnet-latest",
    "offline": "offline-deterministic",
}


# ──────────────────────────────────────────────────────────────────────────
# Provider implementations
# ──────────────────────────────────────────────────────────────────────────

def _resolve_provider(provider: str) -> str:
    """Resolve 'auto' to the best available backend based on keys + packages."""
    if provider != "auto":
        return provider
    if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) and _has_module("google.generativeai"):
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY") and _has_module("anthropic"):
        return "anthropic"
    return "offline"


def _has_module(name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(name) is not None


def _call_gemini(prompt: str, model: str, api_key: Optional[str]) -> str:
    from services.ai.gemini_provider import generate_from_gemini
    return generate_from_gemini(prompt=prompt, system_instruction=SYSTEM_INSTRUCTION, model=model, api_key=api_key)


def _call_anthropic(prompt: str, model: str, api_key: Optional[str]) -> str:
    from services.ai.provider import get_ai_client
    client = get_ai_client()
    msg = client.messages.create(
        model=model,
        max_tokens=4000,
        system=SYSTEM_INSTRUCTION,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(getattr(b, "text", "") for b in msg.content).strip()


# ──────────────────────────────────────────────────────────────────────────
# Offline deterministic renderer (no LLM) — also the example generator
# ──────────────────────────────────────────────────────────────────────────

def _inr(v: Any) -> str:
    try:
        return f"₹{float(v):,.0f}"
    except (TypeError, ValueError):
        return str(v)


def _render_offline(context: Dict[str, Any]) -> str:
    meta = context.get("meta", {})
    cp = context.get("current_period", {})
    pp = context.get("prior_period", {})
    growth = context.get("growth", {})
    bhs = context.get("business_health", {})
    leakage = context.get("leakage", [])
    risks = context.get("risks", [])
    opps = context.get("opportunities", [])
    locs = context.get("top_locations", [])
    advs = context.get("top_advisors", [])

    md: List[str] = []
    md.append(f"# Audit Intelligence Report — {meta.get('client', 'WSMIS')}")
    md.append(f"*Period: {meta.get('period', 'N/A')} · {meta.get('comparison', 'YoY')} · "
              f"Generated {meta.get('generated_at', '')}*")
    md.append("")

    # 1. Executive Summary
    md.append(REPORT_SECTIONS[0].heading())
    health_txt = (f"Business Health Score is **{bhs.get('score')}/100 "
                  f"({bhs.get('label', 'N/A')})**. " if bhs.get("score") is not None else "")
    md.append(
        f"{health_txt}Net revenue for the period is **{_inr(cp.get('total_revenue'))}** "
        f"({growth.get('revenue_pct', 0):+.1f}% vs prior), with total margin of "
        f"**{_inr(cp.get('total_margin'))}** ({growth.get('margin_pct', 0):+.1f}%). "
        f"Labour discount is running at **{cp.get('labour_discount_pct', 0):.1f}%** "
        f"against a **{context.get('benchmarks', {}).get('labour_discount_pct', 15):.0f}%** benchmark."
    )
    md.append("")

    # 2. Business Performance
    md.append(REPORT_SECTIONS[1].heading())
    md.append("| Metric | Current | Prior | Growth |")
    md.append("|---|---|---|---|")
    md.append(f"| Net Revenue | {_inr(cp.get('total_revenue'))} | {_inr(pp.get('total_revenue'))} | {growth.get('revenue_pct', 0):+.1f}% |")
    md.append(f"| Total Margin | {_inr(cp.get('total_margin'))} | {_inr(pp.get('total_margin'))} | {growth.get('margin_pct', 0):+.1f}% |")
    md.append(f"| Job Cards | {cp.get('job_cards', 0):,.0f} | {pp.get('job_cards', 0):,.0f} | {growth.get('jc_pct', 0):+.1f}% |")
    md.append(f"| Labour Discount % | {cp.get('labour_discount_pct', 0):.1f}% | {pp.get('labour_discount_pct', 0):.1f}% | — |")
    md.append("")

    # 3. Profit Drivers
    md.append(REPORT_SECTIONS[2].heading())
    if locs:
        for l in locs[:5]:
            md.append(f"- **{l['name']}** — margin {_inr(l['total_margin'])} across {l['job_cards']:,.0f} JCs")
    else:
        md.append("_No location margin data available._")
    md.append("")

    # 4. Loss Drivers
    md.append(REPORT_SECTIONS[3].heading())
    if risks:
        for r in risks:
            md.append(f"- **{r['title']}** at {r['entity']} — {r['impact']} ({r['detail']})")
    else:
        md.append("_No material loss drivers detected this period._")
    md.append("")

    # 5. Revenue Leakage
    md.append(REPORT_SECTIONS[4].heading())
    if leakage:
        md.append("| Entity | Scope | Level | Disc % | Benchmark | Recoverable |")
        md.append("|---|---|---|---|---|---|")
        for it in leakage:
            md.append(f"| {it['entity']} | {it['scope']} | {it['level']} | "
                      f"{it['discount_pct']:.1f}% | {it['benchmark_pct']:.0f}% | {_inr(it['recoverable'])} |")
        total_leak = sum(it["recoverable"] for it in leakage)
        md.append("")
        md.append(f"**Total identified recoverable leakage: {_inr(total_leak)}**")
    else:
        md.append("_No above-benchmark leakage identified._")
    md.append("")

    # 6. Top Risks
    md.append(REPORT_SECTIONS[5].heading())
    if risks:
        for i, r in enumerate(risks, 1):
            md.append(f"{i}. **{r['title']}** — {r['entity']} · {r['impact']} · _{r['detail']}_")
    else:
        md.append("_No high-priority risks._")
    md.append("")

    # 7. Top Opportunities
    md.append(REPORT_SECTIONS[6].heading())
    if opps:
        for i, o in enumerate(opps, 1):
            md.append(f"{i}. **{o['title']}** — est. {_inr(o['estimated_value'])} · Owner: {o['owner']}")
    else:
        md.append("_No quantified opportunities this period._")
    md.append("")

    # 8. Priority Actions
    md.append(REPORT_SECTIONS[7].heading())
    actions: List[str] = []
    for r in risks[:3]:
        actions.append(f"Address **{r['title']}** at {r['entity']} — {r['recommended_action']}.")
    for o in opps[:2]:
        actions.append(f"Pursue **{o['title']}** (~{_inr(o['estimated_value'])}) — owner {o['owner']}.")
    if not actions:
        actions.append("Maintain current controls; no urgent action required.")
    for i, a in enumerate(actions[:5], 1):
        md.append(f"{i}. {a}")
    md.append("")

    # 9. Estimated Financial Recovery
    md.append(REPORT_SECTIONS[8].heading())
    # Avoid double-counting: separate location-level leakage from advisor-level (advisor is subset of location)
    loc_leakage = sum(it["recoverable"] for it in leakage if it["level"] == "Location")
    opp_total = sum(o["estimated_value"] for o in opps)
    md.append("| Source | Estimated Recovery (₹) |")
    md.append("|---|---|")
    md.append(f"| Location-level Discount/Leakage (above benchmark) | {_inr(loc_leakage)} |")
    md.append(f"| Operational Opportunities | {_inr(opp_total)} |")
    md.append(f"| **Total Indicative Recovery** | **{_inr(loc_leakage + opp_total)}** |")
    md.append("")
    md.append("_Figures are indicative, derived from benchmark gaps on already-calculated WSMIS values._")

    return "\n".join(md).strip()


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────

def generate_report(
    cp: Optional[pd.DataFrame] = None,
    pp: Optional[pd.DataFrame] = None,
    *,
    context: Optional[Dict[str, Any]] = None,
    provider: str = "auto",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **context_kwargs: Any,
) -> GeneratedReport:
    """
    Run the full pipeline and return a GeneratedReport (Markdown + metadata).

    Usage
    -----
    # From dashboard data (builds context internally):
        report = generate_report(cp_df, pp_df, client_name="Rukmani Motors",
                                  period_label="Apr-26 → Jun-26", provider="gemini")

    # From a pre-built context dict:
        report = generate_report(context=my_context, provider="offline")

    On any provider/network error the function falls back to the offline renderer
    so the caller always receives a valid Markdown report.
    """
    if provider not in AVAILABLE_PROVIDERS:
        raise ValueError(f"provider must be one of {AVAILABLE_PROVIDERS}, got {provider!r}")

    if context is None:
        if cp is None:
            raise ValueError("Provide either `context` or `cp` (and optionally `pp`).")
        context = build_context(cp, pp if pp is not None else pd.DataFrame(), **context_kwargs)

    prompt = build_prompt(context)
    resolved = _resolve_provider(provider)
    chosen_model = model or _DEFAULT_MODELS.get(resolved, "unknown")

    markdown = ""
    used_provider = resolved
    used_model = chosen_model

    if resolved == "offline":
        markdown = _render_offline(context)
    else:
        try:
            if resolved == "gemini":
                markdown = _call_gemini(prompt, chosen_model, api_key)
            elif resolved == "anthropic":
                markdown = _call_anthropic(prompt, chosen_model, api_key)
            if not markdown:
                raise RuntimeError(f"{resolved} returned an empty response.")
        except Exception as exc:  # graceful fallback — never crash the caller
            logger.error(f"AI report provider '{resolved}' failed: {exc}. Falling back to offline.")
            markdown = _render_offline(context)
            used_provider = "offline (fallback)"
            used_model = _DEFAULT_MODELS["offline"]

    return GeneratedReport(
        markdown=markdown,
        provider=used_provider,
        model=used_model,
        context=context,
        prompt=prompt,
        generated_at=datetime.now().isoformat(timespec="seconds"),
    )
