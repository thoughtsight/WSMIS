"""
RKM Motors — Profit & Loss Executive Dashboard Module
======================================================
Data-driven P&L report for integration with WSMIS app.py.

Architecture:
  • Computation layer: pure functions, no Streamlit dependency
  • Presentation layer: Streamlit rendering functions
  • Single entry point: render_in_streamlit()

Data sources (passed in, NOT loaded here):
  • df      — WSMIS main sheet (margin, labour, income columns)
  • exp_df  — EXP. worksheet  (Expenses Name, Expenses Rs., Month Name, Location, Expenses Group)

No st.set_page_config(). No navigation. No Google Sheet loading.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

MONTH_ORDER = [
    'Apr-24','May-24','Jun-24','Jul-24','Aug-24','Sep-24',
    'Oct-24','Nov-24','Dec-24','Jan-25','Feb-25','Mar-25',
    'Apr-25','May-25','Jun-25','Jul-25','Aug-25','Sep-25',
    'Oct-25','Nov-25','Dec-25','Jan-26','Feb-26','Mar-26',
    'Apr-26','May-26','Jun-26','Jul-26','Aug-26','Sep-26',
    'Oct-26','Nov-26','Dec-26','Jan-27','Feb-27','Mar-27',
]

# Column names as they appear in the WSMIS main sheet
MARGIN_COLUMNS = [
    "Parts_Margin", "Accessory_Margin", "Oil_Margin",
    "Tyre_Margin", "Battery_Margin", "Other_Margin",
]
LEAKAGE_COLUMNS = ["Internal Consumption", "VOR Charges", "Dealer FOC"]
INCOME_COLUMNS  = ["OTC Income", "MSIL Labour Claim", "FSC Income"]
LABOUR_COL      = "Net_Labour"       # computed column from app.py
TOTAL_MARGIN_COL= "Total Margin"
ADV_COL         = "Advisior Name"    # typo preserved from Google Sheet

# Display grouping for margin composition donut
MARGIN_DISPLAY_CATEGORIES = {
    "Parts Margin":     ["Parts_Margin"],
    "Oil Margin":       ["Oil_Margin"],
    "Net Labour":       [LABOUR_COL],
    "FSC Income":       ["FSC Income"],
    "OTC Income":       ["OTC Income"],
    "Accessory Margin": ["Accessory_Margin"],
    "MSIL Labour":      ["MSIL Labour Claim"],
    "Battery + Tyre":   ["Battery_Margin", "Tyre_Margin"],
}

# Mid-level grouping for expense composition donut
# Maps Expenses Name keywords → display category
EXPENSE_DISPLAY_MAP = {
    "Employee":     "Employee & Staff",
    "Remuneration": "Employee & Staff",
    "Security":     "Employee & Staff",
    "Rent":         "Rent & Utilities",
    "Electricity":  "Rent & Utilities",
    "Telephone":    "Rent & Utilities",
    "Painting":     "Painting & Material",
    "Repair":       "Repair & Maintenance",
    "Maintenance":  "Repair & Maintenance",
    "Free Service": "Warranty & Claims",
    "Maruti":       "Warranty & Claims",
    "Advertising":  "Marketing & Promotion",
    "Sales Promotion": "Marketing & Promotion",
    "Finance":      "Finance & Interest",
    "Interest":     "Finance & Interest",
}
EXPENSE_DEFAULT_GROUP = "Other Admin"

# Chart colours
MARGIN_COLORS = ["#3b82f6","#06b6d4","#8b5cf6","#f59e0b","#10b981","#6366f1","#ec4899","#f97316"]
EXPENSE_COLORS = ["#ef4444","#f87171","#fca5a5","#fb923c","#fbbf24","#a3e635","#34d399","#60a5fa"]
TREND_COLORS = {"margin": "#3b82f6", "expense": "#f87171", "profit": "#16a34a"}

# Status thresholds
LOSS_THRESHOLD  = 0          # profit < 0 → loss
WATCH_THRESHOLD = 0          # mom_change < 0 → watch
NODATA_THRESHOLD = 0.001     # margin < this → nodata

# ═══════════════════════════════════════════════════════════════
#  DATA STRUCTURE
# ═══════════════════════════════════════════════════════════════

@dataclass
class PnLData:
    """All computed results for the P&L dashboard."""
    # Period
    months: list
    current_month: str
    previous_month: str
    period_label: str
    location_count: int
    record_count: int

    # KPIs — current period
    total_margin: float = 0.0
    total_expense: float = 0.0
    net_profit: float = 0.0
    profit_margin_pct: float = 0.0
    expense_ratio_pct: float = 0.0
    leakage_total: float = 0.0

    # KPIs — previous period (for MoM delta)
    prev_total_margin: float = 0.0
    prev_total_expense: float = 0.0
    prev_net_profit: float = 0.0
    prev_profit_margin_pct: float = 0.0
    prev_expense_ratio_pct: float = 0.0

    # Trend series (month → value, ₹ Lakhs)
    margin_by_month: dict = field(default_factory=dict)
    expense_by_month: dict = field(default_factory=dict)
    profit_by_month: dict = field(default_factory=dict)

    # Composition (current month)
    margin_composition: dict = field(default_factory=dict)
    expense_composition: dict = field(default_factory=dict)

    # Margin category trend (category → [val per month])
    margin_category_trend: dict = field(default_factory=dict)

    # Location profitability (sorted by profit desc)
    locations: list = field(default_factory=list)

    # P&L summary rows
    pnl_rows: list = field(default_factory=list)

    # Generated narratives
    drivers: list = field(default_factory=list)
    killers: list = field(default_factory=list)
    insights: list = field(default_factory=list)
    actions: list = field(default_factory=list)

    # Alerts
    alerts: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
#  FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════

from ui.formatters import fmt_cr, fmt_pnl_val

def _safe_pct(num, den):
    """Compute percentage safely."""
    return (num / den * 100) if den and den != 0 else 0.0

def _mom_delta(curr, prev):
    """Simple MoM change."""
    return curr - prev if curr is not None and prev is not None else 0.0

def classify_location_status(profit, mom_change):
    """Classify a location as profit/watch/loss/nodata."""
    if abs(profit) < NODATA_THRESHOLD:
        return "nodata"
    if profit < LOSS_THRESHOLD:
        return "loss"
    if mom_change < WATCH_THRESHOLD:
        return "watch"
    return "good"


# ═══════════════════════════════════════════════════════════════
#  COMPUTATION LAYER — Pure functions, no Streamlit
# ═══════════════════════════════════════════════════════════════

def _to_lakhs(val):
    """Convert raw value (assumed rupees) to lakhs."""
    return val / 100000.0


def _compute_margin_by_month(df, months):
    """
    Compute total margin and per-category margin for each month.
    Returns: (total_by_month, category_by_month)
      total_by_month:    {month: total_margin_lakhs}
      category_by_month: {category_name: [val_per_month_lakhs]}
    """
    df_m = df[df["Month Name"].isin(months)].copy()

    # Total margin per month
    total_by_month = {}
    for m in months:
        m_df = df_m[df_m["Month Name"] == m]
        total_by_month[m] = _to_lakhs(m_df[TOTAL_MARGIN_COL].sum()) if TOTAL_MARGIN_COL in m_df.columns else 0.0

    # Per-category breakdown
    all_cat_cols = MARGIN_COLUMNS + [LABOUR_COL] + INCOME_COLUMNS + LEAKAGE_COLUMNS
    category_by_month = {}
    for display_name, source_cols in MARGIN_DISPLAY_CATEGORIES.items():
        vals = []
        for m in months:
            m_df = df_m[df_m["Month Name"] == m]
            total = 0.0
            for sc in source_cols:
                if sc in m_df.columns:
                    total += _to_lakhs(m_df[sc].sum())
            vals.append(total)
        category_by_month[display_name] = vals

    # Also compute individual columns for P&L table
    detail_by_month = {}
    for col in all_cat_cols:
        vals = []
        for m in months:
            m_df = df_m[df_m["Month Name"] == m]
            if col in m_df.columns:
                vals.append(_to_lakhs(m_df[col].sum()))
            else:
                vals.append(0.0)
        detail_by_month[col] = vals

    return total_by_month, category_by_month, detail_by_month


def _compute_expense_by_month(exp_df, months):
    """
    Compute total expense per month from the EXP. sheet.
    Returns: {month: total_expense_lakhs}
    """
    if exp_df is None or exp_df.empty:
        return {m: 0.0 for m in months}

    exp_m = exp_df[exp_df["Month Name"].isin(months)].copy()
    exp_m["Expenses Rs."] = pd.to_numeric(exp_m["Expenses Rs."], errors="coerce").fillna(0)

    result = {}
    for m in months:
        m_df = exp_m[exp_m["Month Name"] == m]
        result[m] = _to_lakhs(m_df["Expenses Rs."].sum())
    return result


def _compute_expense_composition(exp_df, current_month):
    """
    Compute expense mix by display category for the current month.
    Uses EXPENSE_DISPLAY_MAP keyword matching on Expenses Name.
    Returns: {category: amount_lakhs}
    """
    if exp_df is None or exp_df.empty:
        return {}

    m_df = exp_df[exp_df["Month Name"] == current_month].copy()
    m_df["Expenses Rs."] = pd.to_numeric(m_df["Expenses Rs."], errors="coerce").fillna(0)

    def _classify(name):
        if pd.isna(name):
            return EXPENSE_DEFAULT_GROUP
        name_str = str(name)
        for keyword, group in EXPENSE_DISPLAY_MAP.items():
            if keyword.lower() in name_str.lower():
                return group
        return EXPENSE_DEFAULT_GROUP

    m_df["_display_group"] = m_df["Expenses Name"].apply(_classify)
    result = m_df.groupby("_display_group")["Expenses Rs."].sum().to_dict()
    return {k: _to_lakhs(v) for k, v in result.items() if v != 0}


def _compute_location_profitability(df, exp_df, current_month, previous_month):
    """
    Join margin-by-location with expense-by-location.
    Returns: list of dicts sorted by profit desc.
    """
    # Margin by location (current month)
    df_curr = df[df["Month Name"] == current_month]
    margin_curr = df_curr.groupby("Location Name")[TOTAL_MARGIN_COL].sum().reset_index()
    margin_curr.columns = ["name", "margin"]
    margin_curr["margin"] = margin_curr["margin"].apply(_to_lakhs)

    # Margin by location (previous month)
    df_prev = df[df["Month Name"] == previous_month]
    margin_prev = df_prev.groupby("Location Name")[TOTAL_MARGIN_COL].sum().reset_index()
    margin_prev.columns = ["name", "margin_prev"]
    margin_prev["margin_prev"] = margin_prev["margin_prev"].apply(_to_lakhs)

    # Expense by location (current month)
    exp_curr = pd.DataFrame(columns=["name", "expense"])
    if exp_df is not None and not exp_df.empty:
        e_curr = exp_df[exp_df["Month Name"] == current_month].copy()
        e_curr["Expenses Rs."] = pd.to_numeric(e_curr["Expenses Rs."], errors="coerce").fillna(0)
        exp_curr = e_curr.groupby("Location")["Expenses Rs."].sum().reset_index()
        exp_curr.columns = ["name", "expense"]
        exp_curr["expense"] = exp_curr["expense"].apply(_to_lakhs)
        exp_curr = exp_curr[exp_curr["name"].str.strip() != ""]

    # Expense by location (previous month)
    exp_prev = pd.DataFrame(columns=["name", "expense_prev"])
    if exp_df is not None and not exp_df.empty:
        e_prev = exp_df[exp_df["Month Name"] == previous_month].copy()
        e_prev["Expenses Rs."] = pd.to_numeric(e_prev["Expenses Rs."], errors="coerce").fillna(0)
        exp_prev = e_prev.groupby("Location")["Expenses Rs."].sum().reset_index()
        exp_prev.columns = ["name", "expense_prev"]
        exp_prev["expense_prev"] = exp_prev["expense_prev"].apply(_to_lakhs)
        exp_prev = exp_prev[exp_prev["name"].str.strip() != ""]

    # Merge all
    loc_df = margin_curr.merge(exp_curr, on="name", how="outer")
    loc_df = loc_df.merge(margin_prev, on="name", how="outer")
    loc_df = loc_df.merge(exp_prev, on="name", how="outer")
    loc_df = loc_df.fillna(0)

    # Compute profit and MoM
    loc_df["profit"] = loc_df["margin"] - loc_df["expense"]
    loc_df["profit_prev"] = loc_df["margin_prev"] - loc_df["expense_prev"]
    loc_df["mom_profit_change"] = loc_df["profit"] - loc_df["profit_prev"]

    # Anomaly count: count negative-labour advisors at this location
    anomaly_counts = {}
    if LABOUR_COL in df_curr.columns and ADV_COL in df_curr.columns:
        neg_lab = df_curr.groupby(["Location Name", ADV_COL])[LABOUR_COL].sum().reset_index()
        neg_lab = neg_lab[neg_lab[LABOUR_COL] < 0]
        anomaly_counts = neg_lab.groupby("Location Name")[ADV_COL].count().to_dict()

    # Build result
    locations = []
    for _, row in loc_df.iterrows():
        name = row["name"]
        profit = row["profit"]
        mom_chg = row["mom_profit_change"]
        locations.append({
            "name": name,
            "margin": row["margin"],
            "expense": row["expense"],
            "profit": profit,
            "mom_p": mom_chg,
            "anomalies": anomaly_counts.get(name, 0),
            "status": classify_location_status(profit, mom_chg),
        })

    locations.sort(key=lambda x: x["profit"], reverse=True)
    return locations


def _generate_drivers(detail_by_month, months, locations):
    """
    Identify top profit drivers from margin categories.
    Returns: list of dicts [{icon, name, value, trend, note}]
    """
    if len(months) < 1:
        return []

    curr_idx = -1
    first_idx = 0

    # Rank categories by current-month value (descending)
    categories = []
    for col, vals in detail_by_month.items():
        if col in LEAKAGE_COLUMNS:
            continue  # skip leakage — those go to killers
        curr_val = vals[curr_idx] if vals else 0
        if curr_val <= 0:
            continue
        first_val = vals[first_idx] if vals else 0
        change = curr_val - first_val if len(vals) > 1 else 0
        categories.append({
            "col": col,
            "value": curr_val,
            "change": change,
        })

    categories.sort(key=lambda x: x["value"], reverse=True)

    icons = ["🏆", "💰", "🛢️", "📋", "💎"]
    drivers = []
    for i, cat in enumerate(categories[:4]):
        icon = icons[i] if i < len(icons) else "📊"
        name = cat["col"].replace("_", " ")
        chg_str = f"+{fmt_cr(cat['change'])}" if cat["change"] > 0 else fmt_cr(cat["change"])
        drivers.append({
            "icon": icon,
            "name": name,
            "value": fmt_cr(cat["value"]),
            "trend": f"{chg_str} vs {months[first_idx]}",
            "note": f"Current period value: {fmt_cr(cat['value'])}",
        })

    # Add top profitable location if available
    if locations:
        best = locations[0]
        if best["profit"] > 0:
            drivers.append({
                "icon": "💎",
                "name": f"{best['name']} Location",
                "value": fmt_cr(best["profit"]),
                "trend": "Top location",
                "note": f"Best margin-to-expense ratio in {months[-1]}",
            })

    return drivers[:5]


def _generate_killers(detail_by_month, months, df, current_month, exp_df):
    """
    Identify top profit killers from leakage, high-expense locations, and negative labour.
    Returns: list of dicts [{icon, name, value, tag, note}]
    """
    killers = []
    curr_idx = -1

    # Leakage columns
    for col in LEAKAGE_COLUMNS:
        if col in detail_by_month:
            val = detail_by_month[col][curr_idx] if detail_by_month[col] else 0
            if val < 0:  # these are costs (negative)
                killers.append({
                    "icon": "🔴",
                    "name": col.replace("_", " "),
                    "value": fmt_cr(abs(val)),
                    "tag": "Leakage",
                    "note": f"Revenue drag in {months[-1]}",
                    "_sort": abs(val),
                })

    # Highest expense location
    if exp_df is not None and not exp_df.empty:
        e_curr = exp_df[exp_df["Month Name"] == current_month].copy()
        e_curr["Expenses Rs."] = pd.to_numeric(e_curr["Expenses Rs."], errors="coerce").fillna(0)
        loc_exp = e_curr.groupby("Location")["Expenses Rs."].sum()
        loc_exp = loc_exp[loc_exp.index.str.strip() != ""]
        if not loc_exp.empty:
            worst_loc = loc_exp.idxmax()
            worst_val = _to_lakhs(loc_exp.max())
            total_exp = _to_lakhs(loc_exp.sum())
            pct = _safe_pct(worst_val, total_exp)
            killers.append({
                "icon": "⚠️",
                "name": f"{worst_loc} Expenses",
                "value": fmt_cr(worst_val),
                "tag": f"{pct:.0f}% of total",
                "note": f"Highest expense location — needs revenue justification",
                "_sort": worst_val,
            })

    # Negative labour advisors
    if LABOUR_COL in df.columns and ADV_COL in df.columns:
        df_curr = df[df["Month Name"] == current_month]
        neg_adv = df_curr.groupby([ADV_COL, "Location Name"])[LABOUR_COL].sum().reset_index()
        neg_adv = neg_adv[neg_adv[LABOUR_COL] < 0]
        if not neg_adv.empty:
            count = len(neg_adv)
            killers.append({
                "icon": "⚠️",
                "name": "Negative Net Labour",
                "value": f"{count} advisor{'s' if count > 1 else ''}",
                "tag": ", ".join(neg_adv["Location Name"].unique()[:3]),
                "note": "Labour cost exceeds recovery — productivity issue",
                "_sort": count * 10,
            })

    killers.sort(key=lambda x: x.get("_sort", 0), reverse=True)
    # Remove sort key from output
    for k in killers:
        k.pop("_sort", None)

    return killers[:5]


def _generate_insights(data):
    """
    Generate executive insights from computed PnLData.
    Returns: list of dicts [{icon, level, title, body}]
    """
    insights = []
    mom_profit_chg = _mom_delta(data.net_profit, data.prev_net_profit)
    mom_margin_chg = _mom_delta(data.total_margin, data.prev_total_margin)
    mom_expense_chg = _mom_delta(data.total_expense, data.prev_total_expense)

    # 1. Profit direction
    if mom_profit_chg > 0:
        insights.append({
            "icon": "📈", "level": "HIGH",
            "title": f"Profit improved {fmt_cr(abs(mom_profit_chg))} MoM ({data.previous_month}→{data.current_month})",
            "body": f"Driven by {fmt_cr(abs(mom_margin_chg))} margin {'gain' if mom_margin_chg > 0 else 'decline'} "
                    f"and {fmt_cr(abs(mom_expense_chg))} expense {'reduction' if mom_expense_chg < 0 else 'increase'}. "
                    f"Net profit now {fmt_cr(data.net_profit)} in {data.current_month}."
        })
    elif mom_profit_chg < 0:
        insights.append({
            "icon": "📉", "level": "HIGH",
            "title": f"Profit declined {fmt_cr(abs(mom_profit_chg))} MoM ({data.previous_month}→{data.current_month})",
            "body": f"Net profit dropped to {fmt_cr(data.net_profit)}. "
                    f"Margin changed by {fmt_cr(mom_margin_chg)}, expenses changed by {fmt_cr(mom_expense_chg)}."
        })

    # 2. Leakage
    if data.leakage_total > 0:
        insights.append({
            "icon": "🔧", "level": "HIGH",
            "title": f"Revenue leakage at {fmt_cr(data.leakage_total)} — unrecovered cost",
            "body": "Internal Consumption and VOR Charges are dragging margin. "
                    "Needs job-card enforcement and service advisor accountability."
        })

    # 3. Negative labour advisors
    neg_labour_killers = [k for k in data.killers if "Negative" in k.get("name", "")]
    if neg_labour_killers:
        k = neg_labour_killers[0]
        insights.append({
            "icon": "👷", "level": "HIGH",
            "title": f"{k['value']} with negative net labour — productivity crisis",
            "body": "Labour recovery below cost. Review workload allocation, retrain or reassign."
        })

    # 4. Highest expense location
    high_exp_killers = [k for k in data.killers if "Expenses" in k.get("name", "")]
    if high_exp_killers:
        k = high_exp_killers[0]
        insights.append({
            "icon": "📍", "level": "MED",
            "title": f"{k['name']}: {k['value']} ({k['tag']})",
            "body": "Revenue contribution must justify this cost base. Verify margin numbers."
        })

    # 5. Best/worst margin categories
    if data.margin_category_trend and len(data.months) >= 2:
        for cat, vals in data.margin_category_trend.items():
            if len(vals) >= 2 and vals[-1] > vals[-2] and (vals[-1] - vals[-2]) > 1.0:
                insights.append({
                    "icon": "📈", "level": "MED",
                    "title": f"{cat} surged +{fmt_cr(vals[-1] - vals[-2])} in {data.current_month}",
                    "body": f"Grew from {fmt_cr(vals[-2])} to {fmt_cr(vals[-1])}. Positive signal — capitalise on this."
                })
                break  # only top one

    # 6. Best locations
    profitable = [l for l in data.locations if l["status"] == "good" and l["profit"] > 0]
    if len(profitable) >= 2:
        top2 = profitable[:2]
        insights.append({
            "icon": "✅", "level": "LOW",
            "title": f"{top2[0]['name']} and {top2[1]['name']} are the most profitable locations",
            "body": f"{top2[0]['name']}: {fmt_cr(top2[0]['profit'])} profit. "
                    f"{top2[1]['name']}: {fmt_cr(top2[1]['profit'])} profit. "
                    "These are the efficiency benchmarks."
        })

    # 7. Expense ratio warning
    if data.expense_ratio_pct > 100:
        insights.append({
            "icon": "⚙️", "level": "HIGH",
            "title": f"Expense ratio at {data.expense_ratio_pct:.0f}% — expenses exceed margin",
            "body": "Business is operating at a loss. Margin cannot cover expenses. Immediate cost control required."
        })

    return insights[:7]


def _generate_actions(data):
    """
    Generate prioritised action items from data anomalies.
    Returns: list of dicts [{dot_color, tag_class, tag_label, text}]
    """
    actions = []

    # Leakage actions
    if data.leakage_total > 0:
        actions.append({
            "dot_color": "dot-red", "tag_class": "tag-urgent", "tag_label": "URGENT",
            "text": f"Stop Internal Consumption leakage — enforce job-card for every internal part issue. "
                    f"Current leakage: {fmt_cr(data.leakage_total)}."
        })

    # Negative labour
    neg_labour = [k for k in data.killers if "Negative" in k.get("name", "")]
    if neg_labour:
        actions.append({
            "dot_color": "dot-red", "tag_class": "tag-urgent", "tag_label": "URGENT",
            "text": f"Review {neg_labour[0]['value']} with negative net labour. "
                    "Assign jobs, track bay utilisation daily until resolved."
        })

    # High expense locations
    high_exp = [k for k in data.killers if "Expenses" in k.get("name", "")]
    if high_exp:
        actions.append({
            "dot_color": "dot-amber", "tag_class": "tag-med", "tag_label": "THIS WEEK",
            "text": f"{high_exp[0]['name']}: {high_exp[0]['value']} needs PO verification. "
                    "Cross-check with revenue earned."
        })

    # Loss locations
    loss_locs = [l for l in data.locations if l["status"] == "loss"]
    for loc in loss_locs[:2]:
        actions.append({
            "dot_color": "dot-amber", "tag_class": "tag-med", "tag_label": "THIS WEEK",
            "text": f"{loc['name']}: operating at a loss ({fmt_cr(loc['profit'])}). "
                    "Investigate cost structure and revenue potential."
        })

    # Watch locations (declining MoM)
    watch_locs = [l for l in data.locations if l["status"] == "watch" and l["mom_p"] < -1.0]
    for loc in watch_locs[:2]:
        actions.append({
            "dot_color": "dot-blue", "tag_class": "tag-med", "tag_label": "MONITOR",
            "text": f"{loc['name']}: profit declined {fmt_cr(abs(loc['mom_p']))} MoM. "
                    "If decline continues for 2 months — flag for restructuring."
        })

    # No-data locations
    nodata_locs = [l for l in data.locations if l["status"] == "nodata"]
    for loc in nodata_locs[:1]:
        actions.append({
            "dot_color": "dot-amber", "tag_class": "tag-med", "tag_label": "DATA",
            "text": f"{loc['name']}: ₹0 in {data.current_month}. "
                    "Confirm data upload completeness — likely a sync failure."
        })

    # Replicate best practice
    best = [l for l in data.locations if l["status"] == "good" and l["profit"] > 0]
    if best:
        actions.append({
            "dot_color": "dot-green", "tag_class": "tag-low", "tag_label": "OPTIMISE",
            "text": f"Replicate {best[0]['name']}'s expense discipline across underperforming locations. Share SOP."
        })

    # Annualised run rate
    if data.total_expense > 0 and len(data.months) > 0:
        annual = data.total_expense * 12
        ytd = sum(data.expense_by_month.values())
        actions.append({
            "dot_color": "dot-blue", "tag_class": "tag-med", "tag_label": "BUDGET",
            "text": f"Annualised run rate {fmt_cr(annual)} expenses. "
                    f"YTD {fmt_cr(ytd)} in {len(data.months)}M. Budget alignment review due."
        })

    return actions[:10]


def _build_pnl_rows(detail_by_month, expense_by_month, total_by_month, months):
    """
    Build the P&L summary table rows.
    Returns: list of dicts [{label, values: {month: str}, is_header, is_negative}]
    """
    rows = []

    def _add_row(label, values_dict, is_header=False, is_negative=False):
        rows.append({
            "label": label,
            "values": {m: fmt_pnl_val(values_dict.get(m, 0)) for m in months},
            "is_header": is_header,
            "is_negative": is_negative,
        })

    def _add_section(label):
        rows.append({
            "label": label,
            "values": {m: "" for m in months},
            "is_header": True,
            "is_negative": False,
        })

    # MARGIN section
    _add_section("MARGIN")

    display_cols = [
        ("Parts Margin",     "Parts_Margin",      False),
        ("Accessory Margin", "Accessory_Margin",   False),
        ("Oil Margin",       "Oil_Margin",         False),
        ("Tyre Margin",      "Tyre_Margin",        False),
        ("Battery Margin",   "Battery_Margin",     False),
        ("Other Margin",     "Other_Margin",       False),
        ("VOR Charges",      "VOR Charges",        True),
    ]
    for display_name, col_name, is_neg in display_cols:
        if col_name in detail_by_month:
            vals = {months[i]: detail_by_month[col_name][i] for i in range(len(months))}
            _add_row(display_name, vals, is_negative=is_neg)

    # Total Parts Margin (sum of parts-related)
    parts_cols = ["Parts_Margin", "Accessory_Margin", "Oil_Margin", "Tyre_Margin", "Battery_Margin", "Other_Margin"]
    parts_total = {}
    for i, m in enumerate(months):
        total = sum(detail_by_month.get(c, [0]*len(months))[i] for c in parts_cols if c in detail_by_month)
        parts_total[m] = total
    _add_row("Total Parts Margin", parts_total, is_header=True)

    # Labour and income
    income_cols = [
        ("Net Labour",       LABOUR_COL,           False),
        ("OTC Income",       "OTC Income",         False),
        ("MSIL Labour Claim","MSIL Labour Claim",  False),
        ("FSC Income",       "FSC Income",         False),
        ("Dealer FOC",       "Dealer FOC",         True),
        ("Internal Consumption", "Internal Consumption", True),
    ]
    for display_name, col_name, is_neg in income_cols:
        if col_name in detail_by_month:
            vals = {months[i]: detail_by_month[col_name][i] for i in range(len(months))}
            _add_row(display_name, vals, is_negative=is_neg)

    # TOTAL MARGIN
    _add_row("TOTAL MARGIN", total_by_month, is_header=True)

    # EXPENSE section
    _add_section("EXPENSE")
    _add_row("Total Expense", expense_by_month, is_header=True, is_negative=True)

    # NET PROFIT
    net_profit_by_month = {m: total_by_month.get(m, 0) - expense_by_month.get(m, 0) for m in months}
    _add_row("NET PROFIT", net_profit_by_month, is_header=True, is_negative=True)

    return rows


def _generate_alerts(data, df, current_month):
    """
    Generate alert banners from data anomalies.
    Returns: list of dicts [{type, message, details}]
    """
    alerts = []

    # Net loss alert
    if data.net_profit < 0:
        alerts.append({
            "type": "loss",
            "message": "NET LOSS DETECTED — Immediate action required",
            "details": f"Business is operating at a net loss of {fmt_cr(abs(data.net_profit))} in {current_month}. "
                       "Margin cannot cover expenses."
        })

    # Negative labour alert
    if LABOUR_COL in df.columns and ADV_COL in df.columns:
        df_curr = df[df["Month Name"] == current_month]
        neg_adv = df_curr.groupby([ADV_COL, "Location Name"])[LABOUR_COL].sum().reset_index()
        neg_adv = neg_adv[neg_adv[LABOUR_COL] < 0].sort_values(LABOUR_COL)
        if not neg_adv.empty:
            parts = []
            for _, r in neg_adv.head(5).iterrows():
                parts.append(f"{r[ADV_COL]} ({r['Location Name']}) {fmt_cr(abs(_to_lakhs(r[LABOUR_COL])))}")
            alerts.append({
                "type": "neg_labour",
                "message": "NEGATIVE NET LABOUR DETECTED — Review required",
                "details": " | ".join(parts),
            })

    # Leakage alert
    if data.leakage_total > 1.0:  # > 1 Lakh
        alerts.append({
            "type": "leakage",
            "message": "Revenue leakage exceeds threshold",
            "details": f"Internal Consumption + VOR Charges = {fmt_cr(data.leakage_total)}",
        })

    return alerts


def prepare_pnl_data(df, exp_df, selected_months):
    """
    Master orchestrator: compute all P&L metrics from raw data.

    Args:
        df:              WSMIS main sheet DataFrame (with computed columns from app.py load_data)
        exp_df:          EXP. worksheet DataFrame
        selected_months: list of month strings from the global month picker

    Returns:
        PnLData dataclass with all computed results.
    """
    # Determine months to use (sorted by MONTH_ORDER)
    available = [m for m in MONTH_ORDER if m in df["Month Name"].unique()]
    if selected_months:
        months = [m for m in MONTH_ORDER if m in selected_months]
    else:
        months = available[-3:] if len(available) >= 3 else available

    if not months:
        months = available[-3:] if len(available) >= 3 else available

    current_month  = months[-1] if months else ""
    previous_month = months[-2] if len(months) >= 2 else current_month

    # 1. Margin computation
    total_by_month, category_by_month, detail_by_month = _compute_margin_by_month(df, months)

    # 2. Expense computation
    expense_by_month = _compute_expense_by_month(exp_df, months)

    # 3. Profit by month
    profit_by_month = {m: total_by_month.get(m, 0) - expense_by_month.get(m, 0) for m in months}

    # 4. KPIs
    curr_margin  = total_by_month.get(current_month, 0)
    curr_expense = expense_by_month.get(current_month, 0)
    curr_profit  = curr_margin - curr_expense
    prev_margin  = total_by_month.get(previous_month, 0)
    prev_expense = expense_by_month.get(previous_month, 0)
    prev_profit  = prev_margin - prev_expense

    # Leakage
    leakage = 0.0
    for col in LEAKAGE_COLUMNS:
        if col in detail_by_month and detail_by_month[col]:
            leakage += abs(detail_by_month[col][-1])

    # 5. Compositions
    margin_composition = {}
    for cat, vals in category_by_month.items():
        v = vals[-1] if vals else 0
        if v > 0:
            margin_composition[cat] = v

    expense_composition = _compute_expense_composition(exp_df, current_month)

    # 6. Location profitability
    locations = _compute_location_profitability(df, exp_df, current_month, previous_month)

    # Build partial data for insight/action generation
    data = PnLData(
        months=months,
        current_month=current_month,
        previous_month=previous_month,
        period_label=f"{months[0]} → {months[-1]}" if months else "",
        location_count=df["Location Name"].nunique(),
        record_count=len(df),
        total_margin=curr_margin,
        total_expense=curr_expense,
        net_profit=curr_profit,
        profit_margin_pct=_safe_pct(curr_profit, curr_margin),
        expense_ratio_pct=_safe_pct(curr_expense, curr_margin),
        leakage_total=leakage,
        prev_total_margin=prev_margin,
        prev_total_expense=prev_expense,
        prev_net_profit=prev_profit,
        prev_profit_margin_pct=_safe_pct(prev_profit, prev_margin),
        prev_expense_ratio_pct=_safe_pct(prev_expense, prev_margin),
        margin_by_month=total_by_month,
        expense_by_month=expense_by_month,
        profit_by_month=profit_by_month,
        margin_composition=margin_composition,
        expense_composition=expense_composition,
        margin_category_trend=category_by_month,
        locations=locations,
        pnl_rows=_build_pnl_rows(detail_by_month, expense_by_month, total_by_month, months),
    )

    # 7. Drivers and killers (need detail data)
    data.drivers = _generate_drivers(detail_by_month, months, locations)
    data.killers = _generate_killers(detail_by_month, months, df, current_month, exp_df)

    # 8. Insights and actions (need full data)
    data.insights = _generate_insights(data)
    data.actions  = _generate_actions(data)

    # 9. Alerts
    data.alerts = _generate_alerts(data, df, current_month)

    return data


# ═══════════════════════════════════════════════════════════════
#  CSS — Presentation constants
# ═══════════════════════════════════════════════════════════════

PNL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* reset & base */
.pnl-wrap { font-family: 'Inter', sans-serif; }

/* section heading */
.pnl-section-heading {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #94a3b8; margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.4rem; border-bottom: 1px solid #e2e8f0;
}

/* alert banner */
.pnl-alert-banner {
    background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
    padding: 0.6rem 1rem; margin-bottom: 1rem; font-size: 0.78rem; color: #991b1b;
}
.pnl-alert-banner strong { color: #dc2626; }
.pnl-alert-banner .alert-items { color: #b91c1c; margin-top: 3px; }

.pnl-success-banner {
    background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;
    padding: 0.6rem 1rem; margin-bottom: 1rem; font-size: 0.78rem; color: #166534;
}

/* kpi card */
.pnl-kpi-card {
    background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0;
    padding: 1rem 1.1rem; height: 100%;
}
.pnl-kpi-label {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: #64748b; margin-bottom: 0.4rem;
}
.pnl-kpi-value { font-size: 1.55rem; font-weight: 700; color: #0f172a; line-height: 1; }
.pnl-kpi-sub { font-size: 0.72rem; color: #94a3b8; margin-top: 0.3rem; }
.pnl-kpi-badge {
    display: inline-flex; align-items: center; gap: 3px;
    font-size: 0.7rem; font-weight: 600; padding: 2px 7px; border-radius: 9px; margin-top: 0.4rem;
}
.pnl-kpi-badge.up   { background: #dcfce7; color: #16a34a; }
.pnl-kpi-badge.down { background: #fee2e2; color: #dc2626; }
.pnl-kpi-badge.flat { background: #f1f5f9; color: #64748b; }

/* location table */
.pnl-loc-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
.pnl-loc-table th {
    text-align: left; font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.07em; text-transform: uppercase; color: #94a3b8;
    padding: 6px 10px; border-bottom: 1px solid #e2e8f0;
}
.pnl-loc-table td { padding: 7px 10px; border-bottom: 1px solid #f1f5f9; color: #1e293b; }
.pnl-loc-table tr:hover td { background: #f8fafc; }
.pnl-loc-table .rank-num {
    width: 22px; height: 22px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.65rem; font-weight: 700; color: #fff;
}
.rank-gold   { background: #f59e0b; }
.rank-silver { background: #94a3b8; }
.rank-bronze { background: #c08060; }
.rank-plain  { background: #cbd5e1; color: #475569; }
.rank-red    { background: #fee2e2; color: #dc2626; }

.pnl-pill {
    display: inline-block; padding: 1px 8px; border-radius: 8px; font-size: 0.68rem; font-weight: 600;
}
.pill-green  { background: #dcfce7; color: #16a34a; }
.pill-red    { background: #fee2e2; color: #dc2626; }
.pill-amber  { background: #fef3c7; color: #b45309; }
.pill-gray   { background: #f1f5f9; color: #64748b; }

/* chart card */
.pnl-chart-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 1rem 1.1rem;
}
.pnl-chart-card-title { font-size: 0.75rem; font-weight: 600; color: #1e293b; margin-bottom: 0.1rem; }
.pnl-chart-card-sub { font-size: 0.68rem; color: #94a3b8; margin-bottom: 0.75rem; }

/* insight card */
.pnl-insight-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 0.85rem 1rem; margin-bottom: 0.6rem; display: flex; gap: 0.75rem;
}
.pnl-insight-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }
.pnl-insight-title { font-size: 0.8rem; font-weight: 600; color: #1e293b; margin-bottom: 2px; }
.pnl-insight-body  { font-size: 0.74rem; color: #64748b; line-height: 1.45; }
.pnl-insight-badge {
    display: inline-block; font-size: 0.62rem; font-weight: 700; letter-spacing: 0.05em;
    padding: 1px 6px; border-radius: 6px; text-transform: uppercase; margin-top: 4px;
}
.badge-high { background: #fee2e2; color: #dc2626; }
.badge-med  { background: #fef3c7; color: #b45309; }
.badge-low  { background: #f0fdf4; color: #16a34a; }

/* action panel */
.pnl-action-panel {
    background: #0f172a; border-radius: 10px; padding: 1rem 1.1rem; color: #e2e8f0;
}
.pnl-action-panel .ap-title {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #94a3b8; margin-bottom: 0.75rem;
}
.pnl-action-item {
    display: flex; align-items: flex-start; gap: 0.6rem;
    padding: 0.55rem 0; border-bottom: 1px solid #1e293b; font-size: 0.76rem;
}
.pnl-action-item:last-child { border-bottom: none; }
.pnl-action-dot {
    width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; margin-top: 5px;
}
.dot-red    { background: #ef4444; }
.dot-amber  { background: #f59e0b; }
.dot-green  { background: #22c55e; }
.dot-blue   { background: #3b82f6; }
.pnl-action-text { color: #cbd5e1; flex: 1; }
.pnl-action-tag {
    font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
    padding: 1px 5px; border-radius: 4px; flex-shrink: 0; margin-top: 2px;
}
.tag-urgent { background: #ef4444; color: #fff; }
.tag-med    { background: #f59e0b; color: #fff; }
.tag-low    { background: #22c55e; color: #fff; }
"""


