from views.shared import *
from views.components.kpi_engine import KPIEngine
from views.components.chart_engine import ChartEngine
from views.dashboard_common import inject_responsive_css

"""
WSMIS Discount & Revenue Leakage Dashboard
Multi-Location Mar Dealership  ·  Apple Light-Theme  ·  v2.0
Reference Architecture: Labour/Parts v1.0
"""

                             # render_export_buttons, calc_*, ADV_COL, apply_month_filter,
                             # leakage calcs, aggregations, KPIGrid/MetricCard, EmptyState

# Explicit imports ONLY for symbols NOT already provided by views.shared:
from services.export_service import ExportMeta


# ── Import the approved discount threshold loader from the loader layer ───────
from utils.loaders import load_discount_thresholds

# ── Data Preparation ─────────────────────────────────────────────────────────

def _prepare_data(df, pairs, comparison_mode, selected_months):
    """
    Split df into CP and PP DataFrames using the same pattern as labour.py.
    Returns: cp, pp, mode_str
    """
    _ = selected_months  # unused but kept for signature consistency
    active_pairs = pairs or []
    mode_str = "YoY" if comparison_mode else "MoM"

    if not active_pairs:
        return None, None, mode_str

    cp_months = [p[0] for p in active_pairs]
    pp_months = [p[1] for p in active_pairs]

    cp = df[df["Month Name"].isin(cp_months)].copy()
    pp = df[df["Month Name"].isin(pp_months)].copy()

    # Ensure numeric
    num_cols = [
        "Pre-GST Labour", "Labour Discount",
        "Pre-GST Parts",  "Parts Discount",
        "Parts Profit",   "JC_Nos.", "Month_Sort"
    ]
    for frame in [cp, pp]:
        for c in num_cols:
            if c in frame.columns:
                frame[c] = pd.to_numeric(frame[c], errors="coerce").fillna(0)

    return cp, pp, mode_str


# ── Metrics Computation ─────────────────────────────────────────────────────

