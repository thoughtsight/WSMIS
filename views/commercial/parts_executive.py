from views.shared import *
from views.components.chart_engine import ChartEngine
from ui.components.metrics import KPIGrid

"""
Parts Revenue — Executive Comparative Dashboard
Multi-Location Mar Dealership  ·  Apple Light-Theme  ·  v2.0
"""
from services.state_manager import StateManager
from views.dashboard_common import (
    inject_responsive_css, apply_period_filters, render_cross_filter_bar,
    render_svc_panel,
    style_table_bold_total, style_color_growth, style_margin_color,
    compute_rank_movement, format_rank_movement, navigate_to_page,
)


def _init_state():
    """Initialize Parts dashboard state using StateManager."""
    StateManager.initialize_namespace("parts_")




def _apply_filters(df, active_pairs):
    return apply_period_filters(df, active_pairs, "parts_cross_month")


def _compute_metrics(cp, pp, df):
    # Top-line revenue - use canonical helper
    cp_val = get_parts_sales(cp, aggregate=True)
    pp_val = get_parts_sales(pp, aggregate=True)
    growth_pct = calc_growth_pct(cp_val, pp_val, fill_value=0)
    
    # Job Cards
    cp_jc = get_jobcard_count(cp) if "JC_Nos." in cp.columns else 0
    pp_jc = get_jobcard_count(pp) if "JC_Nos." in pp.columns else 0

    # Oil Penetration Rate: JCs with Oil_Sale > 0 / Total JCs
    cp_oil_pen = 0
    pp_oil_pen = 0
    if "Oil_Sale" in cp.columns and cp_jc > 0:
        cp_oil_jcs = cp[cp["Oil_Sale"] > 0].shape[0] if not cp.empty else 0
        cp_oil_pen = calc_ratio(cp_oil_jcs, cp_jc, multiplier=100, fill_value=0)
    if "Oil_Sale" in pp.columns and pp_jc > 0:
        pp_oil_jcs = pp[pp["Oil_Sale"] > 0].shape[0] if not pp.empty else 0
        pp_oil_pen = calc_ratio(pp_oil_jcs, pp_jc, multiplier=100, fill_value=0)
    oil_pen_growth = calc_growth_pct(cp_oil_pen, pp_oil_pen, fill_value=0)

    # Parts per Job Card: total parts line items / total JCs
    # Using Pre-GST Parts as parts count
    cp_parts_per_jc = calc_ratio(cp_val, cp_jc, fill_value=0) if cp_jc > 0 else 0
    pp_parts_per_jc = calc_ratio(pp_val, pp_jc, fill_value=0) if pp_jc > 0 else 0
    parts_per_jc_growth = calc_growth_pct(cp_parts_per_jc, pp_parts_per_jc, fill_value=0)

    # Margin - use canonical helpers (must be calculated before Health Score)
    cp_profit = get_parts_profit(cp, aggregate=True)
    pp_profit = get_parts_profit(pp, aggregate=True)
    cp_margin_pct = calc_ratio(cp_profit, cp_val, multiplier=100, fill_value=0)
    pp_margin_pct = calc_ratio(pp_profit, pp_val, multiplier=100, fill_value=0)
    margin_delta_pp = cp_margin_pct - pp_margin_pct

    # Discount Rate: Parts Discount / Parts Revenue
    cp_discount = cp["Parts Discount"].sum() if "Parts Discount" in cp.columns else 0
    pp_discount = pp["Parts Discount"].sum() if "Parts Discount" in pp.columns else 0
    cp_discount_rate = calc_ratio(cp_discount, cp_val, multiplier=100, fill_value=0)
    pp_discount_rate = calc_ratio(pp_discount, pp_val, multiplier=100, fill_value=0)
    discount_rate_growth = calc_growth_pct(cp_discount_rate, pp_discount_rate, fill_value=0)

    # Parts Health Score: Composite indicator (0-100)
    # Weights: Margin 30%, Oil Penetration 25%, Parts/JC 25%, Growth 20%
    margin_score = min(100, max(0, (cp_margin_pct / 15) * 100))  # 15% margin = 100 score
    oil_pen_score = min(100, max(0, (cp_oil_pen / 80) * 100))  # 80% penetration = 100 score
    parts_jc_score = min(100, max(0, (cp_parts_per_jc / 4) * 100))  # 4 parts/JC = 100 score
    growth_score = min(100, max(0, ((growth_pct + 10) / 30) * 100))  # 20% growth = 100 score, -10% = 0

    cp_health_score = (margin_score * 0.30 + oil_pen_score * 0.25 +
                      parts_jc_score * 0.25 + growth_score * 0.20)

    # PP health score for comparison
    pp_margin_score = min(100, max(0, (pp_margin_pct / 15) * 100))
    pp_oil_pen_score = min(100, max(0, (pp_oil_pen / 80) * 100))
    pp_parts_jc_score = min(100, max(0, (pp_parts_per_jc / 4) * 100))
    pp_growth = calc_growth_pct(pp_val, pp_val if pp_val > 0 else 1, fill_value=0)  # PP vs PP-1 not available, use 0
    pp_growth_score = min(100, max(0, ((pp_growth + 10) / 30) * 100))

    pp_health_score = (pp_margin_score * 0.30 + pp_oil_pen_score * 0.25 +
                      pp_parts_jc_score * 0.25 + pp_growth_score * 0.20)

    health_score_growth = calc_growth_pct(cp_health_score, pp_health_score, fill_value=0)

    # Avg Parts / JC (revenue per card - existing metric)
    cp_rpc = calc_ratio(cp_val, cp_jc, fill_value=0) if cp_jc > 0 else 0
    pp_rpc = calc_ratio(pp_val, pp_jc, fill_value=0) if pp_jc > 0 else 0
    rpc_growth = calc_growth_pct(cp_rpc, pp_rpc, fill_value=0)
    
    # Location breakdown - use cached location_summary
    cp_loc_gb = location_summary(cp, as_index=True)
    pp_loc_gb = location_summary(pp, as_index=True)
    cp_loc_sum = cp_loc_gb.agg({"Pre-GST Parts": "sum", "JC_Nos.": "sum", "Parts Profit": "sum"})
    pp_loc_sum = pp_loc_gb.agg({"Pre-GST Parts": "sum", "JC_Nos.": "sum", "Parts Profit": "sum"})
    cp_loc = cp_loc_sum["Pre-GST Parts"] if "Pre-GST Parts" in cp_loc_sum.columns else pd.Series(dtype=float)
    pp_loc = pp_loc_sum["Pre-GST Parts"] if "Pre-GST Parts" in pp_loc_sum.columns else pd.Series(dtype=float)
    cp_loc_jc = cp_loc_sum["JC_Nos."] if "JC_Nos." in cp_loc_sum.columns else pd.Series(dtype=float)
    pp_loc_jc = pp_loc_sum["JC_Nos."] if "JC_Nos." in pp_loc_sum.columns else pd.Series(dtype=float)
    
    # Location margin - use cached location_summary and canonical helpers
    cp_loc_profit = cp_loc_sum["Parts Profit"] if "Parts Profit" in cp_loc_sum.columns else pd.Series(dtype=float)
    pp_loc_profit = pp_loc_sum["Parts Profit"] if "Parts Profit" in pp_loc_sum.columns else pd.Series(dtype=float)

    # Location-level Oil Penetration: JCs with Oil_Sale > 0 / Total JCs per location
    cp_loc_oil_pen = pd.Series(0.0, index=cp_loc_sum.index)
    pp_loc_oil_pen = pd.Series(0.0, index=pp_loc_sum.index)
    if "Oil_Sale" in cp.columns:
        cp_oil_jcs = cp[cp["Oil_Sale"] > 0].groupby("Location Name").size()
        cp_loc_oil_pen = calc_ratio(cp_oil_jcs, cp_loc_jc, multiplier=100, fill_value=0).reindex(cp_loc_sum.index, fill_value=0)
    if "Oil_Sale" in pp.columns:
        pp_oil_jcs = pp[pp["Oil_Sale"] > 0].groupby("Location Name").size()
        pp_loc_oil_pen = calc_ratio(pp_oil_jcs, pp_loc_jc, multiplier=100, fill_value=0).reindex(pp_loc_sum.index, fill_value=0)

    # Location-level Parts/JC
    cp_loc_parts_per_jc = calc_ratio(cp_loc, cp_loc_jc, fill_value=0)
    pp_loc_parts_per_jc = calc_ratio(pp_loc, pp_loc_jc, fill_value=0)

    loc_df = pd.DataFrame({"CP": cp_loc, "PP": pp_loc}).fillna(0)
    loc_df["Growth"] = calc_growth_pct(loc_df["CP"], loc_df["PP"], fill_value=np.nan)
    loc_df["Delta"] = loc_df["CP"] - loc_df["PP"]
    loc_df["Margin_CP"] = calc_ratio(cp_loc_profit, cp_loc, multiplier=100, fill_value=0).round(1)
    loc_df["Margin_PP"] = calc_ratio(pp_loc_profit, pp_loc, multiplier=100, fill_value=0).round(1)
    loc_df["Oil_Pen_CP"] = cp_loc_oil_pen.round(1)
    loc_df["Oil_Pen_PP"] = pp_loc_oil_pen.round(1)
    loc_df["Parts_Per_JC_CP"] = cp_loc_parts_per_jc.round(1)
    loc_df["Parts_Per_JC_PP"] = pp_loc_parts_per_jc.round(1)
    
    valid_locs = loc_df[loc_df["PP"] > 10000]
    best_loc = valid_locs["Growth"].idxmax() if not valid_locs.empty else "—"
    best_growth = valid_locs["Growth"].max() if not valid_locs.empty else 0
    worst_loc = valid_locs["Growth"].idxmin() if not valid_locs.empty else "—"
    worst_growth = valid_locs["Growth"].min() if not valid_locs.empty else 0
    n_growing = int((valid_locs["Growth"] > 0).sum())
    n_total = len(valid_locs)
    
    declining_locs = []
    if not valid_locs.empty:
        dec_df = valid_locs[valid_locs["Delta"] < 0].sort_values("Delta")
        for loc in dec_df.index:
            declining_locs.append({
                "location": loc,
                "gap_inr": fmt_inr(abs(dec_df.loc[loc, "Delta"]))
            })
    
    # Low margin alert — flag locations below 11%
    low_margin_locs = loc_df[loc_df["Margin_CP"] < 11.0].index.tolist()
    
    # Monthly trend - use cached monthly_summary and pivot_summary
    cp_month_gb = monthly_summary(cp, as_index=True)
    pp_month_gb = monthly_summary(pp, as_index=True)
    cp_month_sum_df = cp_month_gb.agg({"Pre-GST Parts": "sum"})
    pp_month_sum_df = pp_month_gb.agg({"Pre-GST Parts": "sum"})
    # Reset index to get Month Name as a column for proper dictionary mapping
    cp_month_sum_df = cp_month_sum_df.reset_index() if "Pre-GST Parts" in cp_month_sum_df.columns else pd.DataFrame(columns=["Month Name", "Pre-GST Parts"])
    pp_month_sum_df = pp_month_sum_df.reset_index() if "Pre-GST Parts" in pp_month_sum_df.columns else pd.DataFrame(columns=["Month Name", "Pre-GST Parts"])
    cp_month_sum = dict(zip(cp_month_sum_df["Month Name"], cp_month_sum_df["Pre-GST Parts"])) if "Month Name" in cp_month_sum_df.columns else {}
    pp_month_sum = dict(zip(pp_month_sum_df["Month Name"], pp_month_sum_df["Pre-GST Parts"])) if "Month Name" in pp_month_sum_df.columns else {}
    cp_loc_month_piv = pivot_summary(cp, index="Location Name", columns="Month Name", values="Pre-GST Parts", aggfunc="sum", fill_value=0)
    pp_loc_month_piv = pivot_summary(pp, index="Location Name", columns="Month Name", values="Pre-GST Parts", aggfunc="sum", fill_value=0)

    # Sparkline data: last 6 months of revenue
    cp_month_sum_df_sorted = cp_month_sum_df.sort_values("Month_Sort", ascending=True) if "Month_Sort" in cp_month_sum_df.columns else cp_month_sum_df
    revenue_sparkline = cp_month_sum_df_sorted["Pre-GST Parts"].tail(6).tolist() if "Pre-GST Parts" in cp_month_sum_df.columns else []
    
    # Category panels — use cached category_summary
    CAT_COLS = ["Parts_Sale", "Oil_Sale", "Accessory_Sale", "Tyre_Sale", "Battery_Sale", "Other_Sale"]
    cp_cat_sum = category_summary(cp, CAT_COLS)
    pp_cat_sum = category_summary(pp, CAT_COLS)
    has_category_data = cp_cat_sum.sum() > 0
    
    def _cat_stats(cat_col):
        cp_v = cp_cat_sum[cat_col] if cat_col in cp_cat_sum.index else 0
        pp_v = pp_cat_sum[cat_col] if cat_col in pp_cat_sum.index else 0
        cp_j = get_jobcard_count(cp) if "JC_Nos." in cp.columns else 0
        pp_j = get_jobcard_count(pp) if "JC_Nos." in pp.columns else 0
        return {
            "cp_rev": cp_v, "pp_rev": pp_v,
            "cp_jobs": cp_j, "pp_jobs": pp_j,
            "cp_rpc": calc_ratio(cp_v, cp_j) if cp_j > 0 else 0,
            "pp_rpc": calc_ratio(pp_v, pp_j) if pp_j > 0 else 0,
        }
    
    std_stats = _cat_stats("Parts_Sale") if has_category_data else None
    oil_stats = _cat_stats("Oil_Sale") if has_category_data else None
    
    if has_category_data:
        addon_cols = ["Accessory_Sale", "Tyre_Sale", "Battery_Sale", "Other_Sale"]
        cp_addon = sum(cp_cat_sum[c] for c in addon_cols if c in cp_cat_sum.index)
        pp_addon = sum(pp_cat_sum[c] for c in addon_cols if c in pp_cat_sum.index)
        cp_j = get_jobcard_count(cp) if "JC_Nos." in cp.columns else 0
        pp_j = get_jobcard_count(pp) if "JC_Nos." in pp.columns else 0
        addon_stats = {
            "cp_rev": cp_addon, "pp_rev": pp_addon,
            "cp_jobs": cp_j, "pp_jobs": pp_j,
            "cp_rpc": calc_ratio(cp_addon, cp_j) if cp_j > 0 else 0,
            "pp_rpc": calc_ratio(pp_addon, pp_j) if pp_j > 0 else 0,
        }
    else:
        addon_stats = None
    
    return {
        "cp": cp, "pp": pp,
        "cp_val": cp_val, "pp_val": pp_val, "growth_pct": growth_pct,
        "cp_jc": cp_jc, "pp_jc": pp_jc,
        "cp_rpc": cp_rpc, "pp_rpc": pp_rpc, "rpc_growth": rpc_growth,
        "cp_margin_pct": cp_margin_pct, "pp_margin_pct": pp_margin_pct,
        "margin_delta_pp": margin_delta_pp,
        "cp_oil_pen": cp_oil_pen, "pp_oil_pen": pp_oil_pen, "oil_pen_growth": oil_pen_growth,
        "cp_parts_per_jc": cp_parts_per_jc, "pp_parts_per_jc": pp_parts_per_jc, "parts_per_jc_growth": parts_per_jc_growth,
        "cp_health_score": cp_health_score, "pp_health_score": pp_health_score, "health_score_growth": health_score_growth,
        "cp_discount_rate": cp_discount_rate, "pp_discount_rate": pp_discount_rate, "discount_rate_growth": discount_rate_growth,
        "revenue_sparkline": revenue_sparkline,
        "loc_df": loc_df, "valid_locs": valid_locs,
        "best_loc": best_loc, "best_growth": best_growth,
        "worst_loc": worst_loc, "worst_growth": worst_growth,
        "n_growing": n_growing, "n_total": n_total,
        "declining_locs": declining_locs,
        "low_margin_locs": low_margin_locs,
        "cp_loc_jc": cp_loc_jc, "pp_loc_jc": pp_loc_jc,
        "cp_month_sum": cp_month_sum, "pp_month_sum": pp_month_sum,
        "cp_loc_month_piv": cp_loc_month_piv, "pp_loc_month_piv": pp_loc_month_piv,
        "has_category_data": has_category_data,
        "std_stats": std_stats, "oil_stats": oil_stats, "addon_stats": addon_stats,
    }