# ═══════════════════════════════════════════════════════════════
#  PRESENTATION LAYER — Streamlit rendering
# ═══════════════════════════════════════════════════════════════

def _inject_css():
    """Inject the P&L dashboard CSS once."""
    import streamlit as st
    st.markdown(f"<style>{PNL_CSS}</style>", unsafe_allow_html=True)


def _pill(text, color="gray"):
    return f'<span class="pnl-pill pill-{color}">{text}</span>'


def _render_header(data):
    """Render page title and subtitle."""
    import streamlit as st
    st.markdown(
        '<div style="font-size:1.3rem;font-weight:700;color:#0f172a;margin-bottom:0.2rem">'
        'Profit &amp; Loss — Executive Dashboard</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div style="font-size:0.8rem;color:#64748b;margin-bottom:1.25rem">'
        f'{data.period_label} &nbsp;·&nbsp; MoM comparison &nbsp;·&nbsp; '
        f'{data.location_count} locations &nbsp;·&nbsp; Combined Margin &amp; Expense view</div>',
        unsafe_allow_html=True
    )


def _render_alert_banners(data):
    """Render alert banners based on computed alerts."""
    import streamlit as st
    for alert in data.alerts:
        if alert["type"] == "loss":
            st.markdown(f'''
            <div class="pnl-alert-banner">
              🚨 <strong>{alert["message"]}</strong><br>
              <div class="alert-items">{alert["details"]}</div>
            </div>''', unsafe_allow_html=True)
        elif alert["type"] == "neg_labour":
            st.markdown(f'''
            <div class="pnl-alert-banner">
              ⚠️ <strong>{alert["message"]}</strong>: {alert["details"]}
            </div>''', unsafe_allow_html=True)
        elif alert["type"] == "leakage":
            st.markdown(f'''
            <div class="pnl-alert-banner">
              ⚠️ <strong>{alert["message"]}</strong>: {alert["details"]}
            </div>''', unsafe_allow_html=True)


