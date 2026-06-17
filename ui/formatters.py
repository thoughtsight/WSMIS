import pandas as pd
import numpy as np

# ═══════════════════════════════════════════════════════════════
#  FORMATTERS FROM app.py
# ═══════════════════════════════════════════════════════════════

def fmt_inr(v):
    """Indian style: ₹1,00,000 = 1 Lakh, ₹1,00,00,000 = 1 Crore"""
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    v = float(v)
    if v == 0: return "—"
    neg = v < 0; a = abs(v)
    if a >= 1e7:   s = f"₹{a/1e7:,.2f} Cr"
    elif a >= 1e5: s = f"₹{a/1e5:,.2f} L"
    elif a >= 1e3: s = f"₹{a/1e3:,.1f} K"
    else:          s = f"₹{a:,.0f}"
    return f"-{s}" if neg else s

def fmt_inr_full(v):
    """Full Indian comma format: ₹1,23,45,678"""
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    v = int(round(float(v)))
    if v == 0: return "₹0"
    neg = v < 0
    a = abs(v)
    s = str(a)
    # Indian grouping: last 3 digits, then groups of 2
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

def fmt_inr_short(v):
    """Compact format for chart bar labels: ₹7.75 Cr or ₹88.5 L"""
    if v is None or (isinstance(v, float) and np.isnan(v)): return ""
    v = float(v)
    if v == 0: return ""
    neg = v < 0; a = abs(v)
    if a >= 1e7:   s = f"₹{a/1e7:.2f}Cr"
    elif a >= 1e5: s = f"₹{a/1e5:.1f}L"
    elif a >= 1e3: s = f"₹{a/1e3:.0f}K"
    else:          s = f"₹{a:.0f}"
    return f"-{s}" if neg else s

def fmt_pct(v, sign=False):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "0.00%"
    if str(v) == "New ✦": return "New ✦"
    v = float(v)
    return f"{'+' if v > 0 and sign else ''}{v:.2f}%"

def fmt_num(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    v = float(v)
    if v == 0: return "—"
    return f"{v:,.0f}"


# ═══════════════════════════════════════════════════════════════
#  FORMATTERS FROM internal_audit_app.py
# ═══════════════════════════════════════════════════════════════

def fmt_pct_ratio(v):
    try: return f"{float(v)*100:.1f}%"
    except: return "—"

def fmt_pct_100(v):
    try: return f"{float(v):.1f}%"
    except: return "—"

def fmt_amt(v):
    try:
        f = float(v)
        return "—" if pd.isna(f) else f"₹{f:,.0f}"
    except: return "—"


# ═══════════════════════════════════════════════════════════════
#  FORMATTERS FROM exp_report.py
# ═══════════════════════════════════════════════════════════════

def fmt_inr_exp(v):
    try:
        f = float(v)
        if pd.isna(f): return '—'
        if abs(f) >= 1e7: return f'₹{f/1e7:.2f}Cr'
        if abs(f) >= 1e5: return f'₹{f/1e5:.1f}L'
        return f'₹{f:,.0f}'
    except: return '—'

def fmt_inr_full_exp(v):
    try:
        f = float(v)
        if pd.isna(f): return '—'
        neg = f < 0
        s = f'₹{abs(f):,.0f}'
        return f'({s})' if neg else s
    except: return '—'


# ═══════════════════════════════════════════════════════════════
#  FORMATTERS FROM pnl_report.py
# ═══════════════════════════════════════════════════════════════

def fmt_cr(v):
    """Format a value in ₹ Lakhs to human-readable string."""
    if abs(v) >= 100:
        return f"₹{v/100:.2f} Cr"
    if abs(v) >= 1:
        return f"₹{v:.2f} L"
    if abs(v) >= 0.001:
        return f"₹{v*100:.1f} K"
    return "₹0"

def fmt_pnl_val(v):
    """Format a numeric value for the P&L summary table."""
    if pd.isna(v) or v == 0:
        return "—"
    if abs(v) >= 100:
        return f"{v/100:.2f}Cr"
    if abs(v) >= 1:
        return f"{v:.2f}L"
    if abs(v) >= 0.01:
        return f"{v*100:.1f}K"
    return f"{v*100000:.0f}"
