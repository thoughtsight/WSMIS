"""
Revenue Leakage Executive Dashboard V2
HTML generator – consumes already-filtered miss_df + pen tables from app.py.
Do NOT call load_data() or get_cached_audit_data() here.
"""

import json
import pandas as pd


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _fmt_inr(num):
    if pd.isna(num) or num == 0:
        return "₹0"
    num = float(num)
    if num >= 10_000_000:
        return f"₹{num/10_000_000:.2f}Cr"
    if num >= 100_000:
        return f"₹{num/100_000:.1f}L"
    if num >= 1_000:
        return f"₹{num/1_000:.0f}K"
    return f"₹{num:,.0f}"


def _pct_bar(pct, good=70, warn=50):
    clr = "#22C55E" if pct >= good else "#F59E0B" if pct >= warn else "#EF4444"
    return (
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'<div style="flex:1;height:6px;background:#E5E7EB;border-radius:3px;">'
        f'<div style="width:{min(pct,100):.0f}%;height:100%;background:{clr};border-radius:3px;"></div></div>'
        f'<span style="font-size:11px;color:#374151;white-space:nowrap;">{pct:.0f}%</span></div>'
    )


def _risk_badge(loss, avg):
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
) -> str:

    if miss_df is None or miss_df.empty:
        return "<div style='padding:40px;font-family:Inter,sans-serif;color:#6B7280;text-align:center;'>No revenue leakage data for selected filters.</div>"

    # ── Aggregations ──────────────────────────────────────────────────────────
    tot   = float(miss_df["Missed Revenue"].sum())
    nc    = float(miss_df[miss_df["Leak Type"] == "Not Charged"]["Missed Revenue"].sum())
    fd    = float(miss_df[miss_df["Leak Type"] == "Fully Discounted"]["Missed Revenue"].sum())
    jcs   = int(miss_df["Job Card No"].nunique())
    avg_jc = tot / jcs if jcs else 0
    nc_pct = nc / tot * 100 if tot else 0
    fd_pct = fd / tot * 100 if tot else 0

    # Service type
    svc_agg = (
        miss_df.groupby("Service Type", as_index=False)
        .agg(loss=("Missed Revenue","sum"), count=("Job Card No","nunique"))
        .sort_values("loss", ascending=False)
    )

    # Location
    loc_agg = (
        miss_df.groupby("Location", as_index=False)
        .agg(loss=("Missed Revenue","sum"), count=("Job Card No","nunique"))
        .sort_values("loss", ascending=False)
    )
    loc_agg["rank"] = range(1, len(loc_agg)+1)
    # top service per location
    if "Service Type" in miss_df.columns:
        top_svc = (
            miss_df.groupby(["Location","Service Type"])["Missed Revenue"].sum().reset_index()
        )
        idx = top_svc.groupby("Location")["Missed Revenue"].idxmax()
        top_svc = top_svc.loc[idx][["Location","Service Type"]].rename(columns={"Service Type":"top_svc"})
        loc_agg = loc_agg.merge(top_svc, on="Location", how="left")
    else:
        loc_agg["top_svc"] = "—"

    # PMS penetration per location
    pms_by_loc = {}
    if pms_pen is not None and not pms_pen.empty and "Location" in pms_pen.columns:
        for loc, grp in pms_pen.groupby("Location"):
            tb  = float(grp["Total Bills"].sum()) if "Total Bills" in grp.columns else 0
            yes = float(grp["PMS YES"].sum())      if "PMS YES"     in grp.columns else 0
            pms_by_loc[loc] = round(yes/tb*100, 1) if tb else 0

    # Advisor top 10
    adv_agg = (
        miss_df.groupby("Advisor Name", as_index=False)
        .agg(loss=("Missed Revenue","sum"), count=("Job Card No","nunique"))
        .sort_values("loss", ascending=False)
        .head(10)
    )
    # top leak type per advisor
    if "Leak Type" in miss_df.columns:
        adv_leak = (
            miss_df.groupby(["Advisor Name","Leak Type"])["Missed Revenue"].sum().reset_index()
        )
        idx2 = adv_leak.groupby("Advisor Name")["Missed Revenue"].idxmax()
        adv_leak = adv_leak.loc[idx2][["Advisor Name","Leak Type"]].rename(columns={"Leak Type":"top_leak"})
        adv_agg = adv_agg.merge(adv_leak, on="Advisor Name", how="left")
    else:
        adv_agg["top_leak"] = "—"

    # Top 10 job cards
    jc_cols = [c for c in ["Job Card No","Bill Date","Location","Advisor Name","Model","Service Type","Leak Type","Missed Revenue"] if c in miss_df.columns]
    top_jcs  = miss_df.nlargest(10, "Missed Revenue")[jc_cols].copy()
    if "Bill Date" in top_jcs.columns:
        top_jcs["Bill Date"] = pd.to_datetime(top_jcs["Bill Date"], errors="coerce").dt.strftime("%d-%b-%Y").fillna("—")

    # ── Embed data as JSON for client-side chip filtering ────────────────────
    rows_list = []
    for _, r in miss_df.iterrows():
        rows_list.append({
            "jc":   str(r.get("Job Card No","—")),
            "date": str(pd.to_datetime(r.get("Bill Date"), errors="coerce").strftime("%d-%b-%Y") if pd.notna(r.get("Bill Date")) else "—"),
            "loc":  str(r.get("Location","—")),
            "adv":  str(r.get("Advisor Name","—")),
            "model":str(r.get("Model","—")),
            "svc":  str(r.get("Service Type","—")),
            "leak": str(r.get("Leak Type","—")),
            "loss": round(float(r.get("Missed Revenue",0)), 2),
        })

    rows_json = json.dumps(rows_list)

    # ── Insights ─────────────────────────────────────────────────────────────
    top_loc      = loc_agg.iloc[0]["Location"] if len(loc_agg) else "—"
    top_loc_loss = float(loc_agg.iloc[0]["loss"]) if len(loc_agg) else 0
    top_svc_name = svc_agg.iloc[0]["Service Type"] if len(svc_agg) else "—"
    top_svc_loss = float(svc_agg.iloc[0]["loss"]) if len(svc_agg) else 0
    top_adv      = adv_agg.iloc[0]["Advisor Name"] if len(adv_agg) else "—"
    top_adv_loss = float(adv_agg.iloc[0]["loss"]) if len(adv_agg) else 0
    top_adv_cnt  = int(adv_agg.iloc[0]["count"]) if len(adv_agg) else 0
    locs_cnt     = int(miss_df["Location"].nunique()) if "Location" in miss_df.columns else 0

    insights = [
        f"Total estimated revenue leakage is <strong>{_fmt_inr(tot)}</strong> across <strong>{jcs:,}</strong> affected job cards.",
        f"<strong>{top_loc}</strong> contributes <strong>{_fmt_inr(top_loc_loss)}</strong> ({top_loc_loss/tot*100:.0f}% of total) — highest leakage location.",
        f"<strong>{top_svc_name}</strong> is the primary leakage category, accounting for <strong>{_fmt_inr(top_svc_loss)}</strong> ({top_svc_loss/tot*100:.0f}%).",
        f"<strong>{nc_pct:.0f}%</strong> of leakage is from services Not Charged (<strong>{_fmt_inr(nc)}</strong>); <strong>{fd_pct:.0f}%</strong> from Fully Discounted (<strong>{_fmt_inr(fd)}</strong>).",
        f"Average revenue leakage per affected job card is <strong>{_fmt_inr(avg_jc)}</strong> — focus on reducing per-JC leakage to recover faster.",
        f"<strong>{top_adv}</strong> has the highest individual contribution: <strong>{_fmt_inr(top_adv_loss)}</strong> across <strong>{top_adv_cnt}</strong> job cards.",
        f"Leakage is spread across <strong>{locs_cnt}</strong> location(s) — a multi-location pattern suggests a systemic compliance gap.",
    ]
    insights_html = "".join(
        f'<div class="insight-item"><span class="insight-num">{i+1}</span><span>{ins}</span></div>'
        for i, ins in enumerate(insights)
    )

    # ── KPI cards ─────────────────────────────────────────────────────────────
    def kcard(title, val, sub="", icon="report-money", clr="#2563EB"):
        return f"""
<div class="kpi-card">
  <div class="kpi-icon" style="background:{clr}15;color:{clr};">
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <use href="#{icon}"/>
    </svg>
    <i class="ti ti-{icon}" style="font-size:22px;"></i>
  </div>
  <div class="kpi-body">
    <div class="kpi-val">{val}</div>
    <div class="kpi-title">{title}</div>
    {f'<div class="kpi-sub">{sub}</div>' if sub else ''}
  </div>
</div>"""

    kpis_html = (
        kcard("Total Revenue Leakage", _fmt_inr(tot), f"Across {jcs:,} job cards", "report-money", "#DC2626") +
        kcard("Not Charged",           _fmt_inr(nc),  f"{nc_pct:.0f}% of total",   "ban",           "#7C3AED") +
        kcard("Discounted",            _fmt_inr(fd),  f"{fd_pct:.0f}% of total",   "discount-2",    "#D97706") +
        kcard("Affected Job Cards",    f"{jcs:,}",    f"Avg {_fmt_inr(avg_jc)}/JC","file-invoice",  "#0891B2")
    )

    # ── Service chips ─────────────────────────────────────────────────────────
    all_svcs = ["All"] + svc_agg["Service Type"].tolist()
    svc_map  = {row["Service Type"]: row["loss"] for _, row in svc_agg.iterrows()}
    chips_html = ""
    for s in all_svcs:
        val = _fmt_inr(svc_map.get(s, tot)) if s != "All" else _fmt_inr(tot)
        chips_html += f'<div class="svc-chip" data-svc="{s}" onclick="setSvc(this)">{s}<span class="chip-val">{val}</span></div>'

    # ── Location table rows ───────────────────────────────────────────────────
    loc_avg = tot / locs_cnt if locs_cnt else 0
    loc_rows_html = ""
    for _, r in loc_agg.iterrows():
        pms_p  = pms_by_loc.get(r["Location"], 0)
        expand_id = f"exp_{r['Location'].replace(' ','_').replace('/','_')}"
        # per-svc breakdown for this location
        loc_df = miss_df[miss_df["Location"] == r["Location"]] if "Location" in miss_df.columns else pd.DataFrame()
        svc_detail = ""
        if not loc_df.empty and "Service Type" in loc_df.columns:
            for svc in svc_agg["Service Type"].tolist():
                sv = loc_df[loc_df["Service Type"]==svc]["Missed Revenue"].sum()
                if sv > 0:
                    svc_detail += f'<span class="expand-chip"><b>{svc}:</b> {_fmt_inr(sv)}</span>'
        recov = float(r["loss"]) * 0.7
        loc_rows_html += f"""
<tr class="loc-row" data-loss="{r['loss']:.2f}">
  <td class="rank-cell">{int(r['rank'])}</td>
  <td><span class="loc-name">{r['Location']}</span></td>
  <td style="font-weight:600;">{_fmt_inr(r['loss'])}</td>
  <td>{int(r['count'])}</td>
  <td><span class="svc-tag">{r.get('top_svc','—')}</span></td>
  <td style="min-width:100px;">{_pct_bar(pms_p)}</td>
  <td>{_risk_badge(r['loss'], loc_avg)}</td>
  <td><button class="expand-btn" onclick="toggleExpand('{expand_id}')">▼</button></td>
</tr>
<tr id="{expand_id}" class="expand-row" style="display:none;">
  <td colspan="8">
    <div class="expand-content">
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">{svc_detail if svc_detail else '<span style="color:#9CA3AF">No service breakdown available</span>'}</div>
      <div style="color:#374151;font-size:12px;">Est. Recoverable Revenue: <strong>{_fmt_inr(recov)}</strong> (70% recovery assumption)</div>
    </div>
  </td>
</tr>"""

    # ── Donut data ─────────────────────────────────────────────────────────────
    donut_labels = svc_agg["Service Type"].tolist()
    donut_values = [round(float(x),2) for x in svc_agg["loss"]]
    COLORS = ["#3B82F6","#EF4444","#F59E0B","#10B981","#8B5CF6","#EC4899","#06B6D4","#84CC16"]
    donut_colors = [COLORS[i % len(COLORS)] for i in range(len(donut_labels))]

    # ── Advisor rows ────────────────────────────────────────────────────────────
    adv_rows_html = ""
    for _, r in adv_agg.iterrows():
        adv_rows_html += f"""
<tr class="adv-row" data-advsvc="{r.get('top_leak','—')}">
  <td style="font-weight:500;">{r['Advisor Name']}</td>
  <td style="text-align:center;">{int(r['count'])}</td>
  <td style="font-weight:600;color:#DC2626;">{_fmt_inr(r['loss'])}</td>
  <td><span class="svc-tag">{r.get('top_leak','—')}</span></td>
</tr>"""

    # ── Top JC rows ─────────────────────────────────────────────────────────────
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

    # ── PMS Heatmap ─────────────────────────────────────────────────────────────
    heatmap_html = ""
    if pms_pen is not None and not pms_pen.empty and "Location" in pms_pen.columns:
        for loc, grp in pms_pen.groupby("Location"):
            tb  = float(grp["Total Bills"].sum()) if "Total Bills" in grp.columns else 0
            pms_y = float(grp["PMS YES"].sum()) if "PMS YES" in grp.columns else 0
            wa_y  = float(grp["WA YES"].sum())  if "WA YES"  in grp.columns else 0
            wb_y  = float(grp["WB YES"].sum())  if "WB YES"  in grp.columns else 0
            dc_y  = float(grp["DC YES"].sum())  if "DC YES"  in grp.columns else 0
            pct = (pms_y/tb*100) if tb else 0
            bg  = "#DCFCE7" if pct >= 70 else "#FEF3C7" if pct >= 50 else "#FEE2E2"
            tc  = "#15803D" if pct >= 70 else "#92400E" if pct >= 50 else "#991B1B"
            heatmap_html += f"""
<div class="heat-card" style="background:{bg};border-color:{tc}20;">
  <div class="heat-loc" style="color:{tc};">{loc[:18]}</div>
  <div class="heat-pct" style="color:{tc};">{pct:.0f}%</div>
  <div class="heat-sub">PMS | WA {wa_y/tb*100:.0f}% | WB {wb_y/tb*100:.0f}% | DC {dc_y/tb*100:.0f}%</div>
</div>""" if tb else ""
    if not heatmap_html:
        heatmap_html = '<div style="color:#9CA3AF;padding:16px;">No PMS penetration data available.</div>'

    # ── Bar chart data (by location, top 10) ────────────────────────────────────
    bar_locs   = loc_agg["Location"].head(10).tolist()
    bar_loss   = [round(float(x),2) for x in loc_agg["loss"].head(10)]
    bar_counts = [int(x) for x in loc_agg["count"].head(10)]

    # ── Alert banner ────────────────────────────────────────────────────────────
    alert_msg = (
        f"⚠️  <strong>{top_loc}</strong> leads with <strong>{_fmt_inr(top_loc_loss)}</strong> leakage. "
        f"Primary type: <strong>{top_svc_name}</strong>. "
        f"Immediate action recommended on <strong>{top_adv}</strong> ({_fmt_inr(top_adv_loss)})."
    ) if tot > 0 else "✅  No significant leakage detected in the selected period."

    # ══════════════════════════════════════════════════════════════════════════
    #  HTML
    # ══════════════════════════════════════════════════════════════════════════
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revenue Leakage V2</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.0.0/dist/tabler-icons.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg:#F8FAFC; --surface:#FFFFFF; --border:#E2E8F0;
  --text:#1E293B; --muted:#64748B; --danger:#DC2626;
  --warn:#D97706; --success:#16A34A; --accent:#2563EB;
  --radius:10px; --shadow:0 1px 3px rgba(0,0,0,.08);
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',sans-serif;background:var(--bg);color:var(--text);font-size:14px;}}
.wrap{{max-width:1280px;margin:0 auto;padding:20px 16px;}}
/* Header */
.dash-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:8px;}}
.dash-title{{font-size:20px;font-weight:700;color:var(--text);}}
.dash-meta{{display:flex;align-items:center;gap:12px;}}
.live-badge{{background:#DCFCE7;color:#15803D;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;}}
.meta-chip{{background:var(--surface);border:1px solid var(--border);padding:4px 12px;border-radius:6px;font-size:12px;color:var(--muted);}}
/* Alert */
.alert-banner{{background:#FFF7ED;border:1px solid #FED7AA;border-left:4px solid #F97316;border-radius:var(--radius);padding:12px 16px;margin-bottom:20px;font-size:13px;color:#92400E;line-height:1.5;}}
/* KPIs */
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px;}}
.kpi-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;display:flex;align-items:center;gap:14px;box-shadow:var(--shadow);}}
.kpi-icon{{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;}}
.kpi-val{{font-size:22px;font-weight:700;color:var(--text);line-height:1.2;}}
.kpi-title{{font-size:11px;font-weight:500;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:.5px;}}
.kpi-sub{{font-size:11px;color:var(--muted);margin-top:3px;}}
/* Chips */
.chips-row{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;}}
.svc-chip{{background:var(--surface);border:2px solid var(--border);border-radius:8px;padding:10px 14px;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:3px;font-weight:600;font-size:13px;color:var(--text);transition:all .15s;min-width:72px;}}
.svc-chip:hover{{border-color:var(--accent);background:#EFF6FF;}}
.svc-chip.active{{border-color:var(--accent);background:#EFF6FF;color:var(--accent);}}
.chip-val{{font-size:11px;font-weight:500;color:var(--muted);}}
.svc-chip.active .chip-val{{color:var(--accent);}}
/* Section label */
.section-label{{font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:10px;}}
/* Main grid */
.main-grid{{display:grid;grid-template-columns:3fr 2fr;gap:16px;margin-bottom:20px;}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;box-shadow:var(--shadow);}}
/* Tables */
.dash-table{{width:100%;border-collapse:collapse;}}
.dash-table th{{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;padding:8px 10px;border-bottom:2px solid var(--border);text-align:left;background:#F8FAFC;}}
.dash-table td{{padding:9px 10px;border-bottom:1px solid #F1F5F9;font-size:13px;vertical-align:middle;}}
.dash-table tr:last-child td{{border-bottom:none;}}
.dash-table tbody tr:hover{{background:#F8FAFC;}}
.loc-row td{{cursor:default;}}
.rank-cell{{font-weight:700;color:var(--accent);width:32px;}}
.loc-name{{font-weight:600;}}
.svc-tag{{background:#EFF6FF;color:var(--accent);padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600;}}
.leak-tag{{background:#FEF2F2;color:#DC2626;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600;}}
.expand-btn{{background:none;border:none;cursor:pointer;color:var(--muted);font-size:12px;padding:2px 6px;border-radius:4px;}}
.expand-btn:hover{{background:#F1F5F9;}}
.expand-row td{{background:#F8FAFC;}}
.expand-content{{padding:8px 12px;font-size:12px;}}
.expand-chip{{background:#EFF6FF;color:var(--accent);padding:2px 8px;border-radius:4px;font-size:11px;margin-right:4px;}}
/* Charts */
.chart-wrap{{position:relative;height:220px;}}
/* Analytics */
.analytics-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;}}
.bar-wrap{{position:relative;height:260px;}}
/* Heatmap */
.heat-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;}}
.heat-card{{border:1px solid;border-radius:8px;padding:12px;}}
.heat-loc{{font-size:12px;font-weight:600;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.heat-pct{{font-size:24px;font-weight:700;margin-bottom:2px;}}
.heat-sub{{font-size:10px;opacity:.75;}}
/* Insights */
.insights-list{{display:flex;flex-direction:column;gap:8px;}}
.insight-item{{display:flex;align-items:flex-start;gap:12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px;font-size:13px;line-height:1.5;}}
.insight-num{{background:var(--accent);color:#fff;min-width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;margin-top:1px;}}
/* Responsive */
@media(max-width:900px){{
  .kpi-row{{grid-template-columns:repeat(2,1fr);}}
  .main-grid{{grid-template-columns:1fr;}}
  .analytics-grid{{grid-template-columns:1fr;}}
}}
</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div class="dash-header">
    <div>
      <div class="dash-title">Revenue Leakage Executive Dashboard</div>
      <div style="font-size:12px;color:var(--muted);margin-top:2px;">Estimated missed revenue · {month_label or "All Periods"}</div>
    </div>
    <div class="dash-meta">
      <span class="live-badge"><i class="ti ti-circle-check"></i> Live</span>
      {f'<span class="meta-chip"><i class="ti ti-clock"></i> {last_sync}</span>' if last_sync else ''}
      <span class="meta-chip"><i class="ti ti-calendar"></i> {month_label or "All"}</span>
    </div>
  </div>

  <!-- Alert Banner -->
  <div class="alert-banner">{alert_msg}</div>

  <!-- KPI Cards -->
  <div class="kpi-row" id="kpi-row">
    {kpis_html}
  </div>

  <!-- Service Chips -->
  <div class="section-label">Filter by Service Type</div>
  <div class="chips-row" id="chips-row">
    {chips_html}
  </div>

  <!-- Main Grid -->
  <div class="main-grid">
    <!-- Location Table -->
    <div class="card">
      <div class="section-label" style="margin-bottom:12px;">Location Revenue Leakage</div>
      <div style="overflow-x:auto;">
        <table class="dash-table" id="loc-table">
          <thead><tr>
            <th>#</th><th>Location</th><th>Est. Loss</th><th>JCs</th>
            <th>Top Leakage</th><th>PMS %</th><th>Risk</th><th></th>
          </tr></thead>
          <tbody id="loc-tbody">{loc_rows_html}</tbody>
        </table>
      </div>
    </div>

    <!-- Right panel -->
    <div style="display:flex;flex-direction:column;gap:14px;">
      <!-- Donut -->
      <div class="card">
        <div class="section-label" style="margin-bottom:10px;">Loss by Service Type</div>
        <div class="chart-wrap"><canvas id="donutChart"></canvas></div>
      </div>
      <!-- Advisor table -->
      <div class="card">
        <div class="section-label" style="margin-bottom:10px;">Top Revenue Leakage Advisors</div>
        <div style="overflow-x:auto;">
          <table class="dash-table">
            <thead><tr><th>Advisor</th><th>JCs</th><th>Loss</th><th>Primary Type</th></tr></thead>
            <tbody id="adv-tbody">{adv_rows_html}</tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- Analytics Grid -->
  <div class="analytics-grid">
    <!-- Bar Chart -->
    <div class="card">
      <div class="section-label" style="margin-bottom:10px;">Location Leakage Comparison</div>
      <div class="bar-wrap"><canvas id="barChart"></canvas></div>
    </div>
    <!-- PMS Heatmap -->
    <div class="card">
      <div class="section-label" style="margin-bottom:10px;">PMS Penetration Health</div>
      <div class="heat-grid" id="heat-grid">{heatmap_html}</div>
    </div>
  </div>

  <!-- Top JCs -->
  <div class="card" style="margin-bottom:20px;">
    <div class="section-label" style="margin-bottom:12px;">Recent High-Value Leakage — Top 10 Job Cards</div>
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

  <!-- Executive Insights -->
  <div class="card" style="margin-bottom:20px;">
    <div class="section-label" style="margin-bottom:12px;">Executive Insights</div>
    <div class="insights-list">{insights_html}</div>
  </div>

</div>

<script>
// ── Embedded data ───────────────────────────────────────────────────────────
const ALL_ROWS = {rows_json};

const INIT_DONUT_LABELS = {json.dumps(donut_labels)};
const INIT_DONUT_VALUES = {json.dumps(donut_values)};
const INIT_DONUT_COLORS = {json.dumps(donut_colors)};
const INIT_BAR_LOCS     = {json.dumps(bar_locs)};
const INIT_BAR_LOSS     = {json.dumps(bar_loss)};
const INIT_BAR_COUNTS   = {json.dumps(bar_counts)};

const CHART_COLORS = ["#3B82F6","#EF4444","#F59E0B","#10B981","#8B5CF6","#EC4899","#06B6D4","#84CC16"];

// ── Format helpers ──────────────────────────────────────────────────────────
function fmtInr(n) {{
  if(!n||n===0) return "₹0";
  if(n>=10000000) return "₹"+(n/10000000).toFixed(2)+"Cr";
  if(n>=100000)   return "₹"+(n/100000).toFixed(1)+"L";
  if(n>=1000)     return "₹"+Math.round(n/1000)+"K";
  return "₹"+n.toFixed(0);
}}

// ── Chart instances ─────────────────────────────────────────────────────────
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
        borderWidth:2, borderColor:"#fff",
        hoverOffset:4
      }}]
    }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      cutout:"65%",
      plugins:{{
        legend:{{position:"right",labels:{{boxWidth:10,padding:8,font:{{size:11}}}}}},
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
          borderWidth:2,
          borderRadius:4,
          yAxisID:"y"
        }},
        {{
          label:"Affected JCs",
          data: INIT_BAR_COUNTS,
          backgroundColor:"#EF444420",
          borderColor:"#EF4444",
          borderWidth:2,
          borderRadius:4,
          type:"bar",
          yAxisID:"y1"
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
        x:{{ticks:{{font:{{size:10}},maxRotation:45}},grid:{{display:false}}}},
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

// ── Service chip filter ─────────────────────────────────────────────────────
let activeSvc = "All";

function setSvc(el) {{
  document.querySelectorAll(".svc-chip").forEach(c=>c.classList.remove("active"));
  el.classList.add("active");
  activeSvc = el.dataset.svc;
  applyFilter();
}}

function applyFilter() {{
  const rows = activeSvc === "All" ? ALL_ROWS : ALL_ROWS.filter(r=>r.svc===activeSvc);

  // KPIs
  const tot  = rows.reduce((s,r)=>s+r.loss, 0);
  const nc   = rows.filter(r=>r.leak==="Not Charged").reduce((s,r)=>s+r.loss, 0);
  const fd   = rows.filter(r=>r.leak==="Fully Discounted").reduce((s,r)=>s+r.loss, 0);
  const jcSet= new Set(rows.map(r=>r.jc));
  const jcs  = jcSet.size;
  const avg  = jcs?tot/jcs:0;

  // Update KPI cards
  const kpiVals = document.querySelectorAll(".kpi-val");
  if(kpiVals.length>=4) {{
    kpiVals[0].textContent = fmtInr(tot);
    kpiVals[1].textContent = fmtInr(nc);
    kpiVals[2].textContent = fmtInr(fd);
    kpiVals[3].textContent = jcs.toLocaleString();
  }}
  const kpiSubs = document.querySelectorAll(".kpi-sub");
  if(kpiSubs.length>=4) {{
    kpiSubs[0].textContent = "Across "+jcs.toLocaleString()+" job cards";
    kpiSubs[1].textContent = tot? (nc/tot*100).toFixed(0)+"% of total" : "0%";
    kpiSubs[2].textContent = tot? (fd/tot*100).toFixed(0)+"% of total" : "0%";
    kpiSubs[3].textContent = "Avg "+fmtInr(avg)+"/JC";
  }}

  // Donut chart
  const svcMap = {{}};
  rows.forEach(r=>{{ svcMap[r.svc] = (svcMap[r.svc]||0)+r.loss; }});
  const svcLabels = Object.keys(svcMap).sort((a,b)=>svcMap[b]-svcMap[a]);
  const svcVals   = svcLabels.map(l=>svcMap[l]);
  const svcColors = svcLabels.map((_,i)=>CHART_COLORS[i%CHART_COLORS.length]);
  donutChart.data.labels   = svcLabels;
  donutChart.data.datasets[0].data            = svcVals;
  donutChart.data.datasets[0].backgroundColor = svcColors;
  donutChart.update();

  // Bar chart
  const locMap = {{}}; const locCnt = {{}};
  rows.forEach(r=>{{ locMap[r.loc]=(locMap[r.loc]||0)+r.loss; locCnt[r.loc]=(locCnt[r.loc]||0)+1; }});
  const locKeys = Object.keys(locMap).sort((a,b)=>locMap[b]-locMap[a]).slice(0,10);
  barChart.data.labels              = locKeys;
  barChart.data.datasets[0].data   = locKeys.map(l=>locMap[l]);
  barChart.data.datasets[1].data   = locKeys.map(l=>locCnt[l]);
  barChart.update();

  // JC table — show top 10 filtered
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

  // Loc table — filter visible rows (show loc rows whose top svc matches)
  document.querySelectorAll(".loc-row").forEach(tr=>{{
    if(activeSvc==="All") {{ tr.style.display=""; return; }}
    const loss = parseFloat(tr.dataset.loss)||0;
    const locLoss = rows.filter(r=>r.loc===tr.querySelector(".loc-name")?.textContent).reduce((s,r)=>s+r.loss,0);
    tr.style.display = locLoss>0?"":"none";
    const expand = tr.nextElementSibling;
    if(expand&&expand.classList.contains("expand-row")&&tr.style.display==="none") expand.style.display="none";
  }});

  // Advisor table
  const advMap = {{}}; const advCnt = {{}}; const advLeak = {{}};
  rows.forEach(r=>{{
    advMap[r.adv]=(advMap[r.adv]||0)+r.loss;
    advCnt[r.adv]=(advCnt[r.adv]||0)+1;
    if(!advLeak[r.adv]||advLeak[r.adv][1]<advMap[r.adv]) advLeak[r.adv]=[r.leak,advMap[r.adv]];
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

// ── Expand / collapse ───────────────────────────────────────────────────────
function toggleExpand(id) {{
  const el = document.getElementById(id);
  if(!el) return;
  el.style.display = el.style.display==="none"?"table-row":"none";
}}

// ── Init ────────────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", function() {{
  initCharts();
  // mark first chip active
  const first = document.querySelector(".svc-chip");
  if(first) first.classList.add("active");
}});
</script>
</body>
</html>"""

    return html