def _render_kpi_cards(data):
    """Render Section 1: Executive Profit Summary KPIs."""
    import streamlit as st

    st.markdown(
        f'<div class="pnl-section-heading">① Executive Profit Summary — {data.current_month}</div>',
        unsafe_allow_html=True
    )

    mom_profit_chg  = _mom_delta(data.net_profit, data.prev_net_profit)
    mom_margin_chg  = _mom_delta(data.total_margin, data.prev_total_margin)
    mom_expense_chg = _mom_delta(data.total_expense, data.prev_total_expense)
    profit_pct_chg  = data.profit_margin_pct - data.prev_profit_margin_pct
    expense_pct_chg = data.expense_ratio_pct - data.prev_expense_ratio_pct

    kpis = [
        ("Net Profit",      data.net_profit,        mom_profit_chg,  "MoM vs " + data.previous_month, True),
        ("Total Margin",    data.total_margin,       mom_margin_chg,  "Revenue contribution",          True),
        ("Total Expense",   data.total_expense,      mom_expense_chg, "Operating cost",                False),
        ("Profit Margin %", data.profit_margin_pct,  profit_pct_chg,  "Net margin ratio",              True),
        ("Expense Ratio %", data.expense_ratio_pct,  expense_pct_chg, "Cost as % of margin",           False),
        ("Revenue Leakage", data.leakage_total,      0,               "IC + VOR drag",                 False),
    ]

    cols = st.columns(6)
    for col, (label, val, chg, sub, higher_is_better) in zip(cols, kpis):
        if label.endswith("%"):
            val_str = f"{val:.1f}%"
            chg_str = f"{chg:+.1f}pp"
        else:
            val_str = fmt_cr(val)
            chg_str = f"MoM {fmt_cr(chg)}"

        if chg == 0:
            badge_cls, arrow = "flat", "—"
        elif (chg > 0) == higher_is_better:
            badge_cls, arrow = "up", "▲"
        else:
            badge_cls, arrow = "down", "▼"

        col.markdown(f'''
        <div class="pnl-kpi-card">
          <div class="pnl-kpi-label">{label}</div>
          <div class="pnl-kpi-value">{val_str}</div>
          <div class="pnl-kpi-sub">{sub}</div>
          <span class="pnl-kpi-badge {badge_cls}">{arrow} {chg_str}</span>
        </div>''', unsafe_allow_html=True)


