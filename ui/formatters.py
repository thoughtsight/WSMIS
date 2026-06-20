import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Core Number & Currency Formatters
# ─────────────────────────────────────────────────────────────────────────────

def fmt_num(v):
    """Standard Western number formatting (e.g. 1,234). Zero returns '0' not '—'."""
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    v = float(v)
    if v == 0: return "0"
    return f"{v:,.0f}"

def fmt_amt(v):
    """Standard Western currency formatting (e.g. ₹1,234)"""
    try:
        f = float(v)
        return "—" if pd.isna(f) else f"₹{f:,.0f}"
    except: return "—"

# ─────────────────────────────────────────────────────────────────────────────
# Indian Currency Scale Formatters
# ─────────────────────────────────────────────────────────────────────────────

def fmt_inr(v):
    """Indian style text labels (e.g. ₹1.00 Cr, ₹50.00 L)"""
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    v = float(v)
    if v == 0: return "—"
    neg = v < 0; a = abs(v)
    if a >= 1e7:   s = f"₹{a/1e7:,.2f} Cr"
    elif a >= 1e5: s = f"₹{a/1e5:,.1f} L"
    elif a >= 1e3: s = f"₹{a/1e3:,.1f} K"
    else:          s = f"₹{a:,.0f}"
    return f"-{s}" if neg else s

def fmt_inr_short(v):
    """Compact Indian style for charts (e.g. ₹1.0Cr, ₹50.0L)"""
    if v is None or (isinstance(v, float) and np.isnan(v)): return ""
    v = float(v)
    if v == 0: return ""
    neg = v < 0; a = abs(v)
    if a >= 1e7:   s = f"₹{a/1e7:.2f}Cr"
    elif a >= 1e5: s = f"₹{a/1e5:.1f}L"
    elif a >= 1e3: s = f"₹{a/1e3:.1f}K"
    else:          s = f"₹{a:.0f}"
    return f"-{s}" if neg else s

def fmt_inr_exp(v):
    """Mixed Indian style for expenses (Crores/Lakhs, but raw below 1 Lakh)"""
    try:
        f = float(v)
        if pd.isna(f): return '—'
        if abs(f) >= 1e7: return f'₹{f/1e7:.2f}Cr'
        if abs(f) >= 1e5: return f'₹{f/1e5:.1f}L'
        return f'₹{f:,.0f}'
    except: return '—'

def fmt_cr(v):
    """Format a value already in ₹ Lakhs (e.g. 100 Lakhs -> 1 Cr)"""
    if abs(v) >= 100: return f"₹{v/100:.2f} Cr"
    if abs(v) >= 1: return f"₹{v:.1f} L"
    if abs(v) >= 0.001: return f"₹{v*100:.1f} K"
    return "₹0"

def fmt_pnl_val(v):
    """Format a value already in ₹ Lakhs without rupee symbol"""
    if pd.isna(v) or v == 0: return "—"
    if abs(v) >= 100: return f"{v/100:.2f}Cr"
    if abs(v) >= 1: return f"{v:.1f}L"
    if abs(v) >= 0.01: return f"{v*100:.1f}K"
    return f"{v*100000:.0f}"

# ─────────────────────────────────────────────────────────────────────────────
# Full Comma Currency Formatters
# ─────────────────────────────────────────────────────────────────────────────

def fmt_inr_full(v):
    """Full Indian comma format: ₹1,23,45,678"""
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    v = int(round(float(v)))
    if v == 0: return "₹0"
    neg = v < 0
    a = abs(v)
    s = str(a)
    if len(s) <= 3:
        result = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        groups.insert(0, rest)
        result = ",".join(groups) + "," + last3
    return f"-₹{result}" if neg else f"₹{result}"

def fmt_inr_full_exp(v):
    """Western comma format but wrapped in parentheses for negatives."""
    try:
        f = float(v)
        if pd.isna(f): return '—'
        neg = f < 0
        s = f'₹{abs(f):,.0f}'
        return f'({s})' if neg else s
    except: return '—'

# ─────────────────────────────────────────────────────────────────────────────
# Percentage Formatters
# ─────────────────────────────────────────────────────────────────────────────

def fmt_pct(v, sign=False):
    """Format float as percentage (e.g. 5.1 -> 5.10%)"""
    if v is None or (isinstance(v, float) and np.isnan(v)): return "0.0%"
    if str(v) == "New ✦": return "New ✦"
    v = float(v)
    return f"{'+' if v > 0 and sign else ''}{v:.1f}%"

def fmt_pct_ratio(v):
    """Format raw ratio as percentage (e.g. 0.051 -> 5.1%)"""
    try: return f"{float(v)*100:.1f}%"
    except: return "—"

def fmt_pct_100(v):
    """Format float as 1-decimal percentage (e.g. 5.1 -> 5.1%)"""
    try: return f"{float(v):.1f}%"
    except: return "—"