def _render_narrative_banner(d):
    alerts = []
    severity = "info"

    if d["growth_pct"] < 0:
        severity = "error"
        alerts.append(f"Parts Revenue declined {abs(d['growth_pct']):.1f}% vs prior period")

    if d["declining_locs"]:
        if severity != "error":
            severity = "warning"
        alerts.append(f"{len(d['declining_locs'])} location(s) declined vs prior period")

    if d["low_margin_locs"]:
        if severity not in ("error", "warning"):
            severity = "warning"
        alerts.append(f"{len(d['low_margin_locs'])} location(s) below 11% margin target")

    if d["n_total"] > 1 and d["cp_val"] > d["pp_val"]:
        total_delta = d["cp_val"] - d["pp_val"]
        best_delta = d["loc_df"].loc[d["best_loc"], "Delta"] if d["best_loc"] in d["loc_df"].index else 0
        if total_delta > 0 and best_delta / total_delta > 0.50:
            alerts.append(f"{d['best_loc']} driving >50% of total growth")

    if not alerts:
        return

    colors = {"error": T.COLOR_DANGER_BG, "warning": T.COLOR_WARNING_BG, "info": T.COLOR_INFO_BG}
    borders = {"error": T.COLOR_DANGER, "warning": T.COLOR_WARNING, "info": T.COLOR_PRIMARY}
    msg = "  ·  ".join(alerts)
    st.markdown(
        f'<div style="background:{colors[severity]};border-left:4px solid {borders[severity]};'
        f'padding:10px 14px;border-radius:6px;margin-bottom:12px;'
        f'font-size:var(--type-sm);font-weight:600;">{msg}</div>',
        unsafe_allow_html=True)


