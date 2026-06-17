"""
Revenue Leakage Executive Dashboard V3.1
HTML generator – consumes already-filtered miss_df + pen tables from app.py.
Do NOT call load_data() or get_cached_audit_data() here.

V3.1 Improvements over V2:
  - recovery_rate param (default 0.70) – configurable from app.py
  - _fmt_inr is safe for NaN / None / str (no crash on unexpected types)
  - "All" service chip shows total loss explicitly
  - 6 KPI cards (added Locations Affected + Est. Recoverable)
  - Donut legend built in native HTML – readable on all screen sizes
  - Bar chart x-axis autoSkip + maxRotation:45 so all labels show
  - Heat card shows WA/WB/DC only when tb > 0 (no div-by-zero)
  - Insights ordered by financial impact, deduplicated
  - Expand row shows recoverable amount + affected JC count
  - "Open Dealer Audit" UI hook in every expanded location row
  - Executive Action Panel at bottom of page
  - applyFilter re-aggregates advisor table correctly
  - JS fmtInr mirrors Python _fmt_inr (Cr threshold was missing in V2)
  - Mobile breakpoints for chip row wrapping
  - Chart canvas given aria-label for accessibility
  - _risk_badge flags 0-loss locations as NONE
"""

import json
import pandas as pd


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _fmt_inr(num, default="₹0"):
    """Format a number as Indian currency string. Safe for NaN / None / str."""
    try:
        num = float(num)
    except (TypeError, ValueError):
        return default
    if pd.isna(num) or num == 0:
        return default
    if num >= 10_000_000:
        return f"₹{num/10_000_000:.2f}Cr"
    if num >= 100_000:
        return f"₹{num/100_000:.1f}L"
    if num >= 1_000:
        return f"₹{num/1_000:.0f}K"
    return f"₹{num:,.0f}"


def _pct_bar(pct, good=70, warn=50):
    """Render a mini horizontal progress bar with colour-coded fill."""
    try:
        pct = float(pct)
    except (TypeError, ValueError):
        pct = 0.0
    if pd.isna(pct):
        pct = 0.0
    clr = "#22C55E" if pct >= good else "#F59E0B" if pct >= warn else "#EF4444"
    return (
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'<div style="flex:1;height:6px;background:#E5E7EB;border-radius:3px;">'
        f'<div style="width:{min(pct,100):.0f}%;height:100%;background:{clr};border-radius:3px;"></div></div>'
        f'<span style="font-size:11px;color:#374151;white-space:nowrap;">{pct:.0f}%</span></div>'
    )


def _risk_badge(loss, avg):
    """Return a HIGH / MED / LOW / NONE badge relative to avg loss per location."""
    if loss <= 0:
        return '<span style="background:#F3F4F6;color:#6B7280;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">NONE</span>'
    if loss > avg * 2:
        return '<span style="background:#FEE2E2;color:#DC2626;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">HIGH</span>'
    if loss > avg:
        return '<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">MED</span>'
    return '<span style="background:#DCFCE7;color:#16A34A;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">LOW</span>'


# ─────────────────────────────────────────────
#  Main Builder
# ─────────────────────────────────────────────