def _compute_discount_metrics(cp: pd.DataFrame, pp: pd.DataFrame,
                               targets: pd.DataFrame) -> dict:
    """
    Compute all discount and leakage metrics for both CP and PP periods.
    Returns a single dict `d` used by all render functions.
    """
    # ── Top-line ─────────────────────────────────────────────────────────────
    cp_lab_rev  = get_labour_sales(cp, aggregate=True)
    pp_lab_rev  = get_labour_sales(pp, aggregate=True) if not pp.empty else 0
    cp_lab_disc = get_labour_discount(cp, aggregate=True)
    pp_lab_disc = get_labour_discount(pp, aggregate=True) if not pp.empty else 0
    cp_lab_pct  = calc_ratio(cp_lab_disc, cp_lab_rev, multiplier=100, fill_value=0)
    pp_lab_pct  = calc_ratio(pp_lab_disc, pp_lab_rev, multiplier=100, fill_value=0)

    cp_prt_rev  = get_parts_sales(cp, aggregate=True)
    pp_prt_rev  = get_parts_sales(pp, aggregate=True) if not pp.empty else 0
    cp_prt_disc = get_parts_discount(cp, aggregate=True)
    pp_prt_disc = get_parts_discount(pp, aggregate=True) if not pp.empty else 0
    cp_prt_pct  = calc_ratio(cp_prt_disc, cp_prt_rev, multiplier=100, fill_value=0)
    pp_prt_pct  = calc_ratio(pp_prt_disc, pp_prt_rev, multiplier=100, fill_value=0)

    # ── Anomaly detection (disc > revenue at row level) ───────────────────────
    cp2 = cp.copy()
    cp2["_lab_pct_row"] = np.where(
        cp2["Pre-GST Labour"] > 0,
        cp2["Labour Discount"] / cp2["Pre-GST Labour"] * 100, 0)
    anomaly_rows = cp2[cp2["_lab_pct_row"] > 100].copy()
    anomaly_count = len(anomaly_rows)

    # ── Location breakdown using frozen calculation layer ─────────────────────
    # Use compute_discount_aggregates for labour, compute_parts_leakage for parts
    # These return: group_col, Revenue, DiscRs, Disc_Pct, Recoverable
    loc_lab_cp = compute_discount_aggregates(cp, "Location Name", benchmark=15.0)
    loc_lab_pp = compute_discount_aggregates(pp, "Location Name", benchmark=15.0) if not pp.empty else pd.DataFrame()

    # Merge CP and PP results to match existing structure
    loc_lab = loc_lab_cp.rename(columns={"Revenue": "CP_Rev", "DiscRs": "CP_Disc", "Disc_Pct": "CP_Pct", "Recoverable": "CP_Recoverable"})
    if not loc_lab_pp.empty:
        loc_lab_pp = loc_lab_pp.rename(columns={"Revenue": "PP_Rev", "DiscRs": "PP_Disc", "Disc_Pct": "PP_Pct", "Recoverable": "PP_Recoverable"})
        loc_lab = loc_lab.merge(loc_lab_pp[["Location Name", "PP_Rev", "PP_Disc", "PP_Pct", "PP_Recoverable"]], on="Location Name", how="left")
    else:
        loc_lab["PP_Rev"] = 0
        loc_lab["PP_Disc"] = 0
        loc_lab["PP_Pct"] = 0
        loc_lab["PP_Recoverable"] = 0
    loc_lab = loc_lab.fillna(0)
    loc_lab["Delta_Pct"] = (loc_lab["CP_Pct"] - loc_lab["PP_Pct"]).round(2)

    # Parts leakage using frozen calculation
    loc_prt_cp = compute_parts_leakage(cp, "Location Name", benchmark=1.0)
    loc_prt_pp = compute_parts_leakage(pp, "Location Name", benchmark=1.0) if not pp.empty else pd.DataFrame()

    loc_prt = loc_prt_cp.rename(columns={"Revenue": "CP_Rev", "DiscRs": "CP_Disc", "Disc_Pct": "CP_Pct", "Recoverable": "CP_Recoverable"})
    if not loc_prt_pp.empty:
        loc_prt_pp = loc_prt_pp.rename(columns={"Revenue": "PP_Rev", "DiscRs": "PP_Disc", "Disc_Pct": "PP_Pct", "Recoverable": "PP_Recoverable"})
        loc_prt = loc_prt.merge(loc_prt_pp[["Location Name", "PP_Rev", "PP_Disc", "PP_Pct", "PP_Recoverable"]], on="Location Name", how="left")
    else:
        loc_prt["PP_Rev"] = 0
        loc_prt["PP_Disc"] = 0
        loc_prt["PP_Pct"] = 0
        loc_prt["PP_Recoverable"] = 0
    loc_prt = loc_prt.fillna(0)
    loc_prt["Delta_Pct"] = (loc_prt["CP_Pct"] - loc_prt["PP_Pct"]).round(2)

    # Merge targets and use frozen calculation's Recoverable as Leakage_Rs
    loc_lab = loc_lab.reset_index().merge(
        targets[["Location Name", "Appr_Lab_Disc"]], on="Location Name", how="left")
    loc_lab["Appr_Lab_Disc"] = loc_lab["Appr_Lab_Disc"].fillna(15.0)
    # Use the frozen calculation's Recoverable as Leakage_Rs
    loc_lab["Leakage_Rs"] = loc_lab["CP_Recoverable"]
    loc_lab["Breach"] = loc_lab["CP_Pct"] > loc_lab["Appr_Lab_Disc"]
    loc_lab["Anomaly"] = loc_lab["CP_Pct"] > 100  # location-level anomaly flag

    loc_prt = loc_prt.reset_index().merge(
        targets[["Location Name", "Appr_Parts_Disc"]], on="Location Name", how="left")
    loc_prt["Appr_Parts_Disc"] = loc_prt["Appr_Parts_Disc"].fillna(1.0)
    # Use the frozen calculation's Recoverable as Leakage_Rs
    loc_prt["Leakage_Rs"] = loc_prt["CP_Recoverable"]

    total_leakage_lab = loc_lab["Leakage_Rs"].sum()
    total_leakage_prt = loc_prt["Leakage_Rs"].sum()
    total_leakage     = total_leakage_lab + total_leakage_prt
    n_breach_loc      = int(loc_lab["Breach"].sum())

    # ── Service type breakdown (Labour only — Parts is near-zero) ─────────────
    svc_lab = cp.groupby("Service Type").agg(
        Rev=("Pre-GST Labour", "sum"),
        Disc=("Labour Discount", "sum"),
        JC=("JC_Nos.", "sum")
    )
    svc_lab["Disc_Pct"] = np.where(svc_lab["Rev"] > 0,
                                    svc_lab["Disc"] / svc_lab["Rev"] * 100, 0).round(2)
    svc_lab = svc_lab[svc_lab["Rev"] > 0].sort_values("Disc_Pct", ascending=False)

    # ── Monthly trend ─────────────────────────────────────────────────────────
    # Use Month_Sort for sort order (canonical WSMIS convention)
    monthly = cp.groupby(["Month Name", "Month_Sort"]).agg(
        Lab_Rev=("Pre-GST Labour", "sum"),
        Lab_Disc=("Labour Discount", "sum"),
        Prt_Rev=("Pre-GST Parts", "sum"),
        Prt_Disc=("Parts Discount", "sum"),
        JC=("JC_Nos.", "sum")
    ).reset_index().sort_values("Month_Sort")
    monthly["Lab_Pct"]  = np.where(monthly["Lab_Rev"] > 0,
                                    monthly["Lab_Disc"] / monthly["Lab_Rev"] * 100, 0).round(2)
    monthly["Prt_Pct"]  = np.where(monthly["Prt_Rev"] > 0,
                                    monthly["Prt_Disc"] / monthly["Prt_Rev"] * 100, 0).round(2)
    monthly["Rolling3M"] = monthly["Lab_Pct"].rolling(3, min_periods=1).mean()

    # ── Advisor breakdown using frozen calculation layer ───────────────────────
    # Use compute_discount_aggregates for advisors
    adv_cp_calc = compute_discount_aggregates(cp, "Advisior Name", benchmark=15.0)
    adv_pp_calc = compute_discount_aggregates(pp, "Advisior Name", benchmark=15.0) if not pp.empty else pd.DataFrame()

    # Add JC count and Locations count manually (not in frozen calc)
    adv_jc = cp[cp["Pre-GST Labour"] > 0].groupby("Advisior Name").agg(
        JC=("JC_Nos.", "sum"),
        Locations=("Location Name", "nunique")
    )

    # Merge with frozen calculation results
    adv_cp = adv_cp_calc.merge(adv_jc, on="Advisior Name", how="left").fillna(0)
    adv_cp = adv_cp.rename(columns={"Revenue": "Rev", "DiscRs": "Disc", "Disc_Pct": "Disc_Pct", "Recoverable": "Leakage_Rs"})
    adv_cp["Disc_Pct"] = adv_cp["Disc_Pct"].round(2)

    # Per-advisor leakage: use median approved threshold as single benchmark
    median_threshold = targets["Appr_Lab_Disc"].median() if not targets.empty else 15.0
    adv_cp["Threshold"] = median_threshold
    # Use frozen calculation's Recoverable as Leakage_Rs
    adv_cp["Leakage_Rs"] = adv_cp["Leakage_Rs"]
    adv_cp["Anomaly"] = adv_cp["Disc_Pct"] > 100

    adv_pp = pd.DataFrame()
    if not adv_pp_calc.empty:
        adv_pp = adv_pp_calc.rename(columns={"Revenue": "Rev", "DiscRs": "Disc", "Disc_Pct": "Disc_Pct", "Recoverable": "PP_Recoverable"})
        adv_pp["Disc_Pct"] = adv_pp["Disc_Pct"].round(2)

    n_adv_breach = int((adv_cp["Disc_Pct"] > median_threshold).sum())
    n_adv_anomaly = int(adv_cp["Anomaly"].sum())

    # ── Heatmap data: Location × Month ───────────────────────────────────────
    heatmap_loc = cp.groupby(["Location Name", "Month Name", "Month_Sort"]).agg(
        L=("Pre-GST Labour", "sum"), D=("Labour Discount", "sum")
    ).reset_index()
    heatmap_loc["D_Pct"] = np.where(heatmap_loc["L"] > 0,
                                     heatmap_loc["D"] / heatmap_loc["L"] * 100, 0)
    heatmap_loc = heatmap_loc.sort_values("Month_Sort")

    # Heatmap data: Advisor × Month (top 20 by revenue)
    top20_advs = adv_cp["Rev"].nlargest(20).index.tolist()
    heatmap_adv = cp[cp["Advisior Name"].isin(top20_advs)].groupby(
        ["Advisior Name", "Month Name", "Month_Sort"]).agg(
        L=("Pre-GST Labour", "sum"), D=("Labour Discount", "sum")
    ).reset_index()
    heatmap_adv["D_Pct"] = np.where(heatmap_adv["L"] > 0,
                                     heatmap_adv["D"] / heatmap_adv["L"] * 100, 0)
    heatmap_adv = heatmap_adv.sort_values("Month_Sort")

    return {
        # Top-line
        "cp_lab_rev": cp_lab_rev, "pp_lab_rev": pp_lab_rev,
        "cp_lab_disc": cp_lab_disc, "pp_lab_disc": pp_lab_disc,
        "cp_lab_pct": cp_lab_pct, "pp_lab_pct": pp_lab_pct,
        "cp_prt_rev": cp_prt_rev, "pp_prt_rev": pp_prt_rev,
        "cp_prt_disc": cp_prt_disc, "pp_prt_disc": pp_prt_disc,
        "cp_prt_pct": cp_prt_pct, "pp_prt_pct": pp_prt_pct,
        # Leakage
        "total_leakage": total_leakage,
        "total_leakage_lab": total_leakage_lab,
        "total_leakage_prt": total_leakage_prt,
        "n_breach_loc": n_breach_loc,
        # Anomalies
        "anomaly_count": anomaly_count, "anomaly_rows": anomaly_rows,
        "n_adv_anomaly": n_adv_anomaly,
        # Location tables
        "loc_lab": loc_lab, "loc_prt": loc_prt,
        # Service type
        "svc_lab": svc_lab,
        # Monthly
        "monthly": monthly,
        # Advisor
        "adv_cp": adv_cp, "adv_pp": adv_pp,
        "n_adv_breach": n_adv_breach,
        "median_threshold": median_threshold,
        # Heatmap
        "heatmap_loc": heatmap_loc, "heatmap_adv": heatmap_adv,
        # Targets
        "targets": targets,
    }