def _render_ai_narrative(d, mode_str):
    """Render template-based AI narrative paragraph."""
    st.markdown('<div class="section-title">🤖 Performance Summary</div>', unsafe_allow_html=True)

    growth = d["growth_pct"]
    margin = d["cp_margin_pct"]
    oil_pen = d["cp_oil_pen"]
    parts_per_jc = d["cp_parts_per_jc"]
    best_loc = d["best_loc"]
    worst_loc = d["worst_loc"]

    # Build narrative
    sentences = []

    # Growth narrative
    if growth > 15:
        sentences.append(f"Parts revenue showed strong growth of {growth:.1f}% {mode_str}.")
    elif growth > 0:
        sentences.append(f"Parts revenue grew {growth:.1f}% {mode_str}.")
    elif growth > -10:
        sentences.append(f"Parts revenue declined {abs(growth):.1f}% {mode_str}.")
    else:
        sentences.append(f"Parts revenue declined significantly by {abs(growth):.1f}% {mode_str}.")

    # Margin narrative
    if margin >= 12:
        sentences.append(f"Margin performance is healthy at {margin:.1f}%.")
    elif margin >= 10:
        sentences.append(f"Margin is at {margin:.1f}%, slightly below target.")
    else:
        sentences.append(f"Margin is concerning at {margin:.1f}%, below the 10% threshold.")

    # Oil penetration narrative
    if oil_pen >= 70:
        sentences.append(f"Oil penetration is excellent at {oil_pen:.1f}%.")
    elif oil_pen >= 60:
        sentences.append(f"Oil penetration is {oil_pen:.1f}%, meeting minimum standards.")
    else:
        sentences.append(f"Oil penetration is low at {oil_pen:.1f}%, needs improvement.")

    # Parts/JC narrative
    if parts_per_jc >= 3.2:
        sentences.append(f"Parts per job card is strong at {parts_per_jc:.1f}.")
    elif parts_per_jc >= 3.0:
        sentences.append(f"Parts per job card is {parts_per_jc:.1f}, near benchmark.")
    else:
        sentences.append(f"Parts per job card is {parts_per_jc:.1f}, below the 3.0 benchmark.")

    # Location performance
    if best_loc != "—" and worst_loc != "—":
        sentences.append(f"{best_loc} is the top performer while {worst_loc} needs attention.")

    narrative = " ".join(sentences)

    st.markdown(
        f'<div style="background:{T.COLOR_SURFACE2};padding:16px;border-radius:8px;'
        f'border-left:4px solid {T.COLOR_PRIMARY};font-size:var(--type-base);'
        f'line-height:1.6;color:{T.COLOR_TEXT_PRIMARY};">{narrative}</div>',
        unsafe_allow_html=True
    )