def _render_trend_and_bridge(data):
    """Render Section 2: Margin vs Expense Trend + Profit Bridge."""
    import streamlit as st
    import plotly.graph_objects as go

    st.markdown(
        '<div class="pnl-section-heading">② Margin vs Expense Trend &amp; Profit Bridge</div>',
        unsafe_allow_html=True
    )

    col_trend, col_bridge = st.columns([3, 2])
    months = data.months
    margin_vals  = [data.margin_by_month.get(m, 0) for m in months]
    expense_vals = [data.expense_by_month.get(m, 0) for m in months]
    profit_vals  = [data.profit_by_month.get(m, 0) for m in months]

    with col_trend:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=months, y=margin_vals, name="Total Margin",
            marker_color=TREND_COLORS["margin"], opacity=0.85,
        ))
        fig_trend.add_trace(go.Bar(
            x=months, y=expense_vals, name="Total Expense",
            marker_color=TREND_COLORS["expense"], opacity=0.85,
        ))
        fig_trend.add_trace(go.Scatter(
            x=months, y=profit_vals, name="Net Profit",
            line=dict(color=TREND_COLORS["profit"], width=2.5), mode="lines+markers",
            marker=dict(size=7),
        ))
        fig_trend.update_layout(
            barmode="group", height=280,
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            legend=dict(orientation="h", y=1.08, font_size=11),
            margin=dict(t=30, b=30, l=10, r=10),
            yaxis=dict(tickprefix="₹", ticksuffix="L", gridcolor="#f1f5f9", title=None),
            xaxis=dict(showgrid=False),
            font=dict(family="Inter", size=11),
        )
        st.markdown('<div class="pnl-chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="pnl-chart-card-title">Margin vs Expense Trend</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="pnl-chart-card-sub">₹ Lakhs · {data.period_label} · '
            f'bars = absolute, line = net profit</div>',
            unsafe_allow_html=True
        )
        st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_bridge:
        if len(months) >= 2:
            prev_profit   = data.prev_net_profit
            delta_margin  = _mom_delta(data.total_margin, data.prev_total_margin)
            delta_expense = -_mom_delta(data.total_expense, data.prev_total_expense)
            apr_profit    = data.net_profit

            labels  = [f"{data.previous_month} Profit", "Margin Δ", "Expense Δ", f"{data.current_month} Profit"]
            values  = [prev_profit, delta_margin, delta_expense, 0]
            measure = ["absolute", "relative", "relative", "total"]

            fig_wf = go.Figure(go.Waterfall(
                orientation="v", measure=measure, x=labels, y=values,
                connector={"line": {"color": "#e2e8f0", "width": 1}},
                increasing={"marker": {"color": "#22c55e"}},
                decreasing={"marker": {"color": "#ef4444"}},
                totals={"marker": {"color": "#3b82f6"}},
                text=[fmt_cr(v) for v in [prev_profit, delta_margin, delta_expense, apr_profit]],
                textposition="outside",
            ))
            fig_wf.update_layout(
                height=280,
                plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
                margin=dict(t=30, b=30, l=10, r=10),
                yaxis=dict(tickprefix="₹", ticksuffix="L", gridcolor="#f1f5f9", title=None),
                xaxis=dict(showgrid=False),
                font=dict(family="Inter", size=10),
                showlegend=False,
            )
            st.markdown('<div class="pnl-chart-card">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="pnl-chart-card-title">Profit Bridge — {data.previous_month} → {data.current_month}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                '<div class="pnl-chart-card-sub">What drove the profit change month-on-month</div>',
                unsafe_allow_html=True
            )
            st.plotly_chart(fig_wf, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)