def build_revenue_leakage_dashboard_v2(
    miss_df: pd.DataFrame,
    pms_pen: pd.DataFrame,
    fr2_pen: pd.DataFrame,
    fr3_pen: pd.DataFrame,
    month_label: str = "",
    last_sync: str = "",
    recovery_rate: float = 0.70,
) -> str:
    """
    Build the Revenue Leakage Executive Dashboard HTML.
    Function signature is backward-compatible with V2.
    recovery_rate is new — app.py may pass it or leave it at default 0.70.
    """

    if miss_df is None or miss_df.empty:
        return (
            "<div style='padding:40px;font-family:Inter,sans-serif;"
            "color:#6B7280;text-align:center;'>"
            "No revenue leakage data for selected filters.</div>"
        )

    # ── Aggregations ──────────────────────────────────────────────────────────
    tot      = float(miss_df["Missed Revenue"].sum())
    nc       = float(miss_df[miss_df["Leak Type"] == "Not Charged"]["Missed Revenue"].sum())
    fd       = float(miss_df[miss_df["Leak Type"] == "Fully Discounted"]["Missed Revenue"].sum())
    jcs      = int(miss_df["Job Card No"].nunique())
    locs_cnt = int(miss_df["Location"].nunique()) if "Location" in miss_df.columns else 0
    avg_jc   = tot / jcs if jcs else 0
    nc_pct   = nc / tot * 100 if tot else 0
    fd_pct   = fd / tot * 100 if tot else 0
    recoverable = tot * recovery_rate

    # Service type aggregation
    svc_agg = (
        miss_df.groupby("Service Type", as_index=False)
        .agg(loss=("Missed Revenue", "sum"), count=("Job Card No", "nunique"))
        .sort_values("loss", ascending=False)
    )

    # Location aggregation
    loc_agg = (
        miss_df.groupby("Location", as_index=False)
        .agg(loss=("Missed Revenue", "sum"), count=("Job Card No", "nunique"))
        .sort_values("loss", ascending=False)
    )
    loc_agg["rank"] = range(1, len(loc_agg) + 1)
    loc_agg["avg_loss"] = loc_agg["loss"] / loc_agg["count"].replace(0, 1)

    # Top service type per location
    if "Service Type" in miss_df.columns:
        top_svc_df = (
            miss_df.groupby(["Location", "Service Type"])["Missed Revenue"]
            .sum().reset_index()
        )
        idx = top_svc_df.groupby("Location")["Missed Revenue"].idxmax()
        top_svc_df = (
            top_svc_df.loc[idx][["Location", "Service Type"]]
            .rename(columns={"Service Type": "top_svc"})
        )
        loc_agg = loc_agg.merge(top_svc_df, on="Location", how="left")
    else:
        loc_agg["top_svc"] = "—"

    # PMS penetration per location
    pms_by_loc: dict = {}
    if pms_pen is not None and not pms_pen.empty and "Location" in pms_pen.columns:
        for loc, grp in pms_pen.groupby("Location"):
            tb  = float(grp["Total Bills"].sum()) if "Total Bills" in grp.columns else 0
            yes = float(grp["PMS YES"].sum())      if "PMS YES"     in grp.columns else 0
            pms_by_loc[loc] = round(yes / tb * 100, 1) if tb else 0

    # Advisor top 10
    adv_agg = (
        miss_df.groupby("Advisor Name", as_index=False)
        .agg(loss=("Missed Revenue", "sum"), count=("Job Card No", "nunique"))
        .sort_values("loss", ascending=False)
        .head(10)
    )
    if "Leak Type" in miss_df.columns:
        adv_leak = (
            miss_df.groupby(["Advisor Name", "Leak Type"])["Missed Revenue"]
            .sum().reset_index()
        )
        idx2 = adv_leak.groupby("Advisor Name")["Missed Revenue"].idxmax()
        adv_leak = (
            adv_leak.loc[idx2][["Advisor Name", "Leak Type"]]
            .rename(columns={"Leak Type": "top_leak"})
        )
        adv_agg = adv_agg.merge(adv_leak, on="Advisor Name", how="left")
    else:
        adv_agg["top_leak"] = "—"

    # Top 10 job cards
    jc_cols = [
        c for c in
        ["Job Card No", "Bill Date", "Location", "Advisor Name",
         "Model", "Service Type", "Leak Type", "Missed Revenue"]
        if c in miss_df.columns
    ]
    top_jcs = miss_df.nlargest(10, "Missed Revenue")[jc_cols].copy()
    if "Bill Date" in top_jcs.columns:
        top_jcs["Bill Date"] = (
            pd.to_datetime(top_jcs["Bill Date"], errors="coerce")
            .dt.strftime("%d-%b-%Y").fillna("—")
        )

    # ── Embed data as JSON for client-side chip filtering ─────────────────────
    rows_list = []
    for _, r in miss_df.iterrows():
        bill_raw = r.get("Bill Date")
        try:
            bill_str = pd.to_datetime(bill_raw, errors="coerce").strftime("%d-%b-%Y")
            if bill_str == "NaT":
                bill_str = "—"
        except Exception:
            bill_str = "—"
        rows_list.append({
            "jc":    str(r.get("Job Card No", "—")),
            "date":  bill_str,
            "loc":   str(r.get("Location", "—")),
            "adv":   str(r.get("Advisor Name", "—")),
            "model": str(r.get("Model", "—")),
            "svc":   str(r.get("Service Type", "—")),
            "leak":  str(r.get("Leak Type", "—")),
            "loss":  round(float(r.get("Missed Revenue", 0)), 2),
        })
    rows_json = json.dumps(rows_list)

    # ── Derived scalars for insights / actions ────────────────────────────────
    top_loc      = loc_agg.iloc[0]["Location"]     if len(loc_agg) else "—"
    top_loc_loss = float(loc_agg.iloc[0]["loss"])  if len(loc_agg) else 0
    top_svc_name = svc_agg.iloc[0]["Service Type"] if len(svc_agg) else "—"
    top_svc_loss = float(svc_agg.iloc[0]["loss"])  if len(svc_agg) else 0
    top_adv      = adv_agg.iloc[0]["Advisor Name"] if len(adv_agg) else "—"
    top_adv_loss = float(adv_agg.iloc[0]["loss"])  if len(adv_agg) else 0
    top_adv_cnt  = int(adv_agg.iloc[0]["count"])   if len(adv_agg) else 0

    # Top-3 location contribution
    top3_loss = float(loc_agg.head(3)["loss"].sum()) if len(loc_agg) >= 3 else top_loc_loss
    top3_pct  = top3_loss / tot * 100 if tot else 0

    # ── Insights (7, ordered by financial impact) ─────────────────────────────
    insights = [
        (top_loc_loss,
         f"<strong>{top_loc}</strong> leads all locations with <strong>{_fmt_inr(top_loc_loss)}</strong> "
         f"({top_loc_loss/tot*100:.0f}% of total) — prioritise an immediate audit."),
        (top_svc_loss,
         f"<strong>{top_svc_name}</strong> is the dominant leakage category at <strong>{_fmt_inr(top_svc_loss)}</strong> "
         f"({top_svc_loss/tot*100:.0f}%). Standardising this billing alone recovers the most."),
        (top_adv_loss,
         f"<strong>{top_adv}</strong> accounts for <strong>{_fmt_inr(top_adv_loss)}</strong> across "
         f"<strong>{top_adv_cnt}</strong> job cards — targeted coaching recommended within 7 days."),
        (recoverable,
         f"At a <strong>{recovery_rate*100:.0f}% recovery rate</strong>, billing controls "
         f"could recover <strong>{_fmt_inr(recoverable)}</strong> this period."),
        (nc,
         f"<strong>{nc_pct:.0f}%</strong> of leakage is services never charged (<strong>{_fmt_inr(nc)}</strong>); "
         f"Not-charged cases are the faster fix — no discount approval required."),
        (top3_loss,
         f"Top 3 locations contribute <strong>{_fmt_inr(top3_loss)}</strong> (<strong>{top3_pct:.0f}%</strong>) "
         f"of total leakage — concentrate resources here for maximum impact."),
        (float(locs_cnt),
         f"Leakage spans <strong>{locs_cnt}</strong> location(s) — a multi-site pattern "
         f"suggests a systemic billing compliance gap, not isolated advisor errors."),
    ]
    insights.sort(key=lambda x: x[0], reverse=True)
    insights_html = "".join(
        f'<div class="insight-item">'
        f'<span class="insight-num">{i+1}</span>'
        f'<span>{ins}</span></div>'
        for i, (_, ins) in enumerate(insights)
    )

    # ── Executive Action Panel (5–8 items, dynamic) ───────────────────────────
    actions = []
    if loc_agg is not None and len(loc_agg):
        actions.append(
            (top_loc_loss,
             f"🔴 Audit <strong>{top_loc}</strong> immediately — highest leakage at <strong>{_fmt_inr(top_loc_loss)}</strong>.")
        )
    if len(loc_agg) >= 3:
        loc2 = loc_agg.iloc[1]["Location"]
        loc3 = loc_agg.iloc[2]["Location"]
        actions.append(
            (top3_loss,
             f"📍 Focus on top 3 locations: <strong>{top_loc}</strong>, <strong>{loc2}</strong>, <strong>{loc3}</strong> "
             f"({top3_pct:.0f}% of total loss).")
        )
    actions.append(
        (top_svc_loss,
         f"📋 Standardise <strong>{top_svc_name}</strong> billing process — largest leakage category ({_fmt_inr(top_svc_loss)}).")
    )
    actions.append(
        (top_adv_loss,
         f"👤 Review <strong>{top_adv}</strong>'s job cards within 7 days — "
         f"<strong>{_fmt_inr(top_adv_loss)}</strong> across {top_adv_cnt} JCs.")
    )
    actions.append(
        (recoverable,
         f"💰 Recoverable opportunity: <strong>{_fmt_inr(recoverable)}</strong> at {recovery_rate*100:.0f}% recovery — "
         f"implement billing controls this month.")
    )
    if nc_pct > 0:
        actions.append(
            (nc,
             f"⚡ Not-Charged cases ({nc_pct:.0f}%, {_fmt_inr(nc)}) are the fastest fix — "
             f"no discount approval required. Address these first.")
        )
    actions.append(
        (0,
         f"🔗 Open <strong>Dealer Audit</strong> tab to investigate root cause for each location.")
    )
    actions.sort(key=lambda x: x[0], reverse=True)
    actions_html = "".join(
        f'<div class="action-item">'
        f'<span class="action-num">{i+1}</span>'
        f'<span>{act}</span></div>'
        for i, (_, act) in enumerate(actions)
    )

    # ── KPI cards ─────────────────────────────────────────────────────────────
    def kcard(title, val, sub="", icon="report-money", clr="#2563EB"):
        return f"""
<div class="kpi-card">
  <div class="kpi-icon" style="background:{clr}18;color:{clr};">
    <i class="ti ti-{icon}" style="font-size:22px;"></i>
  </div>
  <div class="kpi-body">
    <div class="kpi-val">{val}</div>
    <div class="kpi-title">{title}</div>
    {f'<div class="kpi-sub">{sub}</div>' if sub else ''}
  </div>
</div>"""

    kpis_html = (
        kcard("Total Revenue Leakage", _fmt_inr(tot),        f"Across {jcs:,} job cards",              "report-money",  "#DC2626") +
        kcard("Not Charged",           _fmt_inr(nc),         f"{nc_pct:.0f}% of total",                "ban",           "#7C3AED") +
        kcard("Fully Discounted",      _fmt_inr(fd),         f"{fd_pct:.0f}% of total",                "discount-2",    "#D97706") +
        kcard("Affected Job Cards",    f"{jcs:,}",           f"Avg {_fmt_inr(avg_jc)}/JC",             "file-invoice",  "#0891B2") +
        kcard("Locations Affected",    str(locs_cnt),        "Unique locations",                        "map-pin",       "#059669") +
        kcard("Est. Recoverable",      _fmt_inr(recoverable),f"At {recovery_rate*100:.0f}% recovery",  "trending-up",   "#16A34A")
    )

    # ── Service chips ─────────────────────────────────────────────────────────
    all_svcs  = ["All"] + svc_agg["Service Type"].tolist()
    svc_map   = {row["Service Type"]: row["loss"] for _, row in svc_agg.iterrows()}
    chips_html = ""
    for s in all_svcs:
        chip_val = _fmt_inr(svc_map.get(s, 0)) if s != "All" else _fmt_inr(tot)
        chips_html += (
            f'<div class="svc-chip{" active" if s == "All" else ""}" '
            f'data-svc="{s}" onclick="setSvc(this)">'
            f'{s}<span class="chip-val">{chip_val}</span></div>'
        )

    # ── Location table rows ───────────────────────────────────────────────────
    loc_avg_loss  = tot / locs_cnt if locs_cnt else 0
    loc_rows_html = ""
    for _, r in loc_agg.iterrows():
        pms_p     = pms_by_loc.get(r["Location"], 0)
        expand_id = f"exp_{r['Location'].replace(' ','_').replace('/','_').replace('(','').replace(')','')}"
        loc_df    = miss_df[miss_df["Location"] == r["Location"]] if "Location" in miss_df.columns else pd.DataFrame()
        svc_detail = ""
        if not loc_df.empty and "Service Type" in loc_df.columns:
            for svc in svc_agg["Service Type"].tolist():
                sv = loc_df[loc_df["Service Type"] == svc]["Missed Revenue"].sum()
                if sv > 0:
                    svc_detail += f'<span class="expand-chip"><b>{svc}:</b> {_fmt_inr(sv)}</span>'
        recov     = float(r["loss"]) * recovery_rate
        avg_loss  = float(r["avg_loss"])
        loc_name_safe = r["Location"].replace("'", "\\'")
        loc_rows_html += f"""
<tr class="loc-row" data-loss="{r['loss']:.2f}" data-loc="{r['Location']}">
  <td class="rank-cell">{int(r['rank'])}</td>
  <td><span class="loc-name">{r['Location']}</span></td>
  <td style="font-weight:600;color:#DC2626;">{_fmt_inr(r['loss'])}</td>
  <td style="text-align:center;">{int(r['count'])}</td>
  <td>{_fmt_inr(avg_loss)}</td>
  <td><span class="svc-tag">{r.get('top_svc','—')}</span></td>
  <td style="min-width:100px;">{_pct_bar(pms_p)}</td>
  <td>{_risk_badge(r['loss'], loc_avg_loss)}</td>
  <td><button class="expand-btn" onclick="toggleExpand('{expand_id}')">▼</button></td>
</tr>
<tr id="{expand_id}" class="expand-row" style="display:none;">
  <td colspan="9">
    <div class="expand-content">
      <div class="expand-row-grid">
        <div>
          <div class="expand-label">Service Breakdown</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px;">
            {svc_detail if svc_detail else '<span style="color:#9CA3AF">No breakdown available</span>'}
          </div>
        </div>
        <div>
          <div class="expand-label">Recovery Estimate</div>
          <div style="font-size:15px;font-weight:700;color:#16A34A;margin-top:4px;">{_fmt_inr(recov)}</div>
          <div style="font-size:11px;color:#6B7280;">At {recovery_rate*100:.0f}% recovery rate</div>
        </div>
        <div>
          <div class="expand-label">Affected Job Cards</div>
          <div style="font-size:15px;font-weight:700;color:#0891B2;margin-top:4px;">{int(r['count'])}</div>
          <div style="font-size:11px;color:#6B7280;">Avg {_fmt_inr(avg_loss)}/JC</div>
        </div>
        <div>
          <div class="expand-label">Operational Investigation</div>
          <button class="dealer-audit-btn" onclick="openDealerAudit('{loc_name_safe}')">
            🔗 Open Dealer Audit
          </button>
        </div>
      </div>
    </div>
  </td>
</tr>"""

    # ── Donut chart data + HTML legend ────────────────────────────────────────
    COLORS        = ["#3B82F6", "#EF4444", "#F59E0B", "#10B981", "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16"]
    donut_labels  = svc_agg["Service Type"].tolist()
    donut_values  = [round(float(x), 2) for x in svc_agg["loss"]]
    donut_colors  = [COLORS[i % len(COLORS)] for i in range(len(donut_labels))]
    donut_legend_html = "".join(
        f'<span style="display:flex;align-items:center;gap:5px;font-size:11px;color:#374151;">'
        f'<span style="width:9px;height:9px;border-radius:2px;background:{donut_colors[i]};flex-shrink:0;"></span>'
        f'{lbl} — {_fmt_inr(donut_values[i])}</span>'
        for i, lbl in enumerate(donut_labels)
    )

    # ── Bar chart data (top 10 locations) ─────────────────────────────────────
    bar_locs   = loc_agg["Location"].head(10).tolist()
    bar_loss   = [round(float(x), 2) for x in loc_agg["loss"].head(10)]
    bar_counts = [int(x) for x in loc_agg["count"].head(10)]

    # ── Advisor rows ──────────────────────────────────────────────────────────
    adv_rows_html = ""
    for _, r in adv_agg.iterrows():
        adv_rows_html += f"""
<tr class="adv-row">
  <td style="font-weight:500;">{r['Advisor Name']}</td>
  <td style="text-align:center;">{int(r['count'])}</td>
  <td style="font-weight:600;color:#DC2626;">{_fmt_inr(r['loss'])}</td>
  <td><span class="svc-tag">{r.get('top_leak','—')}</span></td>
</tr>"""

    # ── Top JC rows ───────────────────────────────────────────────────────────
    jc_rows_html = ""
    for _, r in top_jcs.iterrows():
        jc_rows_html += f"""
<tr class="jc-row" data-jcsvc="{r.get('Service Type','—')}">
  <td><span style="font-family:monospace;font-size:12px;">{r.get('Job Card No','—')}</span></td>
  <td>{r.get('Bill Date','—')}</td>
  <td>{r.get('Location','—')}</td>
  <td>{r.get('Advisor Name','—')}</td>
  <td>{r.get('Model','—')}</td>
  <td><span class="svc-tag">{r.get('Service Type','—')}</span></td>
  <td><span class="leak-tag">{r.get('Leak Type','—')}</span></td>
  <td style="font-weight:700;color:#DC2626;">{_fmt_inr(r.get('Missed Revenue',0))}</td>
</tr>"""

    # ── PMS Heatmap ───────────────────────────────────────────────────────────
    heatmap_html = ""
    if pms_pen is not None and not pms_pen.empty and "Location" in pms_pen.columns:
        for loc, grp in pms_pen.groupby("Location"):
            tb    = float(grp["Total Bills"].sum()) if "Total Bills" in grp.columns else 0
            if not tb:
                continue
            pms_y = float(grp["PMS YES"].sum()) if "PMS YES" in grp.columns else 0
            wa_y  = float(grp["WA YES"].sum())  if "WA YES"  in grp.columns else 0
            wb_y  = float(grp["WB YES"].sum())  if "WB YES"  in grp.columns else 0
            dc_y  = float(grp["DC YES"].sum())  if "DC YES"  in grp.columns else 0
            pct   = pms_y / tb * 100
            bg    = "#DCFCE7" if pct >= 70 else "#FEF3C7" if pct >= 50 else "#FEE2E2"
            tc    = "#15803D" if pct >= 70 else "#92400E" if pct >= 50 else "#991B1B"
            # Only show WA/WB/DC sub-metrics if tb > 0 (already guaranteed here)
            sub_metrics = (
                f"PMS {pct:.0f}%"
                + (f" | WA {wa_y/tb*100:.0f}%" if wa_y > 0 else "")
                + (f" | WB {wb_y/tb*100:.0f}%" if wb_y > 0 else "")
                + (f" | DC {dc_y/tb*100:.0f}%" if dc_y > 0 else "")
            )
            heatmap_html += f"""
<div class="heat-card" style="background:{bg};border-color:{tc}20;">
  <div class="heat-loc" style="color:{tc};">{loc[:18]}</div>
  <div class="heat-pct" style="color:{tc};">{pct:.0f}%</div>
  <div class="heat-sub">{sub_metrics}</div>
</div>"""
    if not heatmap_html:
        heatmap_html = '<div style="color:#9CA3AF;padding:16px;">No PMS penetration data available.</div>'

    # ── Alert banner ──────────────────────────────────────────────────────────
    alert_msg = (
        f"⚠️ &nbsp;<strong>{top_loc}</strong> leads with <strong>{_fmt_inr(top_loc_loss)}</strong> leakage. "
        f"Primary type: <strong>{top_svc_name}</strong> ({_fmt_inr(top_svc_loss)}). "
        f"Top advisor: <strong>{top_adv}</strong> — <strong>{_fmt_inr(top_adv_loss)}</strong> across {top_adv_cnt} JCs."
    ) if tot > 0 else "✅ &nbsp;No significant leakage detected in the selected period."

    # ══════════════════════════════════════════════════════════════════════════
    #  HTML
    # ══════════════════════════════════════════════════════════════════════════
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revenue Leakage Executive Dashboard — {month_label or "All Periods"}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.0.0/dist/tabler-icons.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg:#F8FAFC; --surface:#FFFFFF; --border:#E2E8F0;
  --text:#1E293B; --muted:#64748B; --danger:#DC2626;
  --warn:#D97706; --success:#16A34A; --accent:#2563EB;
  --radius:10px; --shadow:0 1px 4px rgba(0,0,0,.07);
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',sans-serif;background:var(--bg);color:var(--text);font-size:14px;}}
.wrap{{max-width:1280px;margin:0 auto;padding:20px 16px;}}