def _render_executive_panel(d, mode_str):
    rev_cp = fmt_inr_short(d["cp_val"])
    rev_pp = fmt_inr_short(d["pp_val"])

    load_cp = fmt_num(d['cp_jc'])
    load_pp = fmt_num(d['pp_jc'])

    margin_cp = f"{d['cp_margin_pct']:.1f}%"
    margin_pp = f"PP {d['pp_margin_pct']:.1f}%"

    # Oil Penetration Rate with 70% benchmark
    oil_pen_cp = f"{d['cp_oil_pen']:.1f}%"
    oil_pen_pp = f"PP {d['pp_oil_pen']:.1f}%"

    # Parts per JC with 3.2 benchmark
    parts_per_jc_cp = f"{d['cp_parts_per_jc']:.1f}"
    parts_per_jc_pp = f"PP {d['pp_parts_per_jc']:.1f}"

    # Health Score with 80 benchmark
    health_score_cp = f"{d['cp_health_score']:.0f}"
    health_score_pp = f"PP {d['pp_health_score']:.0f}"
    health_color = T.COLOR_SUCCESS if d['cp_health_score'] >= 80 else (T.COLOR_WARNING if d['cp_health_score'] >= 60 else T.COLOR_DANGER)

    # Discount Rate with 2% benchmark
    discount_rate_cp = f"{d['cp_discount_rate']:.2f}%"
    discount_rate_pp = f"PP {d['pp_discount_rate']:.2f}%"

    def _svc_panel(title, stats):
        rev_delta = stats["cp_rev"] - stats["pp_rev"]
        delta_pill = ""
        if rev_delta != 0:
            delta_str = fmt_inr_short(abs(rev_delta))
            if rev_delta > 0:
                delta_pill = f'<span style="background:{T.COLOR_SUCCESS_BG};color:{T.COLOR_ICON_SUCCESS};border-radius:12px;padding:2px 8px;font-size:11px;font-weight:600;margin-left:8px;">+{delta_str} \u20b9</span>'
            else:
                delta_pill = f'<span style="background:{T.COLOR_DANGER_BG};color:{T.COLOR_ICON_DANGER};border-radius:12px;padding:2px 8px;font-size:11px;font-weight:600;margin-left:8px;">-{delta_str} \u20b9</span>'
        return render_svc_panel(title, stats, delta_pill)

    # Eight KPI cards using MetricCard/KPIGrid
    kpi_metrics = [
        {
            "label": "PARTS REVENUE",
            "value": rev_cp,
            "cp": d["cp_val"],
            "pp": d["pp_val"],
            "pp_label": rev_pp,
            "sparkline": d["revenue_sparkline"] if len(d.get("revenue_sparkline", [])) >= 2 else None,
        },
        {
            "label": "GROWTH RATE",
            "value": f"{d['growth_pct']:+.1f}%",
            "sub": "vs Prior Period",
        },
        {
            "label": "LOAD",
            "value": load_cp,
            "cp": d["cp_jc"],
            "pp": d["pp_jc"],
            "pp_label": load_pp,
        },
        {
            "label": "PARTS MARGIN",
            "value": margin_cp,
            "cp": d["cp_margin_pct"],
            "pp": d["pp_margin_pct"],
            "pp_label": margin_pp,
        },
        {
            "label": "DISCOUNT RATE",
            "value": discount_rate_cp,
            "cp": d["cp_discount_rate"],
            "pp": d["pp_discount_rate"],
            "pp_label": discount_rate_pp,
            "benchmark": "2%",
            "invert_trend": True,  # Lower discount is better
        },
        {
            "label": "OIL PENETRATION",
            "value": oil_pen_cp,
            "cp": d["cp_oil_pen"],
            "pp": d["pp_oil_pen"],
            "pp_label": oil_pen_pp,
            "benchmark": "70%",
        },
        {
            "label": "PARTS/JC",
            "value": parts_per_jc_cp,
            "cp": d["cp_parts_per_jc"],
            "pp": d["pp_parts_per_jc"],
            "pp_label": parts_per_jc_pp,
            "benchmark": "3.2",
        },
        {
            "label": "HEALTH SCORE",
            "value": health_score_cp,
            "cp": d["cp_health_score"],
            "pp": d["pp_health_score"],
            "pp_label": health_score_pp,
            "benchmark": "80",
        },
    ]
    KPIGrid(kpi_metrics, cols=4)

    st.markdown('<div style="margin:var(--space-4) 0 var(--space-3) 0;border-top:1px solid var(--color-border);"></div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-label" style="margin-bottom:var(--space-3);">CATEGORY BREAKDOWN — CP VS PP</div>', unsafe_allow_html=True)

    if d["has_category_data"]:
        col4, col5, col6 = st.columns(3)
        with col4:
            st.markdown(_svc_panel("STANDARD PARTS", d["std_stats"]), unsafe_allow_html=True)
        with col5:
            st.markdown(_svc_panel("OIL / LUBRICANTS", d["oil_stats"]), unsafe_allow_html=True)
        with col6:
            st.markdown(_svc_panel("ADD-ONS", d["addon_stats"]), unsafe_allow_html=True)
    else:
        st.info("📦 Category breakdown available from Jan-26 onwards. Showing total parts revenue only.")