# ── SECTION 1 — CEO ALERT BANNER (conditional) ─────────────────────────────

def _render_ceo_alert_banner(d: dict):
    """
    Show only when meaningful alerts exist.
    Severity: red = anomalies present, amber = locations in breach, blue = info only.
    """
    alerts = []
    severity = "info"

    # Highest severity: anomaly rows (discount > revenue)
    if d["anomaly_count"] > 0:
        severity = "error"
        alerts.append(
            f"🚨 {d['anomaly_count']} transactions where discount exceeds revenue "
            f"— likely credit note reversals. See Anomaly Table below."
        )

    # Revenue leakage above ₹1L
    if d["total_leakage"] > 100000:
        if severity != "error":
            severity = "warning"
        alerts.append(
            f"⚠ Revenue leakage: {fmt_inr_short(d['total_leakage'])} "
            f"across {d['n_breach_loc']} location(s) above approved discount %"
        )

    # Labour discount worsening (CP > PP by more than 1pp)
    delta_pp = d["cp_lab_pct"] - d["pp_lab_pct"]
    if delta_pp > 1.0:
        if severity == "info":
            severity = "warning"
        alerts.append(
            f"📈 Labour discount rising: {d['cp_lab_pct']:.2f}% CP vs "
            f"{d['pp_lab_pct']:.2f}% PP (+{delta_pp:.2f}pp)"
        )

    if not alerts:
        return  # clean period — no banner

    colors  = {"error": "#FEE2E2", "warning": "#FEF9C3", "info": "#EFF6FF"}
    borders = {"error": "#EF4444", "warning": "#EAB308", "info": "#3B82F6"}
    msg = "  ·  ".join(alerts)
    st.markdown(
        f'<div style="background:{colors[severity]};border-left:4px solid {borders[severity]};'
        f'padding:12px 16px;border-radius:6px;margin-bottom:16px;'
        f'font-size:var(--type-sm);font-weight:600;line-height:1.6;">{msg}</div>',
        unsafe_allow_html=True
    )


