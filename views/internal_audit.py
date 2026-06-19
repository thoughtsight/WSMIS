import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from io import BytesIO
from datetime import datetime



from services.financial_service import FinancialService
from utils.calculations.fact_metrics import (
    get_labour_sales, get_parts_sales, get_net_labour, get_net_parts,
    get_labour_discount, get_parts_discount, get_oil_sales, get_tyre_sales,
    get_battery_sales, get_accessory_sales, get_total_margin, get_parts_profit,
    get_jobcard_count
)
from utils.calculations.revenue import (
    calculate_gross_revenue, calculate_net_revenue, calculate_total_revenue,
    calculate_revenue_per_jobcard, calculate_revenue_growth
)
from utils.calculations.margin import (
    calculate_total_margin, calculate_parts_margin, calculate_margin_per_jobcard,
    calculate_margin_growth, calculate_margin_kpis
)
from utils.calculations.discount import (
    calculate_labour_discount, calculate_parts_discount, calculate_total_discount,
    calculate_labour_discount_pct, calculate_parts_discount_pct,
    calculate_overall_discount_pct, calculate_discount_per_jobcard,
    calculate_discount_growth
)
from utils.calculations.leakage import (
    compute_discount_aggregates, compute_parts_leakage, compute_leakage_delta
)
from utils.calculations.common import (
    safe_divide, calc_ratio, calc_growth_pct, calc_contribution_pct,
    calc_achievement_pct, calc_variance
)
from utils.aggregations import (
    group_summary, location_summary, advisor_summary, monthly_summary,
    service_summary, dealer_summary, pivot_summary, top_n
)
from utils.filters import (
    apply_month_filter, apply_location_filter, apply_location_group_filter,
    apply_service_type_filter, apply_advisor_filter, apply_mp_pb_filter, split_cp_pp,
    filter_valid_advisors
)
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from utils.constants import ADV_COL, MP_COLORS
from config.settings import LABOUR_DISC_BENCH, PARTS_DISC_BENCH, HIGH_DISC_ALERT, DISC_CONCERN_PCT

# Import shared UI helpers from app
from ui.kpi_cards import kpi
from ui.tables import html_table, searchable_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from ui.export_buttons import render_export_buttons
from services.export_service import ExportMeta