def _render_waterfall(d, mode_str):
    """Render Category Contribution Waterfall chart showing which categories drove growth."""
    if not d["has_category_data"]:
        return

    st.markdown('<div class="section-title">💧 Category Contribution to Revenue Growth</div>', unsafe_allow_html=True)

    # Calculate category deltas
    categories = ["Standard Parts", "Oil", "Add-ons"]
    cat_cp = {
        "Standard Parts": d["std_stats"]["cp_rev"] if d["std_stats"] else 0,
        "Oil": d["oil_stats"]["cp_rev"] if d["oil_stats"] else 0,
        "Add-ons": d["addon_stats"]["cp_rev"] if d["addon_stats"] else 0,
    }
    cat_pp = {
        "Standard Parts": d["std_stats"]["pp_rev"] if d["std_stats"] else 0,
        "Oil": d["oil_stats"]["pp_rev"] if d["oil_stats"] else 0,
        "Add-ons": d["addon_stats"]["pp_rev"] if d["addon_stats"] else 0,
    }

    # Build waterfall data
    x = ["PP Total"] + categories + ["CP Total"]
    y = [d["pp_val"]]
    measure = ["absolute"]
    colors = [T.COLOR_BORDER]

    running_total = d["pp_val"]
    for cat in categories:
        delta = cat_cp[cat] - cat_pp[cat]
        y.append(delta)
        measure.append("relative")
        running_total += delta
        if delta >= 0:
            colors.append(T.COLOR_SUCCESS)
        else:
            colors.append(T.COLOR_DANGER)

    y.append(d["cp_val"])
    measure.append("total")
    colors.append(T.COLOR_PRIMARY)

    fig = go.Figure(go.Waterfall(
        x=x,
        y=y,
        measure=measure,
        text=[fmt_inr_short(v) for v in y],
        textposition="outside",
        textfont=dict(size=12, family=T.FONT_FAMILY, weight=700),
        decreasing=dict(marker=dict(color=T.COLOR_DANGER)),
        increasing=dict(marker=dict(color=T.COLOR_SUCCESS)),
        totals=dict(marker=dict(color=T.COLOR_PRIMARY)),
    ))

    fig = ChartEngine.apply_chart(fig, title=f"Category Contribution — {mode_str}", height=400, size="full")
    st.plotly_chart(fig, use_container_width=True)


def _render_low_margin_locations(d):
    """Render table of locations with margin below 10%."""
    if not d["low_margin_locs"]:
        return

    st.markdown('<div class="section-title">⚠️ Low-Performing Locations (Margin < 10%)</div>', unsafe_allow_html=True)

    loc_df = d["loc_df"].copy()
    low_margin_df = loc_df[loc_df.index.isin(d["low_margin_locs"])].copy()

    if low_margin_df.empty:
        return

    low_margin_df = low_margin_df.sort_values("Margin_CP", ascending=True)

    rows = []
    for loc in low_margin_df.index:
        rows.append({
            "Location": loc,
            "Revenue": low_margin_df.loc[loc, "CP"],
            "Margin %": low_margin_df.loc[loc, "Margin_CP"],
            "Growth %": low_margin_df.loc[loc, "Growth"],
            "Oil Pen %": low_margin_df.loc[loc, "Oil_Pen_CP"],
            "Parts/JC": low_margin_df.loc[loc, "Parts_Per_JC_CP"],
        })

    ldf = pd.DataFrame(rows)

    fmt_dict = {
        "Revenue": fmt_inr_full,
        "Margin %": lambda v: f"{v:.1f}%",
        "Growth %": lambda v: f"{v:+.1f}%" if pd.notna(v) else "—",
        "Oil Pen %": lambda v: f"{v:.1f}%",
        "Parts/JC": lambda v: f"{v:.1f}",
    }

    styled = ldf.style.format(fmt_dict)
    styled = styled.map(style_margin_color, subset=["Margin %"])
    styled = styled.map(style_color_growth, subset=["Growth %"])

    st.dataframe(styled, use_container_width=True, hide_index=True)