def _render_location_ranking(data):
    """Render Section 3: Location Profitability Ranking."""
    import streamlit as st
    import plotly.graph_objects as go

    st.markdown(
        f'<div class="pnl-section-heading">③ Location Profitability Ranking — {data.current_month}</div>',
        unsafe_allow_html=True
    )

    col_table, col_bar = st.columns([3, 2])
    sorted_locs = data.locations
    rank_colors = {0: "rank-gold", 1: "rank-silver", 2: "rank-bronze"}

    with col_table:
        rows_html = ""
        for i, loc in enumerate(sorted_locs):
            status_map = {
                "nodata": _pill("No Data", "gray"),
                "loss":   _pill("Loss", "red"),
                "watch":  _pill("Watch", "amber"),
                "good":   _pill("Profit", "green"),
            }
            status_pill = status_map.get(loc["status"], _pill("—", "gray"))

            mom_color = "#16a34a" if loc["mom_p"] >= 0 else "#dc2626"
            mom_arrow = "▲" if loc["mom_p"] >= 0 else "▼"
            mom_fmt = f'<span style="color:{mom_color}">{mom_arrow} {abs(loc["mom_p"]):.1f}L</span>'
            profit_color = "#16a34a" if loc["profit"] >= 0 else "#dc2626"
            rc = rank_colors.get(i, "rank-plain") if loc["profit"] > 0 else "rank-red"

            rows_html += f'''
            <tr>
              <td><span class="rank-num {rc}">{i+1}</span></td>
              <td><strong>{loc["name"]}</strong></td>
              <td>{fmt_cr(loc["margin"])}</td>
              <td>{fmt_cr(loc["expense"])}</td>
              <td style="color:{profit_color};font-weight:700">{fmt_cr(loc["profit"])}</td>
              <td>{mom_fmt}</td>
              <td>{status_pill}</td>
              <td style="color:#94a3b8">{loc["anomalies"] if loc["anomalies"] else "—"} ⚠</td>
            </tr>'''

        st.markdown(f'''
        <div class="pnl-chart-card" style="padding:0.85rem">
          <div class="pnl-chart-card-title" style="padding:0 0.25rem 0.5rem">All Locations · Profit Ranking</div>
          <table class="pnl-loc-table">
            <thead>
              <tr>
                <th>#</th><th>Location</th><th>Margin</th><th>Expense</th>
                <th>Net Profit</th><th>MoM Δ</th><th>Status</th><th>Alerts</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>''', unsafe_allow_html=True)

    with col_bar:
        top_locs = sorted_locs[:10]
        names   = [l["name"] for l in top_locs]
        profits = [l["profit"] for l in top_locs]
        bar_colors = ["#22c55e" if p >= 0 else "#ef4444" for p in profits]

        fig_bar = go.Figure(go.Bar(
            x=profits, y=names, orientation="h",
            marker_color=bar_colors,
            text=[fmt_cr(p) for p in profits],
            textposition="outside",
        ))
        fig_bar.update_layout(
            height=340,
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            margin=dict(t=20, b=20, l=10, r=60),
            xaxis=dict(tickprefix="₹", ticksuffix="L", gridcolor="#f1f5f9",
                       zeroline=True, zerolinecolor="#cbd5e1"),
            yaxis=dict(showgrid=False, autorange="reversed"),
            font=dict(family="Inter", size=11),
            showlegend=False,
        )
        st.markdown('<div class="pnl-chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="pnl-chart-card-title">Top 10 Locations by Net Profit</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="pnl-chart-card-sub">₹ Lakhs · {data.current_month} · green = profit, red = loss</div>',
            unsafe_allow_html=True
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)