def render(df_jctat, client_config, cp=None):
    """Internal Dealer Audit Report V2 — Investigation layer + native dashboard."""
    ia_tabs = st.tabs(["⚠️ Exception Audit", "💰 Revenue Leakage Dashboard", "🔧 Dealer Audit (Operational)"])

    # V2 INVESTIGATION LAYER (uses WSMIS CP data)
    with ia_tabs[0]:
        audit_df = cp if (cp is not None and not cp.empty) else pd.DataFrame()

        if not audit_df.empty and "Location Name" in audit_df.columns:
            st.markdown('<div class="section-card"><div class="section-title">🔍 Internal Audit V2 — Investigation Layer</div>', unsafe_allow_html=True)

            LAB_BENCH   = LABOUR_DISC_BENCH
            PARTS_BENCH = PARTS_DISC_BENCH

            # Shared aggregates — reuse Phase 2 helpers
            loc_lab   = compute_discount_aggregates(audit_df, "Location Name", LAB_BENCH)
            loc_parts = compute_parts_leakage(audit_df, "Location Name", PARTS_BENCH)

            adv_agg = filter_valid_advisors(audit_df, ADV_COL).groupby([ADV_COL, "Location Name"], dropna=False).agg(
                JCs=("JC_Nos.", "sum"), Revenue=("Pre-GST Labour", "sum"),
                DiscRs=("Labour Discount", "sum"), NetLab=("Net_Labour", "sum")
            ).reset_index()
            adv_agg = adv_agg[adv_agg["Revenue"] > 0].copy()
            if not adv_agg.empty:
                adv_agg["Disc_Pct"] = calc_ratio(adv_agg["DiscRs"], adv_agg["Revenue"], multiplier=100, fill_value=0)
                adv_agg["Leakage"]  = np.maximum(0, (adv_agg["Disc_Pct"] - LAB_BENCH) / 100 * adv_agg["Revenue"])
                adv_agg["AvgLabJC"] = np.where(adv_agg["JCs"] > 0, adv_agg["NetLab"] / adv_agg["JCs"], 0)
                adv_agg = adv_agg.sort_values("Leakage", ascending=False).reset_index(drop=True)

            def _sev_badge(d_pct):
                return "🔴" if d_pct >= 20 else ("🟡" if d_pct >= 15 else "🟢")

            # ── Section 1: Leakage Audit ─────────────────────────────
            with st.expander("📊 Leakage Audit — Location → Advisor Hierarchy", expanded=False):
                if not loc_lab.empty:
                    over_bench = loc_lab[loc_lab["Disc_Pct"] > LAB_BENCH].sort_values("Recoverable", ascending=False)
                    if not over_bench.empty:
                        for _, row in over_bench.head(5).iterrows():
                            _render_finding(
                                finding=f"Labour Discount Breach — {row['Location Name']}",
                                cause=f"Discount at {row['Disc_Pct']:.1f}% exceeds {LAB_BENCH}% benchmark",
                                impact=fmt_inr(row["Recoverable"]),
                                recommendation="Enforce discount approval matrix; cap advisor authority at benchmark level",
                                owner="Service Head / Location Manager",
                                priority="Critical" if row["Disc_Pct"] > HIGH_DISC_ALERT else "High"
                            )
                    else:
                        st.success(f"✅ All locations within {LAB_BENCH}% Labour Discount benchmark")

                    # Location leakage summary table
                    st.markdown("**Location Leakage Summary**")
                    if not loc_parts.empty:
                        lt = loc_lab.merge(loc_parts[["Location Name", "Recoverable"]], on="Location Name",
                                           suffixes=("_lab", "_parts"), how="left").fillna(0)
                        lt["Total"] = lt["Recoverable_lab"] + lt["Recoverable_parts"]
                    else:
                        lt = loc_lab.copy()
                        lt.rename(columns={"Recoverable": "Recoverable_lab"}, inplace=True)
                        lt["Recoverable_parts"] = 0; lt["Total"] = lt["Recoverable_lab"]
                    lt = lt.sort_values("Total", ascending=False).reset_index(drop=True)
                    html_table(pd.DataFrame({
                        "Location":       lt["Location Name"],
                        "Lab Disc %":     lt["Disc_Pct"].apply(lambda x: f"{x:.1f}%"),
                        "Lab Leakage":    lt["Recoverable_lab"].apply(fmt_inr),
                        "Parts Leakage":  lt["Recoverable_parts"].apply(fmt_inr),
                        "Total Leakage":  lt["Total"].apply(fmt_inr),
                        "":               lt["Disc_Pct"].apply(_sev_badge),
                    }), height="280px")

                    # Advisor drilldown
                    st.markdown("**Drill into Location → Advisor Breakdown**")
                    all_locs_ia = sorted(audit_df["Location Name"].dropna().unique().tolist())
                    sel_loc_ia = st.selectbox("Select Location", ["— Select —"] + all_locs_ia, key="ia_lkg_loc")
                    if sel_loc_ia != "— Select —":
                        adv_drill = filter_valid_advisors(audit_df[audit_df["Location Name"] == sel_loc_ia], ADV_COL).groupby(
                            ADV_COL, dropna=False
                        ).agg(JCs=("JC_Nos.","sum"), Rev=("Pre-GST Labour","sum"), Disc=("Labour Discount","sum")).reset_index()
                        adv_drill = adv_drill[adv_drill["Rev"] > 0].copy()
                        if not adv_drill.empty:
                            adv_drill["Disc_Pct"] = calc_ratio(adv_drill["Disc"], adv_drill["Rev"], multiplier=100, fill_value=0)
                            adv_drill["Leakage"]  = np.maximum(0, (adv_drill["Disc_Pct"] - LAB_BENCH) / 100 * adv_drill["Rev"])
                            adv_drill = adv_drill.sort_values("Leakage", ascending=False)
                            html_table(pd.DataFrame({
                                "Advisor":  adv_drill[ADV_COL],
                                "JCs":      adv_drill["JCs"].apply(fmt_num),
                                "Disc %":   adv_drill["Disc_Pct"].apply(lambda x: f"{x:.1f}%"),
                                "Leakage":  adv_drill["Leakage"].apply(fmt_inr),
                                "":         adv_drill["Disc_Pct"].apply(_sev_badge),
                            }), height="250px")
                else:
                    st.info("No leakage data available for this period")

            # ── Section 2: Labour Audit ──────────────────────────────
            with st.expander("🔵 Labour Audit — Revenue & Efficiency", expanded=False):
                loc_eff = location_summary(audit_df, as_index=True).agg(
                    JCs=("JC_Nos.", "sum"), NetLab=("Net_Labour", "sum")
                ).reset_index()
                loc_eff = loc_eff[loc_eff["JCs"] > 0].copy()
                if not loc_eff.empty:
                    loc_eff["AvgJC"] = loc_eff["NetLab"] / loc_eff["JCs"]
                    grp_median       = loc_eff["AvgJC"].median()
                    loc_eff          = loc_eff.sort_values("AvgJC", ascending=False)

                    below = loc_eff[loc_eff["AvgJC"] < grp_median]
                    if not below.empty:
                        for _, row in below.head(3).iterrows():
                            gap       = grp_median - row["AvgJC"]
                            potential = gap * row["JCs"]
                            _render_finding(
                                finding=f"Below-Median Labour/JC — {row['Location Name']}",
                                cause=f"Avg ₹{row['AvgJC']:,.0f}/JC vs group median ₹{grp_median:,.0f}",
                                impact=f"{fmt_inr(potential)} potential uplift",
                                recommendation="Audit service package adoption; review advisor upsell compliance",
                                owner="Location Manager",
                                priority="High" if gap > 500 else "Medium"
                            )
                    else:
                        st.success("✅ All locations at or above group median Labour/JC")

                    st.markdown("**Labour Efficiency by Location**")
                    html_table(pd.DataFrame({
                        "Location":       loc_eff["Location Name"],
                        "JCs":            loc_eff["JCs"].apply(fmt_num),
                        "Net Labour":     loc_eff["NetLab"].apply(fmt_inr),
                        "Avg Labour/JC":  loc_eff["AvgJC"].apply(fmt_inr),
                        "vs Median":      loc_eff["AvgJC"].apply(
                            lambda x: f"{'▲' if x >= grp_median else '▼'} ₹{abs(x - grp_median):,.0f}"
                        ),
                    }), height="280px")
                else:
                    st.info("No labour efficiency data available")

            # ── Section 3: Discount Audit ────────────────────────────
            with st.expander("🏷️ Discount Audit — Trend & Register", expanded=False):
                disc_trend = monthly_summary(audit_df, as_index=False).agg(
                    L=("Pre-GST Labour", "sum"), D=("Labour Discount", "sum")
                ).sort_values("Month_Sort")
                disc_trend["D%"] = calc_ratio(disc_trend["D"], disc_trend["L"], multiplier=100, fill_value=0)

                if not disc_trend.empty:
                    months_over = disc_trend[disc_trend["D%"] > LAB_BENCH]
                    if not months_over.empty:
                        worst = months_over.loc[months_over["D%"].idxmax()]
                        _render_finding(
                            finding=f"Labour Discount Exceeded Benchmark — {worst['Month Name']}",
                            cause=f"Group discount reached {worst['D%']:.1f}% vs {LAB_BENCH}% benchmark",
                            impact=fmt_inr(max(0, (worst["D%"] - LAB_BENCH) / 100 * worst["L"])),
                            recommendation="Implement monthly discount monitoring; set location-level caps",
                            owner="Group Service Head",
                            priority="High"
                        )
                    else:
                        st.success(f"✅ Labour discount within {LAB_BENCH}% benchmark across all months")

                    # Parts discount check
                    pts_trend = monthly_summary(audit_df, as_index=False).agg(
                        P=("Pre-GST Parts", "sum"), PD=("Parts Discount", "sum")
                    ).sort_values("Month_Sort")
                    pts_trend["D%"] = calc_ratio(pts_trend["PD"], pts_trend["P"], multiplier=100, fill_value=0)
                    pts_over = pts_trend[pts_trend["D%"] > PARTS_BENCH]
                    if not pts_over.empty:
                        worst_p = pts_over.loc[pts_over["D%"].idxmax()]
                        _render_finding(
                            finding=f"Parts Discount Exceeded Benchmark — {worst_p['Month Name']}",
                            cause=f"Parts discount at {worst_p['D%']:.1f}% vs {PARTS_BENCH}% benchmark",
                            impact=fmt_inr(max(0, (worst_p["D%"] - PARTS_BENCH) / 100 * worst_p["P"])),
                            recommendation="Review parts pricing authority; enforce parts discount policy",
                            owner="Parts Manager",
                            priority="Medium"
                        )

                    st.markdown("**Advisor Discount Register — Sorted by Discount %**")
                    if not adv_agg.empty:
                        adr = adv_agg.sort_values("Disc_Pct", ascending=False)
                        searchable_table(pd.DataFrame({
                            "Advisor":   adr[ADV_COL],
                            "Location":  adr["Location Name"],
                            "JCs":       adr["JCs"].apply(fmt_num),
                            "Disc %":    adr["Disc_Pct"].apply(lambda x: f"{x:.1f}%"),
                            "Disc ₹":    adr["DiscRs"].apply(fmt_inr),
                            "Leakage ₹": adr["Leakage"].apply(fmt_inr),
                            "":          adr["Disc_Pct"].apply(_sev_badge),
                        }), key="ia_disc_register", height="350px")
                else:
                    st.info("No discount data available")

            # ── Section 4: Advisor Audit ─────────────────────────────
            with st.expander("🎯 Advisor Audit — Risk Ranking", expanded=False):
                if not adv_agg.empty:
                    top_risk = adv_agg[adv_agg["Leakage"] > 0].head(5)
                    if not top_risk.empty:
                        for i, (_, row) in enumerate(top_risk.iterrows()):
                            _render_finding(
                                finding=f"#{i+1} High-Risk Advisor — {row[ADV_COL]}",
                                cause=f"Discount at {row['Disc_Pct']:.1f}%; {fmt_num(row['JCs'])} JCs at {row['Location Name']}",
                                impact=fmt_inr(row["Leakage"]),
                                recommendation="Review job card approvals; conduct advisor counselling and retrain on discount policy",
                                owner=f"Location Manager — {row['Location Name']}",
                                priority="Critical" if row["Disc_Pct"] > HIGH_DISC_ALERT else ("High" if row["Disc_Pct"] > DISC_CONCERN_PCT else "Medium")
                            )
                    else:
                        st.success("✅ No advisors generating leakage above benchmark")

                    st.markdown("**Full Advisor Risk Register**")
                    searchable_table(pd.DataFrame({
                        "Advisor":    adv_agg[ADV_COL],
                        "Location":   adv_agg["Location Name"],
                        "JCs":        adv_agg["JCs"].apply(fmt_num),
                        "Disc %":     adv_agg["Disc_Pct"].apply(lambda x: f"{x:.1f}%"),
                        "Avg Lab/JC": adv_agg["AvgLabJC"].apply(fmt_inr),
                        "Leakage ₹":  adv_agg["Leakage"].apply(fmt_inr),
                        "":           adv_agg["Disc_Pct"].apply(_sev_badge),
                    }), key="ia_risk_register", height="350px")

                    st.markdown("**Advisor Monthly Drilldown**")
                    all_advs_ia = sorted(audit_df[ADV_COL].dropna().unique().tolist())
                    sel_adv_ia  = st.selectbox("Select Advisor", ["— Select —"] + all_advs_ia, key="ia_adv_drilldown")
                    if sel_adv_ia != "— Select —":
                        adv_m = filter_valid_advisors(audit_df[audit_df[ADV_COL] == sel_adv_ia], ADV_COL).groupby(
                            ["Month_Sort", "Month Name"], dropna=False
                        ).agg(JCs=("JC_Nos.","sum"), Rev=("Pre-GST Labour","sum"),
                              Disc=("Labour Discount","sum"), Net=("Net_Labour","sum")).reset_index()
                        adv_m = adv_m[adv_m["Rev"] > 0].copy()
                        if not adv_m.empty:
                            adv_m["Disc %"]  = calc_ratio(adv_m["Disc"], adv_m["Rev"], multiplier=100, fill_value=0)
                            adv_m["Leakage"] = np.maximum(0, (adv_m["Disc %"] - LAB_BENCH) / 100 * adv_m["Rev"])
                            adv_m = adv_m.sort_values("Month_Sort")
                            html_table(pd.DataFrame({
                                "Month":    adv_m["Month Name"],
                                "JCs":      adv_m["JCs"].apply(fmt_num),
                                "Revenue":  adv_m["Rev"].apply(fmt_inr),
                                "Disc %":   adv_m["Disc %"].apply(lambda x: f"{x:.1f}%"),
                                "Net Lab":  adv_m["Net"].apply(fmt_inr),
                                "Leakage":  adv_m["Leakage"].apply(fmt_inr),
                            }), height="250px")
                else:
                    st.info("No advisor data available")

            # ── Section 5: Exception Audit ───────────────────────────
            with st.expander("⚠️ Exception Audit — Anomaly Detection", expanded=False):
                total_exceptions = 0

                st.markdown(f"**🔴 Exception 1 — Labour Discount > {HIGH_DISC_ALERT}%**")
                exc1 = adv_agg[adv_agg["Disc_Pct"] > HIGH_DISC_ALERT] if not adv_agg.empty else pd.DataFrame()
                if not exc1.empty:
                    total_exceptions += len(exc1)
                    for _, row in exc1.sort_values("Disc_Pct", ascending=False).head(5).iterrows():
                        _render_finding(
                            finding=f"Extreme Discount — {row[ADV_COL]} ({row['Location Name']})",
                            cause=f"Labour discount at {row['Disc_Pct']:.1f}% — far above {LAB_BENCH}% benchmark",
                            impact=fmt_inr(row["Leakage"]),
                            recommendation="Immediate review of all job cards; escalate for possible unauthorised discounting",
                            owner=f"Location Manager — {row['Location Name']}",
                            priority="Critical"
                        )
                else:
                    st.success(f"✅ No advisors with discount > {HIGH_DISC_ALERT}%")

                st.markdown("**🔴 Exception 2 — Negative Net Labour**")
                neg_lab = filter_valid_advisors(audit_df, ADV_COL).groupby(["Location Name", ADV_COL], dropna=False).agg(
                    NetLab=("Net_Labour", "sum"), JCs=("JC_Nos.", "sum")
                ).reset_index()
                neg_lab = neg_lab[neg_lab["NetLab"] < 0]
                if not neg_lab.empty:
                    total_exceptions += len(neg_lab)
                    for _, row in neg_lab.sort_values("NetLab").head(3).iterrows():
                        _render_finding(
                            finding=f"Negative Labour — {row[ADV_COL]} at {row['Location Name']}",
                            cause=f"Net Labour = {fmt_inr(row['NetLab'])} — credits/reversals exceed billings",
                            impact=fmt_inr(abs(row["NetLab"])),
                            recommendation="Verify job card reversals; check for credit note misuse",
                            owner="Accounts / Location Manager",
                            priority="Critical"
                        )
                else:
                    st.success("✅ No negative labour entries detected")

                st.markdown("**🟡 Exception 3 — Zero Labour with Active JCs**")
                zero_lab = filter_valid_advisors(audit_df, ADV_COL).groupby(["Location Name", ADV_COL], dropna=False).agg(
                    NetLab=("Net_Labour", "sum"), JCs=("JC_Nos.", "sum")
                ).reset_index()
                zero_lab = zero_lab[(zero_lab["NetLab"] == 0) & (zero_lab["JCs"] > 0)]
                if not zero_lab.empty:
                    total_exceptions += len(zero_lab)
                    for _, row in zero_lab.sort_values("JCs", ascending=False).head(3).iterrows():
                        _render_finding(
                            finding=f"Zero Labour — {row[ADV_COL]} ({fmt_num(row['JCs'])} JCs)",
                            cause=f"Net Labour = ₹0 on {fmt_num(row['JCs'])} JCs at {row['Location Name']}",
                            impact="Revenue leakage risk — amount undetermined",
                            recommendation="Audit all zero-labour JCs for billing completeness; check DMS entry",
                            owner="Location Manager",
                            priority="High"
                        )
                else:
                    st.success("✅ No zero-labour JC anomalies detected")

                st.markdown("**🟡 Exception 4 — Abnormal Labour/JC (Statistical Outlier)**")
                loc_stat = location_summary(audit_df, as_index=True).agg(
                    JCs=("JC_Nos.", "sum"), Net=("Net_Labour", "sum")
                ).reset_index()
                loc_stat = loc_stat[loc_stat["JCs"] > 0].copy()
                if not loc_stat.empty:
                    loc_stat["AvgJC"] = loc_stat["Net"] / loc_stat["JCs"]
                    mu  = loc_stat["AvgJC"].mean()
                    sig = loc_stat["AvgJC"].std()
                    if sig > 0:
                        outliers = loc_stat[(loc_stat["AvgJC"] > mu + 2 * sig) | (loc_stat["AvgJC"] < mu - 2 * sig)]
                        if not outliers.empty:
                            total_exceptions += len(outliers)
                            for _, row in outliers.iterrows():
                                direction = "HIGH" if row["AvgJC"] > mu + 2 * sig else "LOW"
                                _render_finding(
                                    finding=f"Abnormal Labour/JC ({direction}) — {row['Location Name']}",
                                    cause=f"Avg ₹{row['AvgJC']:,.0f}/JC vs group mean ₹{mu:,.0f} ± ₹{sig:,.0f}",
                                    impact="Billing anomaly or service mix issue",
                                    recommendation="Audit job card mix; verify service type classification in DMS",
                                    owner="Location Manager",
                                    priority="Medium"
                                )
                        else:
                            st.success("✅ No statistical outliers in Labour/JC")
                    else:
                        st.info("Insufficient variance to detect outliers")

                st.markdown("**🟡 Exception 5 — High Discount + Low Revenue**")
                if not adv_agg.empty:
                    rev_median = adv_agg["Revenue"].median()
                    exc5 = adv_agg[(adv_agg["Disc_Pct"] > DISC_CONCERN_PCT) & (adv_agg["Revenue"] < rev_median)]
                    if not exc5.empty:
                        total_exceptions += len(exc5)
                        for _, row in exc5.sort_values("Disc_Pct", ascending=False).head(3).iterrows():
                            _render_finding(
                                finding=f"High Discount + Low Revenue — {row[ADV_COL]}",
                                cause=f"{row['Disc_Pct']:.1f}% discount on {fmt_inr(row['Revenue'])} revenue at {row['Location Name']}",
                                impact=fmt_inr(row["Leakage"]),
                                recommendation="Review advisor performance; check for selective discounting on small-value jobs",
                                owner=f"Location Manager — {row['Location Name']}",
                                priority="High"
                            )
                    else:
                        st.success("✅ No high-discount + low-revenue combination detected")

                st.markdown("---")
                if total_exceptions == 0:
                    st.success("🏆 Zero exceptions across all audit buckets — clean period")
                else:
                    st.warning(f"⚠️ {total_exceptions} total exception(s) detected — see findings above")

            # ── Export ───────────────────────────────────────────
            period_label = ", ".join(sorted(audit_df["Month Name"].dropna().unique().tolist())) if not audit_df.empty else ""
            _export_meta = ExportMeta(
                report_title="Internal Audit",
                location="Filtered",
                date_range=period_label,
            )
            render_export_buttons(
                adv_agg if not adv_agg.empty else audit_df,
                _export_meta,
                formats=["csv", "excel"],
                key_prefix="ia_exception",
                label="Export Audit Data",
            )

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

    # LABOUR COMPLIANCE & LEAKAGE TAB
    with ia_tabs[1]:
        import streamlit.components.v1 as components
        import revenue_leakage_v31

        with st.spinner("Calculating missed labour..."):
            try:
                import app
                report_data = app.get_cached_audit_data()
                miss_df_raw = report_data["missed"]

                # Internal Audit now inherits Month, Location, Advisor, and Service filters from the Global/Module level.

                # ── Advanced filters — collapsed by default; methodology hidden here ──
                with st.expander("⚙️ Advanced Filters", expanded=False):
                    mod_opts = sorted(miss_df_raw['Model'].dropna().unique()) if 'Model' in miss_df_raw.columns else []
                    sel_mods = st.multiselect("Model", options=mod_opts)
                    st.caption("ℹ️ Revenue loss is calculated using average billed labour for the same model and service at the same location and month.")

                # ── Apply Advanced & Global Filters ──
                miss_df = miss_df_raw.copy()
                
                # Apply Global/Module Filters
                if st.session_state.get('filter_model_group'):
                    miss_df = miss_df[miss_df['Location'].apply(lambda x: app.classify_location(x, client_config) if x else None).isin(st.session_state['filter_model_group'])]
                if st.session_state.get('filter_location'):
                    miss_df = miss_df[miss_df['Location'].isin(st.session_state['filter_location'])]
                if st.session_state.get('filter_advisor'):
                    miss_df = miss_df[miss_df['Advisor Name'].isin(st.session_state['filter_advisor'])]
                if st.session_state.get('filter_svc_type') and 'Service Type' in miss_df.columns:
                    miss_df = miss_df[miss_df['Service Type'].isin(st.session_state['filter_svc_type'])]
                if st.session_state.get('selected_months_custom'):
                    miss_df = miss_df[miss_df['_month'].astype(str).isin(st.session_state['selected_months_custom'])]

                if sel_mods and 'Model' in miss_df.columns:
                    miss_df = miss_df[miss_df['Model'].isin(sel_mods)]

                if miss_df.empty:
                    st.warning("No missed labour data available for the selected filters.")
                else:
                    # ── Penetration tables ──
                    pms_pen = report_data.get("pms_pen", pd.DataFrame())
                    fr2_pen = report_data.get("fr2_pen", pd.DataFrame())
                    fr3_pen = report_data.get("fr3_pen", pd.DataFrame())
                    if sel_locs:
                        pms_pen = pms_pen[pms_pen["Location"].isin(sel_locs)] if not pms_pen.empty else pms_pen
                        fr2_pen = fr2_pen[fr2_pen["Location"].isin(sel_locs)] if not fr2_pen.empty else fr2_pen
                        fr3_pen = fr3_pen[fr3_pen["Location"].isin(sel_locs)] if not fr3_pen.empty else fr3_pen
                    if sel_advs:
                        pms_pen = pms_pen[pms_pen["Advisor Name"].isin(sel_advs)] if not pms_pen.empty else pms_pen
                        fr2_pen = fr2_pen[fr2_pen["Advisor Name"].isin(sel_advs)] if not fr2_pen.empty else fr2_pen
                        fr3_pen = fr3_pen[fr3_pen["Advisor Name"].isin(sel_advs)] if not fr3_pen.empty else fr3_pen

                    _month_lbl = ", ".join(sorted(sel_months)) if sel_months else "All Periods"

                    # ── V3.1 Executive Dashboard ──
                    v2_html = revenue_leakage_v31.build_revenue_leakage_dashboard_v2(
                        miss_df      = miss_df,
                        pms_pen      = pms_pen,
                        fr2_pen      = fr2_pen,
                        fr3_pen      = fr3_pen,
                        month_label  = _month_lbl,
                        last_sync    = "",
                        recovery_rate= 0.70,
                    )
                    components.html(v2_html, height=2600, scrolling=True)

            except Exception as e:
                st.error(f"Error generating Revenue Leakage dashboard: {e}")

    with ia_tabs[2]:
        import streamlit.components.v1 as components
        import internal_audit_app
        try:
            import app
            data = app.get_cached_audit_data()
            
            # Build available months from audit data (Revenue Leakage pattern)
            all_months = set()
            for k in ["pms", "fr2", "fr3"]:
                df = data.get(k)
                if df is not None and not df.empty and "Bill Date" in df.columns:
                    df['_month'] = pd.to_datetime(df["Bill Date"], errors="coerce").dt.to_period('M').astype(str)
                    months = df['_month'].dropna().unique()
                    all_months.update(months)
            
            all_months = sorted([str(m) for m in all_months], reverse=True)
            default_month = [all_months[0]] if all_months else []
            
            # Get selected month from localStorage or use default
            if "dealer_audit_period" not in st.session_state:
                st.session_state["dealer_audit_period"] = default_month[0] if default_month else None
            
            # Check for localStorage update from HTML selector
            if st.query_params.get("period"):
                st.session_state["dealer_audit_period"] = st.query_params.get("period")
                st.query_params.clear()
            
            selected_month = st.session_state["dealer_audit_period"]
            
            # Create filtered copy and apply month filter
            filtered = {k: v.copy() for k, v in data.items()}
            for k in ["pms", "fr2", "fr3"]:
                df = filtered.get(k)
                if df is not None and not df.empty and "Bill Date" in df.columns:
                    df['_month'] = pd.to_datetime(df["Bill Date"], errors="coerce").dt.to_period('M').astype(str)
                    if selected_month:
                        filtered[k] = df[df['_month'].astype(str).isin([selected_month])].copy()
            
            # Regenerate penetration tables from filtered data (reuse calc_penetration from load_data)
            filtered["pms_pen"] = internal_audit_app.calc_penetration(filtered["pms"], ["PMS", "WA", "WB", "DC", "EVAP", "AC"]) if not filtered["pms"].empty else pd.DataFrame()
            filtered["fr2_pen"] = internal_audit_app.calc_penetration(filtered["fr2"], ["WA", "WB"]) if not filtered["fr2"].empty else pd.DataFrame()
            filtered["fr3_pen"] = internal_audit_app.calc_penetration(filtered["fr3"], ["WA", "WB"]) if not filtered["fr3"].empty else pd.DataFrame()
            
            month = internal_audit_app.get_month(filtered)
            @st.cache_data(ttl=3600, show_spinner=False)
            def generate_audit_html(_audit_data, current_month):
                # Using _audit_data prevents slow hashing of the massive DataFrame dictionary
                contacts, loc_map, wc_map, sort_map = internal_audit_app.load_contacts()
                locations = internal_audit_app.all_locs(
                    _audit_data,
                    sort_map=sort_map
                )
                return internal_audit_app.build_master_report(
                    locations,
                    loc_map,
                    current_month,
                    _audit_data,
                    wc_map=wc_map,
                    available_months=all_months
                )
                
            html_report = generate_audit_html(filtered, month)
            
            components.html(
                html_report,
                height=1400,
                scrolling=True
            )
        except Exception as e:
            st.error(f"Dealer Audit Error: {e}")