def _render_category_heatmap(d, mode_str):
    """Render Category Growth Heatmap showing growth by category."""
    if not d["has_category_data"]:
        return

    st.markdown('<div class="section-title">📊 Category Growth Heatmap</div>', unsafe_allow_html=True)

    categories = ["Standard Parts", "Oil", "Add-ons"]
    cat_cp = {
        "Standard Parts": d["std_stats"]["cp_rev"] if d["std_stats"] else 0,
        "Oil": d["oil_stats"]["cp_rev"] if d["oil_stats"] else 0,
        "Add-ons": d["addon_stats"]["cp_rev"] if d["addon_stats"] else 0,
    }
    cat_pp = {
        "Standard Parts": d["std_stats"]["pp_rev"] if d["std_stats"] else 0,
        "Oil": d["oil_stats"]["pp_rev"] if d["oil_stats"] else 0,
        "Add-ons": d["addon_stats"]["pp_rev"] if d["addon_stats"] else 0,
    }

    # Calculate growth percentages
    growth_data = []
    for cat in categories:
        growth = calc_growth_pct(cat_cp[cat], cat_pp[cat], fill_value=0)
        growth_data.append(growth)

    # Create heatmap using Plotly
    fig = go.Figure(data=go.Heatmap(
        z=[growth_data],
        x=categories,
        y=["Growth %"],
        colorscale="RdYlGn",
        zmid=0,
        text=[f"{g:+.1f}%" for g in growth_data],
        textfont={"size": 14, "color": "white", "family": T.FONT_FAMILY, "weight": 700},
        hovertemplate="<b>%{x}</b><br>Growth: %{z:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        title=f"Category Growth — {mode_str}",
        xaxis_title="Category",
        yaxis_title=None,
        height=200,
        margin=dict(l=10, r=10, t=40, b=10),
    )

    fig.update_yaxes(showticklabels=False)
    st.plotly_chart(fig, use_container_width=True)


def _render_charts(d, active_pairs, mode_str, ctx=None):
    """Render analytical charts for Parts Executive"""
    inject_responsive_css()
    col_trend, col_loc = st.columns([6, 4])
    
    with col_trend:
        months = [p[0] for p in active_pairs]
        cp_vals = [d["cp_month_sum"].get(m, 0) for m in months]
        pp_vals = [d["pp_month_sum"].get(m, 0) for m in months]
        growth = [calc_growth_pct(c, p, fill_value=0) for c, p in zip(cp_vals, pp_vals)]

        overall_growth = sum(growth) / len(growth) if growth else 0
        growth_line_color = T.COLOR_SUCCESS if overall_growth > 0 else T.COLOR_DANGER

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Current Period", x=months, y=cp_vals,
            marker_color=T.COLOR_PRIMARY,
            text=[fmt_inr_short(v) for v in cp_vals], textposition="outside",
            textfont=dict(size=14, family=T.FONT_FAMILY, color=T.COLOR_TEXT_PRIMARY, weight=700),
            hovertemplate="<b>%{x}</b><br>CP: %{y:,.0f}<br>PP: %{customdata[0]:,.0f}<br>Growth: %{customdata[1]:.1f}%<extra></extra>",
            customdata=list(zip(pp_vals, growth))))
        fig.add_trace(go.Bar(
            name="Prior Period", x=months, y=pp_vals, marker_color=T.COLOR_BORDER, opacity=0.7,
            text=[fmt_inr_short(v) for v in pp_vals], textposition="outside",
            textfont=dict(size=14, family=T.FONT_FAMILY, color=T.COLOR_TEXT_SECONDARY)))
        
        marker_colors = [T.COLOR_SUCCESS if g > 0 else T.COLOR_DANGER if g < 0 else T.COLOR_TEXT_SECONDARY for g in growth]
        
        fig.add_trace(go.Scatter(
            name="Growth %", x=months, y=growth,
            mode="lines+markers", yaxis="y2",
            line=dict(color=growth_line_color, width=3),
            marker=dict(size=10, color=marker_colors,
                        line=dict(width=2, color="white"))))

        # Add target overlay if ctx.target_provider is available
        if ctx is not None and hasattr(ctx, 'target_provider'):
            target_vals = []
            achievement_pcts = []
            variances = []
            for m in months:
                # Use target_provider for the specific month
                m_target = ctx.target_provider.get_parts_target(d["cp"]["Location Name"].unique().tolist(), [m])
                target_vals.append(m_target)
                
                # Calculate achievement % and variance
                cp_val = d["cp_month_sum"].get(m, 0)
                if m_target > 0:
                    achievement = calc_ratio(cp_val, m_target, multiplier=100, fill_value=0)
                    variance = cp_val - m_target
                else:
                    achievement = 0
                    variance = 0
                achievement_pcts.append(achievement)
                variances.append(variance)
            
            # Add target line
            fig.add_trace(go.Scatter(
                name="Target", x=months, y=target_vals,
                mode="lines+markers", line=dict(dash="dash", color=T.COLOR_WARNING, width=2),
                marker=dict(size=8, color=T.COLOR_WARNING),
                hovertemplate="<b>%{x}</b><br>Target: %{y:,.0f}<extra></extra>"))
            
            # Add achievement annotations
            for m, cp_val, target, ach, var in zip(months, cp_vals, target_vals, achievement_pcts, variances):
                if target > 0:
                    fig.add_annotation(
                        x=m, y=target, xref="x", yref="y",
                        text=f"Ach: {ach:.0f}% | Var: {fmt_inr_short(var)}",
                        showarrow=False,
                        font=dict(size=11, family=T.FONT_FAMILY, color=T.COLOR_TEXT_SECONDARY),
                        bgcolor="white", bordercolor=T.COLOR_BORDER, borderpad=3, yshift=-30
                    )

        growth_annotations = []
        for m, g in zip(months, growth):
            growth_annotations.append(dict(
                x=m, y=g, xref="x", yref="y2",
                text=f"{g:+.1f}%",
                showarrow=False,
                font=dict(size=13, family=T.FONT_FAMILY, color=T.COLOR_SUCCESS if g > 0 else T.COLOR_DANGER if g < 0 else T.COLOR_TEXT_SECONDARY, weight=700),
                bgcolor="white", bordercolor="white", borderpad=2, yshift=26
            ))
        
        fig = ChartEngine.apply_chart(fig, title=f"Parts Revenue Trend — {mode_str}  ·  click bar to filter by month", height=450, y_title="₹ in Cr", barmode="group", size="full")
        fig.update_layout(
            yaxis2=dict(title="Growth %", overlaying="y", side="right", tickformat=".1f", showgrid=False, title_font=dict(size=15, family=T.FONT_FAMILY), tickfont=dict(size=14, family=T.FONT_FAMILY)),
            annotations=growth_annotations
        )

        ev = st.plotly_chart(fig, use_container_width=True,
                             on_select="rerun", selection_mode="points",
                             key="parts_chart_trend")
        if ev and ev.selection and ev.selection.points:
            cm = ev.selection.points[0].get("x")
            if cm and cm != StateManager.get("parts_cross_month"):
                StateManager.set("parts_cross_month", cm)
                st.rerun()
        
        st.markdown(
            '<div style="font-size:11px;color:var(--color-text-secondary);text-align:center;margin-top:4px;">'
            '\u1f50d Click chart bars to filter by month</div>',
            unsafe_allow_html=True
        )
    
    with col_loc:
        ldf = d["valid_locs"].copy()
        if not ldf.empty:
            ldf = ldf.sort_values("Growth", ascending=True)
            colors = [T.COLOR_SUCCESS if g >= 0 else T.COLOR_DANGER for g in ldf["Growth"]]
            
            fig = go.Figure(go.Bar(
                x=ldf["Growth"].round(1),
                y=ldf.index,
                orientation="h",
                marker_color=colors,
                text=[f"{g:+.1f}%" for g in ldf["Growth"].round(1)],
                textposition="outside",
                textfont=dict(size=12, family=T.FONT_FAMILY, weight=700),
                hovertemplate="<b>%{y}</b><br>Growth: %{x:.1f}%<extra></extra>"
            ))
            
            fig = ChartEngine.apply_chart(fig,
                title=f"Location Growth — {mode_str}",
                height=450,
                x_title="Growth %",
                size="full")
            
            fig.add_vline(x=0, line_color=T.COLOR_BORDER, line_width=1.5)
            
            st.plotly_chart(fig, use_container_width=True)