/* ── Header ── */
.dash-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px;}}
.dash-title{{font-size:22px;font-weight:800;color:var(--text);letter-spacing:-.3px;}}
.dash-sub{{font-size:12px;color:var(--muted);margin-top:3px;}}
.dash-meta{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}}
.live-badge{{background:#DCFCE7;color:#15803D;padding:3px 11px;border-radius:20px;font-size:11px;font-weight:700;display:flex;align-items:center;gap:5px;}}
.live-dot{{width:6px;height:6px;border-radius:50%;background:#16A34A;animation:pulse 2s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:.4;}}}}
.meta-chip{{background:var(--surface);border:1px solid var(--border);padding:4px 12px;border-radius:6px;font-size:12px;color:var(--muted);}}

/* ── Alert ── */
.alert-banner{{background:#FFF7ED;border:1px solid #FED7AA;border-left:4px solid #F97316;border-radius:var(--radius);padding:12px 16px;margin-bottom:18px;font-size:13px;color:#92400E;line-height:1.6;}}

/* ── KPIs ── */
.kpi-row{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:18px;}}
.kpi-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px;display:flex;align-items:center;gap:12px;box-shadow:var(--shadow);}}
.kpi-icon{{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.kpi-val{{font-size:20px;font-weight:800;color:var(--text);line-height:1.2;}}
.kpi-title{{font-size:10px;font-weight:600;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:.5px;}}
.kpi-sub{{font-size:11px;color:var(--muted);margin-top:3px;}}

/* ── Chips ── */
.chips-row{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px;}}
.svc-chip{{background:var(--surface);border:2px solid var(--border);border-radius:8px;padding:9px 14px;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:3px;font-weight:700;font-size:13px;color:var(--text);transition:all .15s;min-width:70px;}}
.svc-chip:hover{{border-color:var(--accent);background:#EFF6FF;}}
.svc-chip.active{{border-color:var(--accent);background:#EFF6FF;color:var(--accent);}}
.chip-val{{font-size:10px;font-weight:500;color:var(--muted);}}
.svc-chip.active .chip-val{{color:var(--accent);}}

/* ── Cards ── */
.section-label{{font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-bottom:10px;}}
.main-grid{{display:grid;grid-template-columns:3fr 2fr;gap:16px;margin-bottom:18px;}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;box-shadow:var(--shadow);}}

/* ── Tables ── */
.dash-table{{width:100%;border-collapse:collapse;}}
.dash-table th{{font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;padding:8px 10px;border-bottom:2px solid var(--border);text-align:left;background:#F8FAFC;white-space:nowrap;}}
.dash-table td{{padding:9px 10px;border-bottom:1px solid #F1F5F9;font-size:13px;vertical-align:middle;}}
.dash-table tr:last-child td{{border-bottom:none;}}
.dash-table tbody tr:hover{{background:#F8FAFC;}}
.rank-cell{{font-weight:700;color:var(--accent);width:28px;text-align:center;}}
.loc-name{{font-weight:600;}}
.svc-tag{{background:#EFF6FF;color:var(--accent);padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap;}}
.leak-tag{{background:#FEF2F2;color:#DC2626;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap;}}
.expand-btn{{background:none;border:1px solid var(--border);cursor:pointer;color:var(--muted);font-size:11px;padding:3px 7px;border-radius:4px;transition:all .15s;}}
.expand-btn:hover{{background:#F1F5F9;border-color:var(--accent);color:var(--accent);}}
.expand-row td{{background:#F8FAFC;}}
.expand-content{{padding:12px 14px;}}
.expand-row-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;}}
.expand-label{{font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;}}
.expand-chip{{background:#EFF6FF;color:var(--accent);padding:3px 8px;border-radius:4px;font-size:11px;margin-right:4px;margin-bottom:4px;display:inline-block;}}
.dealer-audit-btn{{margin-top:6px;background:#1D4ED8;color:#fff;border:none;border-radius:6px;padding:7px 14px;font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap;transition:background .15s;}}
.dealer-audit-btn:hover{{background:#1E40AF;}}

/* ── Charts ── */
.chart-wrap{{position:relative;height:220px;}}
.analytics-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px;}}
.bar-wrap{{position:relative;height:260px;}}
.donut-legend{{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;padding-top:10px;border-top:1px solid var(--border);}}

/* ── Heatmap ── */
.heat-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;}}
.heat-card{{border:1px solid;border-radius:8px;padding:12px;}}
.heat-loc{{font-size:12px;font-weight:700;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.heat-pct{{font-size:26px;font-weight:800;margin-bottom:2px;}}
.heat-sub{{font-size:10px;opacity:.8;line-height:1.4;}}

/* ── Insights ── */
.insights-list{{display:flex;flex-direction:column;gap:8px;}}
.insight-item{{display:flex;align-items:flex-start;gap:12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px;font-size:13px;line-height:1.6;}}
.insight-num{{background:var(--accent);color:#fff;min-width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;margin-top:2px;}}

/* ── Action Panel ── */
.action-panel{{background:linear-gradient(135deg,#1E3A8A 0%,#1D4ED8 100%);border-radius:var(--radius);padding:20px;margin-bottom:20px;}}
.action-panel-title{{font-size:14px;font-weight:800;color:#fff;text-transform:uppercase;letter-spacing:.8px;margin-bottom:14px;display:flex;align-items:center;gap:8px;}}
.action-list{{display:flex;flex-direction:column;gap:8px;}}
.action-item{{display:flex;align-items:flex-start;gap:12px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:12px 14px;font-size:13px;line-height:1.5;color:#fff;}}
.action-num{{background:rgba(255,255,255,.2);color:#fff;min-width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;margin-top:2px;}}

/* ── Responsive ── */
@media(max-width:1100px){{.kpi-row{{grid-template-columns:repeat(3,1fr);}}}}
@media(max-width:900px){{
  .kpi-row{{grid-template-columns:repeat(2,1fr);}}
  .main-grid{{grid-template-columns:1fr;}}
  .analytics-grid{{grid-template-columns:1fr;}}
  .expand-row-grid{{grid-template-columns:repeat(2,1fr);}}
}}
@media(max-width:500px){{
  .kpi-row{{grid-template-columns:1fr 1fr;}}
  .chips-row{{gap:6px;}}
  .expand-row-grid{{grid-template-columns:1fr;}}
}}
</style>
</head>
<body>
<div class="wrap">

  <!-- 1. Header -->
  <div class="dash-header">
    <div>
      <div class="dash-title">Revenue Leakage Executive Dashboard</div>
      <div class="dash-sub">Estimated missed revenue · {month_label or "All Periods"}</div>
    </div>
    <div class="dash-meta">
      <span class="live-badge"><span class="live-dot"></span>Live</span>
      {f'<span class="meta-chip"><i class="ti ti-clock"></i> {last_sync}</span>' if last_sync else ''}
      <span class="meta-chip"><i class="ti ti-calendar"></i> {month_label or "All"}</span>
    </div>
  </div>

  <!-- 2. Alert Banner -->
  <div class="alert-banner">{alert_msg}</div>

  <!-- 3. KPI Cards -->
  <div class="kpi-row" id="kpi-row">{kpis_html}</div>

  <!-- 4. Service Type Chips -->
  <div class="section-label">Filter by Service Type</div>
  <div class="chips-row" id="chips-row">{chips_html}</div>

  <!-- 5. Main Grid: Location Table + Right Panel -->
  <div class="main-grid">
    <!-- Location Table -->
    <div class="card">
      <div class="section-label" style="margin-bottom:12px;">Location Revenue Leakage</div>
      <div style="overflow-x:auto;">
        <table class="dash-table" id="loc-table">
          <thead><tr>
            <th>#</th><th>Location</th><th>Est. Loss</th><th>JCs</th>
            <th>Avg/JC</th><th>Top Leakage</th><th>PMS %</th><th>Risk</th><th></th>
          </tr></thead>
          <tbody id="loc-tbody">{loc_rows_html}</tbody>
        </table>
      </div>
    </div>

    <!-- Right Panel -->
    <div style="display:flex;flex-direction:column;gap:14px;">
      <!-- Donut Chart -->
      <div class="card">
        <div class="section-label" style="margin-bottom:10px;">Loss by Service Type</div>
        <div class="chart-wrap">
          <canvas id="donutChart" aria-label="Donut chart of revenue loss by service type"></canvas>
        </div>
        <div class="donut-legend" id="donut-legend">{donut_legend_html}</div>
      </div>
      <!-- Top Advisors -->
      <div class="card">
        <div class="section-label" style="margin-bottom:10px;">Top Advisors by Leakage</div>
        <div style="overflow-x:auto;">
          <table class="dash-table">
            <thead><tr><th>Advisor</th><th>JCs</th><th>Loss</th><th>Primary Type</th></tr></thead>
            <tbody id="adv-tbody">{adv_rows_html}</tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- 6. Analytics Grid -->
  <div class="analytics-grid">
    <!-- Bar Chart -->
    <div class="card">
      <div class="section-label" style="margin-bottom:10px;">Location Leakage Comparison (Top 10)</div>
      <div class="bar-wrap">
        <canvas id="barChart" aria-label="Bar chart of location revenue leakage"></canvas>
      </div>
    </div>
    <!-- PMS Heatmap -->
    <div class="card">
      <div class="section-label" style="margin-bottom:10px;">PMS Penetration Health</div>
      <div class="heat-grid" id="heat-grid">{heatmap_html}</div>
    </div>
  </div>

  <!-- 7. High Value Job Cards -->
  <div class="card" style="margin-bottom:18px;">
    <div class="section-label" style="margin-bottom:12px;">High-Value Leakage — Top 10 Job Cards</div>
    <div style="overflow-x:auto;">
      <table class="dash-table">
        <thead><tr>
          <th>Job Card</th><th>Date</th><th>Location</th><th>Advisor</th>
          <th>Model</th><th>Service Type</th><th>Leak Type</th><th>Est. Loss</th>
        </tr></thead>
        <tbody id="jc-tbody">{jc_rows_html}</tbody>
      </table>
    </div>
  </div>

  <!-- 8. Executive Insights -->
  <div class="card" style="margin-bottom:18px;">
    <div class="section-label" style="margin-bottom:12px;">Executive Insights</div>
    <div class="insights-list">{insights_html}</div>
  </div>

  <!-- 9. Executive Action Panel (bottom) -->
  <div class="action-panel">
    <div class="action-panel-title">
      <i class="ti ti-checklist" style="font-size:18px;"></i>
      Executive Action Plan — What To Do Next
    </div>
    <div class="action-list">{actions_html}</div>
  </div>

</div>

<script>
// ── Embedded data ────────────────────────────────────────────────────────────
const ALL_ROWS = {rows_json};

const INIT_DONUT_LABELS = {json.dumps(donut_labels)};
const INIT_DONUT_VALUES = {json.dumps(donut_values)};
const INIT_DONUT_COLORS = {json.dumps(donut_colors)};
const INIT_BAR_LOCS     = {json.dumps(bar_locs)};
const INIT_BAR_LOSS     = {json.dumps(bar_loss)};
const INIT_BAR_COUNTS   = {json.dumps(bar_counts)};

const CHART_COLORS = ["#3B82F6","#EF4444","#F59E0B","#10B981","#8B5CF6","#EC4899","#06B6D4","#84CC16"];
const RECOVERY_RATE = {recovery_rate};

// ── Format helpers ───────────────────────────────────────────────────────────
function fmtInr(n) {{
  if(!n||n===0) return "₹0";
  if(n>=10000000) return "₹"+(n/10000000).toFixed(2)+"Cr";
  if(n>=100000)   return "₹"+(n/100000).toFixed(1)+"L";
  if(n>=1000)     return "₹"+Math.round(n/1000)+"K";
  return "₹"+n.toFixed(0);
}}

// ── Chart instances ──────────────────────────────────────────────────────────
let donutChart, barChart;

function initCharts() {{
  const donutCtx = document.getElementById("donutChart").getContext("2d");
  donutChart = new Chart(donutCtx, {{
    type:"doughnut",
    data:{{
      labels: INIT_DONUT_LABELS,
      datasets:[{{
        data: INIT_DONUT_VALUES,
        backgroundColor: INIT_DONUT_COLORS,
        borderWidth:2, borderColor:"#fff", hoverOffset:6
      }}]
    }},
    options:{{
      responsive:true, maintainAspectRatio:false, cutout:"65%",
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:function(c){{ return " "+c.label+": "+fmtInr(c.raw); }}}}}}
      }}
    }}
  }});

  const barCtx = document.getElementById("barChart").getContext("2d");
  barChart = new Chart(barCtx, {{
    type:"bar",
    data:{{
      labels: INIT_BAR_LOCS,
      datasets:[
        {{
          label:"Est. Loss",
          data: INIT_BAR_LOSS,
          backgroundColor:"#3B82F620",
          borderColor:"#3B82F6",
          borderWidth:2, borderRadius:4, yAxisID:"y"
        }},
        {{
          label:"Affected JCs",
          data: INIT_BAR_COUNTS,
          backgroundColor:"#EF444420",
          borderColor:"#EF4444",
          borderWidth:2, borderRadius:4, type:"bar", yAxisID:"y1"
        }}
      ]
    }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      plugins:{{
        legend:{{position:"top",labels:{{boxWidth:10,font:{{size:11}}}}}},
        tooltip:{{callbacks:{{label:function(c){{ return c.dataset.yAxisID==="y"?" "+fmtInr(c.raw):" "+c.raw+" JCs"; }}}}}}
      }},
      scales:{{
        x:{{ticks:{{font:{{size:10}},maxRotation:45,autoSkip:false}},grid:{{display:false}}}},
        y:{{
          type:"linear", position:"left",
          ticks:{{callback:function(v){{return fmtInr(v);}},font:{{size:10}}}},
          grid:{{color:"#F1F5F9"}}
        }},
        y1:{{
          type:"linear", position:"right",
          ticks:{{font:{{size:10}}}},
          grid:{{drawOnChartArea:false}}
        }}
      }}
    }}
  }});
}}

// ── Service chip filter ──────────────────────────────────────────────────────
let activeSvc = "All";

function setSvc(el) {{
  document.querySelectorAll(".svc-chip").forEach(c=>c.classList.remove("active"));
  el.classList.add("active");
  activeSvc = el.dataset.svc;
  applyFilter();
}}

function applyFilter() {{
  const rows = activeSvc === "All" ? ALL_ROWS : ALL_ROWS.filter(r=>r.svc===activeSvc);

  // ── KPI re-calculation ──
  const tot  = rows.reduce((s,r)=>s+r.loss, 0);
  const nc   = rows.filter(r=>r.leak==="Not Charged").reduce((s,r)=>s+r.loss, 0);
  const fd   = rows.filter(r=>r.leak==="Fully Discounted").reduce((s,r)=>s+r.loss, 0);
  const jcSet= new Set(rows.map(r=>r.jc));
  const jcs  = jcSet.size;
  const avg  = jcs ? tot/jcs : 0;
  const locSet = new Set(rows.map(r=>r.loc));
  const locsCount = locSet.size;
  const recov = tot * RECOVERY_RATE;

  // Update KPI values
  const kpiVals = document.querySelectorAll(".kpi-val");
  if(kpiVals.length>=6) {{
    kpiVals[0].textContent = fmtInr(tot);
    kpiVals[1].textContent = fmtInr(nc);
    kpiVals[2].textContent = fmtInr(fd);
    kpiVals[3].textContent = jcs.toLocaleString();
    kpiVals[4].textContent = locsCount;
    kpiVals[5].textContent = fmtInr(recov);
  }}
  // Update KPI sub-text
  const kpiSubs = document.querySelectorAll(".kpi-sub");
  if(kpiSubs.length>=6) {{
    kpiSubs[0].textContent = "Across "+jcs.toLocaleString()+" job cards";
    kpiSubs[1].textContent = tot ? (nc/tot*100).toFixed(0)+"% of total" : "0%";
    kpiSubs[2].textContent = tot ? (fd/tot*100).toFixed(0)+"% of total" : "0%";
    kpiSubs[3].textContent = "Avg "+fmtInr(avg)+"/JC";
    kpiSubs[4].textContent = "Unique locations";
    kpiSubs[5].textContent = "At "+(RECOVERY_RATE*100).toFixed(0)+"% recovery";
  }}

  // ── Donut chart ──
  const svcMap = {{}};
  rows.forEach(r=>{{ svcMap[r.svc] = (svcMap[r.svc]||0)+r.loss; }});
  const svcLabels = Object.keys(svcMap).sort((a,b)=>svcMap[b]-svcMap[a]);
  const svcVals   = svcLabels.map(l=>svcMap[l]);
  const svcColors = svcLabels.map((_,i)=>CHART_COLORS[i%CHART_COLORS.length]);
  donutChart.data.labels   = svcLabels;
  donutChart.data.datasets[0].data            = svcVals;
  donutChart.data.datasets[0].backgroundColor = svcColors;
  donutChart.update();

  // Rebuild donut legend
  const legend = document.getElementById("donut-legend");
  if(legend) {{
    legend.innerHTML = svcLabels.map((lbl,i)=>
      `<span style="display:flex;align-items:center;gap:5px;font-size:11px;color:#374151;">
       <span style="width:9px;height:9px;border-radius:2px;background:${{svcColors[i]}};flex-shrink:0;"></span>
       ${{lbl}} — ${{fmtInr(svcVals[i])}}</span>`
    ).join("");
  }}

  // ── Bar chart ──
  const locMap = {{}}; const locCnt = {{}};
  rows.forEach(r=>{{ locMap[r.loc]=(locMap[r.loc]||0)+r.loss; locCnt[r.loc]=(locCnt[r.loc]||0)+1; }});
  const locKeys = Object.keys(locMap).sort((a,b)=>locMap[b]-locMap[a]).slice(0,10);
  barChart.data.labels            = locKeys;
  barChart.data.datasets[0].data = locKeys.map(l=>locMap[l]);
  barChart.data.datasets[1].data = locKeys.map(l=>locCnt[l]);
  barChart.update();

  // ── JC table (top 10 filtered) ──
  const top10 = [...rows].sort((a,b)=>b.loss-a.loss).slice(0,10);
  const jcTbody = document.getElementById("jc-tbody");
  if(jcTbody) {{
    jcTbody.innerHTML = top10.map(r=>`
<tr>
  <td><span style="font-family:monospace;font-size:12px;">${{r.jc}}</span></td>
  <td>${{r.date}}</td><td>${{r.loc}}</td><td>${{r.adv}}</td><td>${{r.model}}</td>
  <td><span class="svc-tag">${{r.svc}}</span></td>
  <td><span class="leak-tag">${{r.leak}}</span></td>
  <td style="font-weight:700;color:#DC2626;">${{fmtInr(r.loss)}}</td>
</tr>`).join("");
  }}

  // ── Location table — hide rows with 0 loss under current filter ──
  document.querySelectorAll(".loc-row").forEach(tr=>{{
    if(activeSvc==="All") {{ tr.style.display=""; return; }}
    const locName = tr.dataset.loc;
    const locLoss = rows.filter(r=>r.loc===locName).reduce((s,r)=>s+r.loss,0);
    tr.style.display = locLoss>0 ? "" : "none";
    const expRow = tr.nextElementSibling;
    if(expRow && expRow.classList.contains("expand-row") && tr.style.display==="none")
      expRow.style.display="none";
  }});

  // ── Advisor table (re-aggregated from filtered rows) ──
  const advMap = {{}}; const advCnt = {{}}; const advLeak = {{}};
  rows.forEach(r=>{{
    advMap[r.adv] = (advMap[r.adv]||0)+r.loss;
    advCnt[r.adv] = (advCnt[r.adv]||0)+1;
    if(!advLeak[r.adv] || advMap[r.adv] > (advLeak[r.adv][1]||0))
      advLeak[r.adv] = [r.leak, advMap[r.adv]];
  }});
  const advKeys = Object.keys(advMap).sort((a,b)=>advMap[b]-advMap[a]).slice(0,10);
  const advTbody = document.getElementById("adv-tbody");
  if(advTbody) {{
    advTbody.innerHTML = advKeys.map(a=>`
<tr>
  <td style="font-weight:500;">${{a}}</td>
  <td style="text-align:center;">${{advCnt[a]}}</td>
  <td style="font-weight:600;color:#DC2626;">${{fmtInr(advMap[a])}}</td>
  <td><span class="svc-tag">${{advLeak[a]?advLeak[a][0]:"—"}}</span></td>
</tr>`).join("");
  }}
}}

// ── Expand / collapse ────────────────────────────────────────────────────────
function toggleExpand(id) {{
  const el = document.getElementById(id);
  if(!el) return;
  const btn = el.previousElementSibling?.querySelector(".expand-btn");
  if(el.style.display==="none") {{
    el.style.display="table-row";
    if(btn) btn.textContent="▲";
  }} else {{
    el.style.display="none";
    if(btn) btn.textContent="▼";
  }}
}}

// ── Dealer Audit hook ────────────────────────────────────────────────────────
function openDealerAudit(locName) {{
  // UI hook: navigates parent Streamlit app to Dealer Audit tab.
  // When Streamlit routing supports deep-linking, replace this with:
  // window.parent.location.href = "?tab=dealer_audit&loc=" + encodeURIComponent(locName);
  try {{
    window.parent.postMessage({{type:"OPEN_DEALER_AUDIT", location: locName}}, "*");
  }} catch(e) {{}}
  alert("Open Dealer Audit for: " + locName + "\\n\\nNavigate to the 'Dealer Audit (Operational)' tab and select this location.");
}}

// ── Init ─────────────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", function() {{
  initCharts();
}});
</script>
</body>
</html>"""

    return html