def _render_composition_charts(data):
    """Render Section 4: Margin Mix + Expense Mix + Category Trend."""
    import streamlit as st
    import plotly.graph_objects as go

    st.markdown(
        f'<div class="pnl-section-heading">④ Margin Composition &amp; Expense Composition — {data.current_month}</div>',
        unsafe_allow_html=True
    )

    col_mcomp, col_ecomp, col_trend = st.columns([2, 2, 3])

    # Margin mix donut
    with col_mcomp:
        mc_labels = list(data.margin_composition.keys())
        mc_values = list(data.margin_composition.values())
        colors = MARGIN_COLORS[:len(mc_labels)]

        fig_mcomp = go.Figure(go.Pie(
            labels=mc_labels, values=mc_values,
            marker=dict(colors=colors),
            textinfo="label+percent", textfont_size=10, hole=0.45,
        ))
        fig_mcomp.update_layout(
            height=260, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="#ffffff", font=dict(family="Inter", size=10), showlegend=False,
        )
        st.markdown('<div class="pnl-chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="pnl-chart-card-title">Margin Mix</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pnl-chart-card-sub">{data.current_month} · by category</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_mcomp, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # Expense mix donut
    with col_ecomp:
        if data.expense_composition:
            ec_labels = list(data.expense_composition.keys())
            ec_values = list(data.expense_composition.values())
            ec_colors = EXPENSE_COLORS[:len(ec_labels)]

            fig_ecomp = go.Figure(go.Pie(
                labels=ec_labels, values=ec_values,
                marker=dict(colors=ec_colors),
                textinfo="label+percent", textfont_size=10, hole=0.45,
            ))
            fig_ecomp.update_layout(
                height=260, margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="#ffffff", font=dict(family="Inter", size=10), showlegend=False,
            )
            st.markdown('<div class="pnl-chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="pnl-chart-card-title">Expense Mix</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="pnl-chart-card-sub">{data.current_month} · by category</div>', unsafe_allow_html=True)
            st.plotly_chart(fig_ecomp, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No expense composition data available.")

    # Margin category trend (stacked bar)
    with col_trend:
        fig_stack = go.Figure()
        cat_colors = MARGIN_COLORS
        for idx, (cat, vals) in enumerate(data.margin_category_trend.items()):
            fig_stack.add_trace(go.Bar(
                name=cat, x=data.months, y=vals,
                marker_color=cat_colors[idx % len(cat_colors)], opacity=0.88,
            ))
        fig_stack.update_layout(
            barmode="stack", height=260,
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            margin=dict(t=15, b=20, l=10, r=10),
            yaxis=dict(tickprefix="₹", ticksuffix="L", gridcolor="#f1f5f9", title=None),
            xaxis=dict(showgrid=False),
            legend=dict(orientation="h", y=1.12, font_size=10),
            font=dict(family="Inter", size=10),
        )
        st.markdown('<div class="pnl-chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="pnl-chart-card-title">Margin Category Trend (Stacked)</div>', unsafe_allow_html=True)
        st.markdown('<div class="pnl-chart-card-sub">₹ Lakhs · which categories are growing vs shrinking</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_stack, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)


def _render_drivers_killers(data):
    """Render Section 5: Top Profit Drivers & Killers."""
    import streamlit as st

    st.markdown(
        f'<div class="pnl-section-heading">⑤ Top Profit Drivers &amp; Killers — {data.current_month}</div>',
        unsafe_allow_html=True
    )

    col_drivers, col_killers = st.columns(2)

    with col_drivers:
        st.markdown('<div class="pnl-chart-card" style="padding:0.85rem">', unsafe_allow_html=True)
        st.markdown('<div class="pnl-chart-card-title">✅ Top Profit Drivers</div>', unsafe_allow_html=True)
        st.markdown('<div class="pnl-chart-card-sub">What is making money this month</div>', unsafe_allow_html=True)
        for d in data.drivers:
            st.markdown(f'''
            <div style="display:flex;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid #f1f5f9;align-items:flex-start">
              <span style="font-size:1.15rem">{d["icon"]}</span>
              <div style="flex:1">
                <div style="font-size:0.8rem;font-weight:600;color:#1e293b">{d["name"]} &nbsp;<span style="color:#16a34a;font-weight:700">{d["value"]}</span></div>
                <div style="font-size:0.7rem;color:#64748b">{d["note"]} — <em>{d["trend"]}</em></div>
              </div>
            </div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_killers:
        st.markdown('<div class="pnl-chart-card" style="padding:0.85rem">', unsafe_allow_html=True)
        st.markdown('<div class="pnl-chart-card-title">🚨 Top Profit Killers</div>', unsafe_allow_html=True)
        st.markdown('<div class="pnl-chart-card-sub">What is destroying margin — act first</div>', unsafe_allow_html=True)
        for k in data.killers:
            st.markdown(f'''
            <div style="display:flex;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid #f1f5f9;align-items:flex-start">
              <span style="font-size:1.15rem">{k["icon"]}</span>
              <div style="flex:1">
                <div style="font-size:0.8rem;font-weight:600;color:#1e293b">{k["name"]} &nbsp;<span style="color:#dc2626;font-weight:700">{k["value"]}</span> {_pill(k["tag"], "red")}</div>
                <div style="font-size:0.7rem;color:#64748b">{k["note"]}</div>
              </div>
            </div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def _render_insights_and_actions(data):
    """Render Section 6: Executive Insights & Action Panel."""
    import streamlit as st

    st.markdown(
        '<div class="pnl-section-heading">⑥ Executive Insights &amp; Action Panel</div>',
        unsafe_allow_html=True
    )

    col_ins, col_act = st.columns([3, 2])

    with col_ins:
        for ins in data.insights:
            badge_cls = {"HIGH": "badge-high", "MED": "badge-med", "LOW": "badge-low"}.get(ins["level"], "badge-med")
            st.markdown(f'''
            <div class="pnl-insight-card">
              <span class="pnl-insight-icon">{ins["icon"]}</span>
              <div>
                <div class="pnl-insight-title">{ins["title"]}</div>
                <div class="pnl-insight-body">{ins["body"]}</div>
                <span class="pnl-insight-badge {badge_cls}">{ins["level"]}</span>
              </div>
            </div>''', unsafe_allow_html=True)

    with col_act:
        count = len(data.actions)
        st.markdown(f'''
        <div class="pnl-action-panel">
          <div class="ap-title">🎯 Executive Action Panel — {count} Recommended Actions</div>''',
          unsafe_allow_html=True)
        for act in data.actions:
            st.markdown(f'''
          <div class="pnl-action-item">
            <div class="pnl-action-dot {act["dot_color"]}"></div>
            <div class="pnl-action-text">{act["text"]}</div>
            <span class="pnl-action-tag {act["tag_class"]}">{act["tag_label"]}</span>
          </div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def _render_pnl_summary_table(data):
    """Render Section 7: Full P&L Summary Table."""
    import streamlit as st

    st.markdown(
        '<div class="pnl-section-heading">⑦ Full P&amp;L Summary Table — All Categories</div>',
        unsafe_allow_html=True
    )

    months = data.months
    rows_html = ""
    for row in data.pnl_rows:
        style = "font-weight:700;background:#f8fafc;" if row["is_header"] else ""
        tds = ""
        for m in months:
            val_str = row["values"].get(m, "—")
            is_neg = row["is_negative"] and val_str.startswith("-")
            color = "#dc2626" if is_neg else ("#16a34a" if row["is_header"] and not row["is_negative"] else "#64748b")
            weight = "700" if row["is_header"] else "400"
            tds += (f'<td style="padding:6px 10px;border-bottom:1px solid #f1f5f9;'
                    f'text-align:right;color:{color};font-weight:{weight}">{val_str}</td>')

        rows_html += f'''
        <tr style="{style}">
          <td style="padding:6px 10px;border-bottom:1px solid #f1f5f9">{row["label"]}</td>
          {tds}
        </tr>'''

    # Build header
    th_style = ('text-align:right;padding:7px 10px;font-size:0.65rem;font-weight:700;'
                'letter-spacing:0.07em;text-transform:uppercase;color:#94a3b8')
    th_left  = th_style.replace("text-align:right", "text-align:left")
    header_ths = f'<th style="{th_left}">Category</th>'
    for m in months:
        header_ths += f'<th style="{th_style}">{m}</th>'

    st.markdown(f'''
    <div class="pnl-chart-card" style="padding:0.85rem">
      <div class="pnl-chart-card-title">Consolidated P&amp;L — Margin &amp; Expense Combined</div>
      <div class="pnl-chart-card-sub">All figures in Indian denomination (Cr = ₹Crore, L = ₹Lakh, K = ₹Thousand) · {data.period_label}</div>
      <table style="width:100%;border-collapse:collapse;font-size:0.78rem">
        <thead>
          <tr style="border-bottom:2px solid #e2e8f0">{header_ths}</tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def render_in_streamlit(df, exp_df, selected_months,
                        locations=None, report_period=None):
    """
    Single entry point for app.py integration.

    Args:
        df:              WSMIS main sheet DataFrame (with computed columns from load_data)
        exp_df:          EXP. worksheet DataFrame
        selected_months: list of month strings from the global month picker
        locations:       optional location filter (list of location names)
        report_period:   optional period label override

    Renders directly into Streamlit using native widgets.
    """
    import streamlit as st

    # Apply location filter if provided
    if locations:
        df = df[df["Location Name"].isin(locations)]
        if exp_df is not None and not exp_df.empty:
            exp_df = exp_df[exp_df["Location"].isin(locations)]

    # Compute all P&L data
    data = prepare_pnl_data(df, exp_df, selected_months)

    # Override period label if provided
    if report_period:
        data.period_label = report_period

    # Render
    _inject_css()
    _render_header(data)
    _render_alert_banners(data)
    _render_kpi_cards(data)
    _render_trend_and_bridge(data)
    _render_location_ranking(data)
    _render_composition_charts(data)
    _render_drivers_killers(data)
    _render_insights_and_actions(data)
    _render_pnl_summary_table(data)