def _render_executive_table(d, active_pairs, mode_str):
    section_title(f"📊 Executive Location Performance — {mode_str}")
    
    all_locs = sorted(set(d["cp_loc_month_piv"]["Location Name"]) |
                      set(d["pp_loc_month_piv"]["Location Name"]))
    
    # Compute PP-period ranks for rank movement
    pp_loc = d["loc_df"]["PP"].sort_values(ascending=False)
    pp_ranks = {loc: i+1 for i, loc in enumerate(pp_loc.index)}
    cp_loc = d["loc_df"]["CP"].sort_values(ascending=False)
    cp_ranks = {loc: i+1 for i, loc in enumerate(cp_loc.index)}
    
    rows = []
    for loc in all_locs:
        lcp = d["loc_df"].loc[loc, "CP"] if loc in d["loc_df"].index else 0
        lpp = d["loc_df"].loc[loc, "PP"] if loc in d["loc_df"].index else 0
        growth = d["loc_df"].loc[loc, "Growth"] if loc in d["loc_df"].index else 0
        delta = d["loc_df"].loc[loc, "Delta"] if loc in d["loc_df"].index else 0
        margin_cp = d["loc_df"].loc[loc, "Margin_CP"] if loc in d["loc_df"].index else 0
        oil_pen_cp = d["loc_df"].loc[loc, "Oil_Pen_CP"] if loc in d["loc_df"].index else 0
        parts_per_jc_cp = d["loc_df"].loc[loc, "Parts_Per_JC_CP"] if loc in d["loc_df"].index else 0

        cp_jc = d["cp_loc_jc"].get(loc, 0) if "cp_loc_jc" in d else 0

        rows.append({
            "Location": loc,
            "Revenue": lcp,
            "Growth %": growth,
            "Margin %": margin_cp,
            "Job Cards": cp_jc,
            "Parts/JC": parts_per_jc_cp,
            "Oil Pen %": oil_pen_cp,
            "Difference": delta,
            "Rank": compute_rank_movement(loc, cp_ranks, pp_ranks)
        })

    total_cp = d["cp_val"]
    total_pp = d["pp_val"]
    total_delta = total_cp - total_pp
    total_growth = calc_growth_pct(total_cp, total_pp, fill_value=0)
    total_jc = d["cp_jc"]
    total_parts_per_jc = d["cp_parts_per_jc"]
    total_oil_pen = d["cp_oil_pen"]

    rows.append({
        "Location": "TOTAL",
        "Revenue": total_cp,
        "Growth %": total_growth,
        "Margin %": d["cp_margin_pct"],
        "Job Cards": total_jc,
        "Parts/JC": total_parts_per_jc,
        "Oil Pen %": total_oil_pen,
        "Difference": total_delta,
        "Rank": "—"
    })
    
    tdf = pd.DataFrame(rows)
    
    total_row = tdf[tdf["Location"] == "TOTAL"].copy()
    loc_rows = tdf[tdf["Location"] != "TOTAL"].sort_values("Growth %", ascending=False)
    tdf = pd.concat([loc_rows, total_row], ignore_index=True)
    
    tdf["Rank"] = None
    for idx, row in tdf.iterrows():
        if row["Location"] != "TOTAL":
            tdf.at[idx, "Rank"] = compute_rank_movement(row["Location"], cp_ranks, pp_ranks)
    
    cc = {
        "Location": st.column_config.TextColumn("Location"),
        "Revenue": st.column_config.NumberColumn("Revenue"),
        "Growth %": st.column_config.NumberColumn("Growth %"),
        "Margin %": st.column_config.NumberColumn("Margin %"),
        "Job Cards": st.column_config.NumberColumn("Job Cards"),
        "Parts/JC": st.column_config.NumberColumn("Parts/JC"),
        "Oil Pen %": st.column_config.NumberColumn("Oil Pen %"),
        "Difference": st.column_config.NumberColumn("Difference"),
        "Rank": st.column_config.TextColumn("Rank Δ"),
    }

    styled = tdf.style.apply(style_table_bold_total, axis=1)
    styled = styled.map(style_color_growth, subset=["Growth %", "Difference"])
    styled = styled.map(style_margin_color, subset=["Margin %"])

    # Conditional formatting for Parts/JC and Oil Pen %
    def _parts_jc_color(val):
        if val < 3.0: return f"color:{T.COLOR_DANGER};font-weight:700"
        if val < 3.2: return f"color:{T.COLOR_WARNING};font-weight:700"
        return ""

    def _oil_pen_color(val):
        if val < 60: return f"color:{T.COLOR_DANGER};font-weight:700"
        if val < 70: return f"color:{T.COLOR_WARNING};font-weight:700"
        return ""

    styled = styled.map(_parts_jc_color, subset=["Parts/JC"])
    styled = styled.map(_oil_pen_color, subset=["Oil Pen %"])

    styled = styled.format({
        "Revenue": fmt_inr_full,
        "Growth %": lambda v: f"{v:+.1f}%",
        "Margin %": lambda v: f"{v:.1f}%",
        "Job Cards": fmt_num,
        "Parts/JC": lambda v: f"{v:.1f}",
        "Oil Pen %": lambda v: f"{v:.1f}%",
        "Difference": fmt_inr_full,
        "Rank": format_rank_movement,
    })

    st.dataframe(
        styled,
        column_config=cc,
        use_container_width=True,
        on_select="rerun",
        key="parts_executive_table",
        selection_mode="single-row"
    )
    
    # Handle location drill-through
    if st.session_state.get("parts_executive_table_selection", {}).get("row_ids"):
        selected_idx = st.session_state["parts_executive_table_selection"]["row_ids"][0]
        selected_location = tdf.iloc[selected_idx]["Location"]
        if selected_location != "TOTAL":
            if st.button(f"🔍 View {selected_location} in Parts Detail", key="drill_location_btn"):
                navigate_to_page("Parts Detail", drill_params={"location": selected_location})
    
    from services.export_service import ExportMeta
    meta = ExportMeta(
        report_title="Parts Executive",
        location="All Locations",
        date_range=", ".join([str(p[2]) for p in active_pairs]) if active_pairs else "",
    )
    render_export_buttons(tdf, meta, key_prefix="parts_executive")


