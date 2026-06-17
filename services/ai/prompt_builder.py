"""
services.ai.prompt_builder — Turns the context JSON into the final LLM prompt.

No business logic and no calculations. This module only serialises the context
and stitches it together with the section template guidance into a single
instruction string for the LLM.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from services.ai.templates import REPORT_SECTIONS


SYSTEM_INSTRUCTION = (
    "You are a senior automotive-dealership financial analyst writing an "
    "Audit Intelligence Report for a Maruti Suzuki workshop network. "
    "Write in clear, executive business English using Markdown. "
    "Use ONLY the figures present in the provided JSON context — never invent or "
    "estimate numbers that are not given. Format all currency in Indian Rupees "
    "with the ₹ symbol and thousands separators. Be concise, specific and "
    "decision-oriented."
)


def _format_inr(value: Any) -> str:
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _sections_block() -> str:
    lines = ["Produce the report with EXACTLY these sections, in this order:"]
    for s in REPORT_SECTIONS:
        lines.append(f"{s.number}. {s.title} — {s.guidance}")
    return "\n".join(lines)


def build_prompt(context: Dict[str, Any], *, include_system: bool = True) -> str:
    """
    Build the final prompt string from a context dict (see context_builder).

    Parameters
    ----------
    context : dict produced by services.ai.context_builder.build_context
    include_system : prepend the system instruction (useful for providers without
        a separate system role).
    """
    meta = context.get("meta", {})
    context_json = json.dumps(context, indent=2, ensure_ascii=False, default=str)

    header = (
        f"# Audit Intelligence Report Request\n"
        f"- Client: {meta.get('client', 'N/A')}\n"
        f"- Period: {meta.get('period', 'N/A')} ({meta.get('comparison', 'YoY')} comparison)\n"
        f"- Currency: {meta.get('currency', 'INR')}\n"
    )

    parts = []
    if include_system:
        parts.append(SYSTEM_INSTRUCTION)
        parts.append("")
    parts.append(header)
    parts.append(_sections_block())
    parts.append("")
    parts.append("## Data Context (authoritative — use only these values)")
    parts.append("```json")
    parts.append(context_json)
    parts.append("```")
    parts.append(
        "\nReturn the complete report in Markdown starting at '## 1. Executive "
        "Summary'. Do not add sections beyond the nine specified."
    )
    return "\n".join(parts)