# ── SECTION 2 — CEO KPI CARDS (6 cards, two rows) ────────────────────────────

def _render_ceo_kpis(d: dict, mode_str: str):
    """
    Row 1 (4 cards): Labour Disc ₹ | Labour Disc % | Total Leakage | Parts Disc %
    Row 2 (3 cards): Advisors in breach | Anomaly alerts | PMS Disc %
    All cards use the existing kpi-card CSS class from style.css.
    Delta pills show % change AND absolute ₹ where applicable.
    invert_trend=True means rising % = red (bad).
    """

    def _kpi(title, cp_val_str, pp_val_str, delta_pct, invert=False, suffix=""):
        """Render a single KPI card using existing CSS classes."""
        if invert:
            # Rising = bad = red
            pos_class = "kpi-delta-neg"
            neg_class = "kpi-delta-pos"
        else:
            pos_class = "kpi-delta-pos"
            neg_class = "kpi-delta-neg"

        if delta_pct > 0.01:
            badge = f'<div class="{pos_class}">▲ {delta_pct:.2f}{suffix} vs PP</div>'
        elif delta_pct < -0.01:
            badge = f'<div class="{neg_class}">▼ {abs(delta_pct):.2f}{suffix} vs PP</div>'
        else:
            badge = '<div class="kpi-delta-new">= vs PP</div>'

        return (
            f'<div class="kpi-card">'
            f'  <div class="kpi-label">{title}</div>'
            f'  <div class="kpi-value">{cp_val_str}</div>'
            f'  <div class="kpi-sub">PP {pp_val_str}</div>'
            f'  {badge}'
            f'</div>'
        )

    # Row 1
    c1, c2, c3, c4 = st.columns(4)

    lab_delta_pct  = calc_growth_pct(d["cp_lab_disc"], d["pp_lab_disc"], fill_value=0)
    lab_pct_delta  = d["cp_lab_pct"] - d["pp_lab_pct"]  # pp delta in percentage points

    with c1:
        st.markdown(_kpi(
            "LABOUR DISCOUNT ₹",
            fmt_inr_short(d["cp_lab_disc"]),
            fmt_inr_short(d["pp_lab_disc"]),
            lab_delta_pct, invert=True, suffix="%"
        ), unsafe_allow_html=True)

    with c2:
        st.markdown(_kpi(
            "LABOUR DISC %",
            f"{d['cp_lab_pct']:.2f}%",
            f"{d['pp_lab_pct']:.2f}%",
            lab_pct_delta, invert=True, suffix="pp"
        ), unsafe_allow_html=True)

    with c3:
        # Leakage has no PP equivalent — show absolute only
        leakage_str = fmt_inr_short(d["total_leakage"])
        st.markdown(
            f'<div class="kpi-card">'
            f'  <div class="kpi-label">REVENUE LEAKAGE</div>'
            f'  <div class="kpi-value">{leakage_str}</div>'
            f'  <div class="kpi-sub">{d["n_breach_loc"]} location(s) above approved %</div>'
            f'  <div class="kpi-delta-neg">₹ above approved thresholds</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with c4:
        prt_pp_delta = d["cp_prt_pct"] - d["pp_prt_pct"]
        st.markdown(_kpi(
            "PARTS DISC %",
            f"{d['cp_prt_pct']:.2f}%",
            f"{d['pp_prt_pct']:.2f}%",
            prt_pp_delta, invert=True, suffix="pp"
        ), unsafe_allow_html=True)

    # Row 2 — operational signals
    st.markdown(
        f'<div style="margin:var(--space-3) 0 var(--space-2) 0;'
        f'border-top:1px solid var(--color-border);"></div>',
        unsafe_allow_html=True
    )

    c5, c6, c7 = st.columns(3)

    with c5:
        breach_color = T.COLOR_DANGER if d["n_adv_breach"] > 5 else T.COLOR_WARNING
        st.markdown(
            f'<div class="kpi-card">'
            f'  <div class="kpi-label">ADVISORS IN BREACH</div>'
            f'  <div class="kpi-value" style="color:{breach_color};">{d["n_adv_breach"]}</div>'
            f'  <div class="kpi-sub">above approved Labour Disc %</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with c6:
        anom_color = T.COLOR_DANGER if d["anomaly_count"] > 0 else T.COLOR_SUCCESS
        anom_label = "⚠ Review Required" if d["anomaly_count"] > 0 else "✓ None"
        st.markdown(
            f'<div class="kpi-card">'
            f'  <div class="kpi-label">ANOMALY TRANSACTIONS</div>'
            f'  <div class="kpi-value" style="color:{anom_color};">{d["anomaly_count"]}</div>'
            f'  <div class="kpi-sub">{anom_label} (disc > revenue)</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with c7:
        pms_svc = d["svc_lab"]
        pms_pct = pms_svc.loc["PMS", "Disc_Pct"] if "PMS" in pms_svc.index else 0
        pms_rev = pms_svc.loc["PMS", "Rev"] if "PMS" in pms_svc.index else 0
        pms_color = T.COLOR_DANGER if pms_pct > 20 else T.COLOR_WARNING if pms_pct > 15 else T.COLOR_SUCCESS
        st.markdown(
            f'<div class="kpi-card">'
            f'  <div class="kpi-label">PMS DISC % (KEY DRIVER)</div>'
            f'  <div class="kpi-value" style="color:{pms_color};">{pms_pct:.1f}%</div>'
            f'  <div class="kpi-sub">PMS Rev: {fmt_inr_short(pms_rev)}</div>'
            f'</div>',
            unsafe_allow_html=True
        )


# ── SECTION 3 — CEO TREND CHART (dual axis) ────────────────────────────────

def _render_trend_chart(d: dict, mode_str: str):
    """
    Full-width dual-axis chart:
    - Bars: Monthly Labour Discount ₹ (CP only)
    - Line: Labour Discount % (right axis, with 3M rolling average)
    - Reference line: median approved threshold from targets
    """
    section_title(f"📉 Labour Discount % Trend — {mode_str}")

    monthly = d["monthly"]
    if monthly.empty:
        st.info("No monthly data available.")
        return

    months      = monthly["Month Name"].tolist()
    lab_disc_rs = monthly["Lab_Disc"].tolist()
    lab_pct     = monthly["Lab_Pct"].tolist()
    rolling3m   = monthly["Rolling3M"].tolist()
    threshold   = d["median_threshold"]

    fig = go.Figure()

    # Bar: Labour Discount ₹
    fig.add_trace(go.Bar(
        name="Labour Disc ₹", x=months, y=lab_disc_rs,
        marker_color=T.COLOR_DANGER,
        opacity=0.75,
        text=[fmt_inr_short(v) for v in lab_disc_rs],
        textposition="outside",
        textfont=dict(size=12, family=T.FONT_FAMILY, weight=700),
        yaxis="y1"
    ))

    # Line: Monthly Discount %
    point_colors = [
        T.COLOR_DANGER if p > threshold else T.COLOR_WARNING if p > threshold * 0.85
        else T.COLOR_SUCCESS for p in lab_pct
    ]
    fig.add_trace(go.Scatter(
        name="Labour Disc %", x=months, y=lab_pct,
        mode="lines+markers+text",
        line=dict(color=T.COLOR_PRIMARY, width=3),
        marker=dict(size=10, color=point_colors, line=dict(width=2, color="white")),
        text=[f"{p:.1f}%" for p in lab_pct],
        textposition="top center",
        textfont=dict(size=12, family=T.FONT_FAMILY, weight=700),
        yaxis="y2"
    ))

    # Line: 3M Rolling Avg
    fig.add_trace(go.Scatter(
        name="3M Rolling Avg", x=months, y=rolling3m,
        mode="lines",
        line=dict(color="#FF9500", width=2, dash="dash"),
        yaxis="y2"
    ))

    # Reference line: median approved threshold
    fig.add_hline(
        y=threshold, yref="y2",
        line_dash="dot", line_color=T.COLOR_DANGER, line_width=1.5,
        annotation_text=f"Approved {threshold:.1f}% (median)",
        annotation_position="bottom right",
        annotation_font=dict(size=11, color=T.COLOR_DANGER, family=T.FONT_FAMILY)
    )

    fig = ChartEngine.apply_chart(fig,
        title=f"Labour Discount Trend — {mode_str}",
        height=400, barmode="group", size="full",
        y_title="Discount ₹")
    fig.update_layout(
        yaxis2=dict(
            title="Discount %", overlaying="y", side="right",
            showgrid=False,
            tickformat=".1f",
            title_font=dict(size=13, family=T.FONT_FAMILY),
            tickfont=dict(size=12, family=T.FONT_FAMILY)
        )
    )

    st.plotly_chart(fig, use_container_width=True)


# ── SECTION 4 — LOCATION PERFORMANCE TABLE (CEO view) ───────────────────────

def _render_location_table(d: dict, mode_str: str):
    """
    Executive location table — sorted by Leakage ₹ descending.
    Columns: Rank | Location | Lab Disc% CP | Lab Disc% PP | Δpp | Approved % | Leakage ₹ | Status
    """
    section_title(f"📍 Location Discount Performance — {mode_str}")

    loc = d["loc_lab"].copy()
    loc = loc.sort_values("Leakage_Rs", ascending=False).reset_index(drop=True)
    loc.insert(0, "Rank", range(1, len(loc) + 1))

    def _status(row):
        if row["Anomaly"]:
            return "🚨 Anomaly"
        if row["Breach"]:
            return "⚠ Breach"
        if row["CP_Pct"] > row["Appr_Lab_Disc"] * 0.85:
            return "🟡 Watch"
        return "✅ OK"

    loc["Status"] = loc.apply(_status, axis=1)

    display = pd.DataFrame({
        "Rank":         loc["Rank"],
        "Location":     loc["Location Name"],
        "Lab Disc% CP": loc["CP_Pct"].round(2),
        "Lab Disc% PP": loc["PP_Pct"].round(2),
        "Δ pp":         loc["Delta_Pct"].round(2),
        "Approved %":   loc["Appr_Lab_Disc"].round(2),
        "Leakage ₹":    loc["Leakage_Rs"],
        "Status":       loc["Status"],
    })

    # Add TOTAL row (leakage total, no approved benchmark for total)
    total_row = {
        "Rank": None, "Location": "TOTAL",
        "Lab Disc% CP": d["cp_lab_pct"],
        "Lab Disc% PP": d["pp_lab_pct"],
        "Δ pp": d["cp_lab_pct"] - d["pp_lab_pct"],
        "Approved %": d["targets"]["Appr_Lab_Disc"].median(),
        "Leakage ₹": d["total_leakage_lab"],
        "Status": ""
    }
    display = pd.concat([display, pd.DataFrame([total_row])], ignore_index=True)

    def _bold_total(row):
        if row["Location"] == "TOTAL":
            return ["font-weight:700;background:#E8F0FE"] * len(row)
        i = getattr(row, "name", 0)
        return ["background:#F9F9FB" if i % 2 == 1 else ""] * len(row)

    def _pct_color(val):
        if pd.isna(val): return ""
        if val > 50: return f"color:{T.COLOR_DANGER};font-weight:800"
        if val > 15: return f"color:{T.COLOR_DANGER};font-weight:700"
        if val > 10: return "color:#D97706;font-weight:700"
        return f"color:{T.COLOR_SUCCESS};font-weight:700"

    def _delta_color(val):
        if pd.isna(val) or val == 0: return ""
        return f"color:{T.COLOR_DANGER};" if val > 0 else f"color:{T.COLOR_SUCCESS};"

    def _leakage_color(val):
        if pd.isna(val) or val == 0: return f"color:{T.COLOR_SUCCESS}"
        return f"color:{T.COLOR_DANGER};font-weight:700"

    styled = display.style.apply(_bold_total, axis=1)
    styled = styled.map(_pct_color,    subset=["Lab Disc% CP", "Lab Disc% PP"])
    styled = styled.map(_delta_color,  subset=["Δ pp"])
    styled = styled.map(_leakage_color, subset=["Leakage ₹"])
    styled = styled.format({
        "Lab Disc% CP": lambda v: f"{v:.2f}%" if pd.notna(v) else "—",
        "Lab Disc% PP": lambda v: f"{v:.2f}%" if pd.notna(v) else "—",
        "Δ pp":         lambda v: f"{v:+.2f}pp" if pd.notna(v) else "—",
        "Approved %":   lambda v: f"{v:.2f}%" if pd.notna(v) else "—",
        "Leakage ₹":    lambda v: fmt_inr_full(v) if pd.notna(v) else "—",
    }, na_rep="—")

    cc = {
        "Rank":         st.column_config.NumberColumn("Rank"),
        "Location":     st.column_config.TextColumn("Location"),
        "Lab Disc% CP": st.column_config.TextColumn("Lab Disc% CP"),
        "Lab Disc% PP": st.column_config.TextColumn("Lab Disc% PP"),
        "Δ pp":         st.column_config.TextColumn("Δ pp"),
        "Approved %":   st.column_config.TextColumn("Approved %"),
        "Leakage ₹":    st.column_config.TextColumn("Leakage ₹"),
        "Status":       st.column_config.TextColumn("Status"),
    }
    st.dataframe(styled, column_config=cc, use_container_width=True, hide_index=True)


# ── SECTION 5 — DISCOUNT HEATMAP (Location × Month and Advisor × Month) ──────

def _render_heatmap(d: dict):
    """
    Toggle between Location × Month and Advisor × Month heatmap.
    Color scale: green (low) → amber → red (high). Capped at 50% for display.
    Anomaly locations get a separate annotation.
    """
    section_title("🗺 Discount % Heatmap")

    view = st.radio(
        "Heatmap View",
        ["By Location", "By Advisor (Top 20)"],
        horizontal=True,
        key="disc_heat_view"
    )

    grp_col = "Location Name" if view == "By Location" else "Advisior Name"
    hd = d["heatmap_loc"] if view == "By Location" else d["heatmap_adv"]

    if hd.empty:
        st.info("No data for heatmap.")
        return

    hp = hd.pivot_table(
        index=grp_col, columns="Month Name",
        values="D_Pct", aggfunc="mean"
    ).fillna(0)

    # Cap display at 50% to prevent anomalies from washing out the color scale
    hp_display = hp.clip(upper=50)

    fig = px.imshow(
        hp_display.values,
        x=hp_display.columns.tolist(),
        y=hp_display.index.tolist(),
        color_continuous_scale=["#D1FAE5", "#FEF9C3", "#FEE2E2"],  # green→amber→red
        zmin=0, zmax=50,
        aspect="auto",
        text_auto=".1f"
    )
    fig.update_coloraxes(colorbar_title="Disc %")
    fig.update_traces(textfont=dict(size=11, family=T.FONT_FAMILY))

    # Annotate anomaly cells (original value > 100)
    if view == "By Location":
        anomaly_locs = d["loc_lab"][d["loc_lab"]["Anomaly"]]["Location Name"].tolist()
        for loc in anomaly_locs:
            if loc in hp.index:
                for col in hp.columns:
                    if hp.loc[loc, col] > 100:
                        fig.add_annotation(
                            x=col, y=loc,
                            text="🚨", showarrow=False,
                            font=dict(size=14)
                        )

    fig = ChartEngine.apply_chart(fig,
        title="Labour Discount % — Month Heatmap (capped at 50% for scale)",
        height=max(350, len(hp) * 28 + 100),
        size="full"
    )
    st.plotly_chart(fig, use_container_width=True)


# ── SECTION 6 — SERVICE TYPE BREAKDOWN ────────────────────────────────────────

def _render_service_breakdown(d: dict, mode_str: str):
    """
    Table: Service Type | Revenue | Discount ₹ | Disc % | JC Count
    Sorted by Disc % descending. PMS highlighted as primary driver.
    Note in section title: PMS drives 95% of total Labour discount.
    """
    _ = mode_str  # unused but kept for signature consistency
    st.markdown(
        '<div class="section-title">🔧 Labour Discount by Service Type'
        ' <span style="font-size:var(--type-xs);color:var(--color-text-secondary);'
        'font-weight:400;"> — PMS drives ~95% of total Labour discount</span></div>',
        unsafe_allow_html=True
    )

    svc = d["svc_lab"].reset_index()
    svc.columns = ["Service Type", "Revenue", "Discount ₹", "JC Count", "Disc %"]

    def _pct_color(val):
        if val > 50: return f"color:{T.COLOR_DANGER};font-weight:800"
        if val > 20: return f"color:{T.COLOR_DANGER};font-weight:700"
        if val > 10: return "color:#D97706;font-weight:700"
        return f"color:{T.COLOR_SUCCESS}"

    styled = svc.style.map(_pct_color, subset=["Disc %"])
    styled = styled.format({
        "Revenue":    fmt_inr_full,
        "Discount ₹": fmt_inr_full,
        "JC Count":   fmt_num,
        "Disc %":     lambda v: f"{v:.2f}%",
    })
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ── SECTION 7 — ADVISOR LEAKAGE TABLE (Manager drill-down) ───────────────────

def _render_advisor_table(d: dict, mode_str: str):
    """
    Full advisor-level discount table with:
    - CP Disc ₹, CP Disc %, PP Disc %, Δpp, Leakage ₹, JC Count, Locations, Anomaly flag
    Sorted by Leakage ₹ descending.
    Anomaly rows (Disc > 100%) visually flagged in red.
    """
    st.markdown(
        f'<div class="section-title">👤 Advisor Discount Leakage — {mode_str}'
        f' <span style="font-size:var(--type-xs);color:var(--color-text-secondary);">'
        f'Threshold: {d["median_threshold"]:.1f}% (median approved across locations)</span></div>',
        unsafe_allow_html=True
    )

    adv = d["adv_cp"].copy().reset_index()

    # Merge PP data
    if not d["adv_pp"].empty:
        adv = adv.merge(
            d["adv_pp"].reset_index()[["Advisior Name", "Disc_Pct"]].rename(
                columns={"Disc_Pct": "PP_Disc_Pct"}),
            on="Advisior Name", how="left"
        ).fillna({"PP_Disc_Pct": 0})
        adv["Delta_pp"] = (adv["Disc_Pct"] - adv["PP_Disc_Pct"]).round(2)
    else:
        adv["PP_Disc_Pct"] = 0.0
        adv["Delta_pp"]    = 0.0

    adv["Flag"] = adv.apply(
        lambda r: "🚨 Anomaly" if r["Anomaly"]
        else "⚠ Breach" if r["Disc_Pct"] > r["Threshold"]
        else "✅ OK", axis=1
    )

    adv = adv.sort_values("Leakage_Rs", ascending=False).reset_index(drop=True)
    adv.insert(0, "Rank", range(1, len(adv) + 1))

    display = pd.DataFrame({
        "Rank":       adv["Rank"],
        "Advisor":    adv["Advisior Name"],
        "Disc ₹ CP":  adv["Disc"],
        "Disc% CP":   adv["Disc_Pct"],
        "Disc% PP":   adv["PP_Disc_Pct"],
        "Δ pp":       adv["Delta_pp"],
        "Approved %": adv["Threshold"],
        "Leakage ₹":  adv["Leakage_Rs"],
        "JC Count":   adv["JC"],
        "Locations":  adv["Locations"],
        "Flag":       adv["Flag"],
    })

    def _row_style(row):
        if "Anomaly" in str(row.get("Flag", "")):
            return [f"background:#FEE2E2"] * len(row)
        if "Breach" in str(row.get("Flag", "")):
            return [f"background:#FEF9C3"] * len(row)
        i = getattr(row, "name", 0)
        return ["background:#F9F9FB" if i % 2 == 1 else ""] * len(row)

    def _pct_color(val):
        if val > 100: return f"color:{T.COLOR_DANGER};font-weight:800"
        if val > 20:  return f"color:{T.COLOR_DANGER};font-weight:700"
        if val > 10:  return "color:#D97706;font-weight:700"
        return f"color:{T.COLOR_SUCCESS}"

    def _leakage_color(val):
        if pd.isna(val) or val == 0: return f"color:{T.COLOR_SUCCESS}"
        return f"color:{T.COLOR_DANGER};font-weight:700"

    def _row_style(row):
        if "Anomaly" in str(row.get("Flag", "")):
            return [f"background:#FEE2E2"] * len(row)
        if "Breach" in str(row.get("Flag", "")):
            return [f"background:#FEF9C3"] * len(row)
        i = getattr(row, "name", 0)
        return ["background:#F9F9FB" if i % 2 == 1 else ""] * len(row)

    styled = display.style.apply(_row_style, axis=1)
    styled = styled.map(_pct_color, subset=["Disc% CP", "Disc% PP"])
    styled = styled.map(_leakage_color, subset=["Leakage ₹"])
    styled = styled.format({
        "Disc ₹ CP":  fmt_inr_full,
        "Disc% CP":   lambda v: f"{v:.2f}%",
        "Disc% PP":   lambda v: f"{v:.2f}%",
        "Δ pp":       lambda v: f"{v:+.2f}pp",
        "Approved %": lambda v: f"{v:.2f}%",
        "Leakage ₹":  fmt_inr_full,
        "JC Count":   fmt_num,
    }, na_rep="—")

    st.dataframe(styled, use_container_width=True, hide_index=True, height=450)

    # Export
    meta = ExportMeta(
        report_title="Discount Advisor",
        location="All Locations",
        date_range="",
    )
    render_export_buttons(display, meta, formats=["csv", "excel"], key_prefix="discount_advisor", collapsed=True)


# ── SECTION 8 — ANOMALY TABLE ───────────────────────────────────────────────

def _render_anomaly_table(d: dict):
    """
    Shown only when anomaly_count > 0.
    Table of rows where Labour Discount > Labour Revenue.
    Helps Finance team identify credit note reversals for review.
    """
    if d["anomaly_count"] == 0:
        return

    with st.expander(
        f"🚨 {d['anomaly_count']} Anomaly Transactions — Discount Exceeds Revenue",
        expanded=False
    ):
        st.markdown(
            '<div style="font-size:var(--type-sm);color:var(--color-text-secondary);'
            'margin-bottom:8px;">These rows have Labour Discount > Labour Revenue. '
            'Likely causes: credit note reversals, rounding errors, or data entry issues. '
            'Include in totals but verify with Finance.</div>',
            unsafe_allow_html=True
        )

        anom = d["anomaly_rows"][[
            "Location Name", "Month Name", "Advisior Name",
            "Service Type", "Pre-GST Labour", "Labour Discount", "_lab_pct_row"
        ]].copy().sort_values("_lab_pct_row", ascending=False)

        anom.columns = [
            "Location", "Month", "Advisor", "Service Type",
            "Labour ₹", "Discount ₹", "Disc %"
        ]

        styled = anom.style.format({
            "Labour ₹":   fmt_inr_full,
            "Discount ₹": fmt_inr_full,
            "Disc %":     lambda v: f"{v:.1f}%",
        }).map(
            lambda v: f"color:{T.COLOR_DANGER};font-weight:800",
            subset=["Disc %"]
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        meta = ExportMeta(
            report_title="Discount Anomalies",
            location="All Locations",
            date_range="",
        )
        render_export_buttons(anom, meta, formats=["csv", "excel"], key_prefix="discount_anomalies", collapsed=True)


# ── SECTION 9 — PARTS DISCOUNT TABLE (secondary, always collapsed) ──────────

def _render_parts_discount(d: dict, mode_str: str):
    """
    Parts discount is 0.40% overall — low risk.
    Show as collapsed expander. Location table only. No heatmap, no advisor drill-down.
    """
    with st.expander("📦 Parts Discount by Location (low risk — 0.40% overall)", expanded=False):
        section_title(f"Parts Discount — {mode_str}")

        loc_p = d["loc_prt"].copy().sort_values("Leakage_Rs", ascending=False)
        display = pd.DataFrame({
            "Location":      loc_p["Location Name"],
            "Parts Disc% CP": loc_p["CP_Pct"],
            "Parts Disc% PP": loc_p["PP_Pct"],
            "Δ pp":           loc_p["Delta_Pct"],
            "Approved %":     loc_p["Appr_Parts_Disc"],
            "Leakage ₹":      loc_p["Leakage_Rs"],
        })

        styled = display.style.format({
            "Parts Disc% CP": lambda v: f"{v:.2f}%",
            "Parts Disc% PP": lambda v: f"{v:.2f}%",
            "Δ pp":           lambda v: f"{v:+.2f}pp",
            "Approved %":     lambda v: f"{v:.2f}%",
            "Leakage ₹":      fmt_inr_full,
        })
        st.dataframe(styled, use_container_width=True, hide_index=True)


# ── MAIN render() FUNCTION ─────────────────────────────────────────────────

def render(df, pairs, comparison_mode=True, selected_months=None):
    """
    Main entry point — called by router exactly as existing discount.py is called.
    Signature is identical to current discount.py render().
    """
    inject_responsive_css()
    PageBreadcrumb(["Commercial", "Discounts"])

    if df.empty:
        EmptyState("No data available for the selected period.")
        return

    # ── Load approved discount thresholds from the loader layer ───────────────
    # Use the first client's sheet_id (same pattern as app.py line 721)
    client_config = list(CLIENTS.values())[0]
    sheet_id = client_config["sheet_id"]
    targets = load_discount_thresholds(sheet_id)

    # ── Prepare CP / PP split ─────────────────────────────────────────────────
    cp, pp, mode_str = _prepare_data(df, pairs, comparison_mode, selected_months)

    if cp is None:
        EmptyState("No matching prior period data for the selected comparison mode.")
        return

    if cp.empty:
        EmptyState("No data for the selected period.")
        return

    # ── Compute all metrics ───────────────────────────────────────────────────
    d = _compute_discount_metrics(cp, pp, targets)

    # ── Render: CEO section ───────────────────────────────────────────────────
    _render_ceo_kpis(d, mode_str)
    _render_ceo_alert_banner(d)

    divider()

    _render_trend_chart(d, mode_str)

    divider()

    _render_location_table(d, mode_str)

    # ── Manager drill-down section ────────────────────────────────────────────
    st.markdown(
        f'<div style="margin:var(--space-6) 0 var(--space-3) 0;'
        f'border-top:2px solid var(--color-border);"></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-title" style="font-size:var(--type-lg);">'
        '🔍 Manager Drill-Down</div>',
        unsafe_allow_html=True
    )

    _render_heatmap(d)

    divider()

    _render_service_breakdown(d, mode_str)

    divider()

    _render_advisor_table(d, mode_str)

    # ── Anomaly and Parts — secondary, collapsed ──────────────────────────────
    _render_anomaly_table(d)
    _render_parts_discount(d, mode_str)
    UniversalFooter()