def _render_monthly_detail(d, active_pairs, mode_str):
    with st.expander("▶ Monthly Location Performance (Detailed View)", expanded=False):
        section_title(f"📊 Monthly Detail — {mode_str}")
        
        all_locs = sorted(set(d["cp_loc_month_piv"]["Location Name"]) |
                          set(d["pp_loc_month_piv"]["Location Name"]))
        t2_rows = []
        for loc in all_locs:
            row = {"Location": loc}
            for cm, pm, _ in active_pairs:
                cv = (d["cp_loc_month_piv"].set_index("Location Name").loc[loc, cm]
                      if loc in d["cp_loc_month_piv"]["Location Name"].values
                      and cm in d["cp_loc_month_piv"].columns else 0)
                pv = (d["pp_loc_month_piv"].set_index("Location Name").loc[loc, pm]
                      if loc in d["pp_loc_month_piv"]["Location Name"].values
                      and pm in d["pp_loc_month_piv"].columns else 0)
                row[f"{cm[:3]} Parts_CP"] = cv
                row[f"{cm[:3]} Parts_PP"] = pv
                row[f"{cm[:3]} YoY%"] = calc_growth_pct(cv, pv, fill_value=np.nan)
            t2_rows.append(row)

        totals = {"Location": "TOTAL"}
        for cm, pm, _ in active_pairs:
            tcv = sum(r.get(f"{cm[:3]} Parts_CP", 0) for r in t2_rows)
            tpv = sum(r.get(f"{cm[:3]} Parts_PP", 0) for r in t2_rows)
            totals[f"{cm[:3]} Parts_CP"] = tcv
            totals[f"{cm[:3]} Parts_PP"] = tpv
            totals[f"{cm[:3]} YoY%"] = calc_growth_pct(tcv, tpv, fill_value=np.nan)
        t2_rows.append(totals)

        t2df = pd.DataFrame(t2_rows)
        t2cc = {"Location": st.column_config.TextColumn("Location")}
        
        format_dict = {}
        color_subset = []
        for cm, _, _ in active_pairs:
            t2cc[f"{cm[:3]} Parts_CP"] = st.column_config.NumberColumn(f"{cm[:3]} Parts_CP")
            t2cc[f"{cm[:3]} Parts_PP"] = st.column_config.NumberColumn(f"{cm[:3]} Parts_PP")
            t2cc[f"{cm[:3]} YoY%"] = st.column_config.NumberColumn(f"{cm[:3]} YoY%")
            
            format_dict[f"{cm[:3]} Parts_CP"] = fmt_inr_full
            format_dict[f"{cm[:3]} Parts_PP"] = fmt_inr_full
            format_dict[f"{cm[:3]} YoY%"] = lambda v: f"{v:+.1f}%" if pd.notna(v) else "—"
            color_subset.append(f"{cm[:3]} YoY%")
            
            
        styled2 = t2df.style.apply(style_table_bold_total, axis=1)
        styled2 = styled2.map(style_color_growth, subset=color_subset)
        styled2 = styled2.format(format_dict)
            
        st.dataframe(styled2, column_config=t2cc, use_container_width=True, hide_index=True)


def render(df, ctx, pairs, comparison_mode=True, selected_months=None):
    inject_responsive_css()
    PageBreadcrumb(["Commercial", "Parts Executive"])
    if df.empty:
        EmptyState("No parts data for the selected period.")
        return

    _init_state()
    
    mode_str = "YoY" if comparison_mode else "MoM"
    active_pairs = pairs if pairs else []
    
    if not active_pairs:
        EmptyState("No matching prior period data for the selected comparison mode.")
        return

    cp, pp = _apply_filters(df, active_pairs)
    if cp.empty and pp.empty:
        EmptyState("No data matches the active filters.")
        return

    d = _compute_metrics(cp, pp, df)

    render_cross_filter_bar("parts_cross_month")
    _render_executive_panel(d, mode_str)
    _render_narrative_banner(d)
    _render_ai_narrative(d, mode_str)
    _render_waterfall(d, mode_str)
    _render_category_heatmap(d, mode_str)
    _render_charts(d, active_pairs, mode_str, ctx)
    _render_executive_table(d, active_pairs, mode_str)
    _render_low_margin_locations(d)
    _render_monthly_detail(d, active_pairs, mode_str)
    UniversalFooter()
