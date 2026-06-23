import streamlit as st
import pandas as pd
import numpy as np
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from ui.design_tokens import T
from utils.calculations.common import calc_growth_pct
from config.settings import TRAFFIC_GREEN_PCT, TRAFFIC_RED_PCT

def yoy_badge(cp, pp):
    if pp is None or np.isnan(pp) or pp <= 0: return '<span class="badge-new">New ✦</span>'
    pct = calc_growth_pct(cp, pp, fill_value=0)
    if pct > 0: return f'<span class="badge-pos">▲ {pct:.1f}%</span>'
    if pct < 0: return f'<span class="badge-neg">▼ {abs(pct):.1f}%</span>'
    return '<span class="badge-neutral">— 0%</span>'


def traffic_light(cp, pp):
    """Returns a CSS-styled traffic light indicator (no emoji)."""
    if pp is None or (isinstance(pp, float) and np.isnan(pp)) or pp <= 0:
        return f'<span style="color: {T.C["gray"]}; font-size: 12px;">●</span>'
    pct = calc_growth_pct(cp, pp, fill_value=0)
    if pct > TRAFFIC_GREEN_PCT:
        return f'<span style="color: {T.COLOR_SUCCESS}; font-size: 12px;">●</span>'
    if pct < -TRAFFIC_RED_PCT:
        return f'<span style="color: {T.COLOR_DANGER}; font-size: 12px;">●</span>'
    return f'<span style="color: {T.COLOR_WARNING}; font-size: 12px;">●</span>'


def tgt_badge(pct):
    """Returns a CSS-styled target badge without emoji."""
    try:
        pct = float(pct)
    except (TypeError, ValueError):
        return '<span class="badge-neutral">—</span>'
    
    if pct >= 100:
        badge_cls = "badge-pos"
        indicator = "▲"
    elif pct >= 90:
        badge_cls = "badge-warn"
        indicator = "~"
    else:
        badge_cls = "badge-neg"
        indicator = "▼"
    
    return f'<span class="{badge_cls}">{indicator} {pct:.1f}%</span>'


