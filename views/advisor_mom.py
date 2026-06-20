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
from utils.constants import ADV_COL, MP_COLORS, C

# Import new Phase B UI Components
from ui.components import MetricCard, ChartCard, TableCard
from ui.helpers import apply_chart, clean_hover
from ui.design_tokens import T

def render(df, pairs, comparison_mode=True, selected_months=None):
    if df.empty:
        from ui.components.core import EmptyState
        EmptyState('No data available for the selected period. Adjust your filters or check data freshness.')
        return
    pp_months = [p[1] for p in pairs]
    # df is already filtered by selected_months at main level, use it directly for current period
    cp = df.copy()
    pp = apply_month_filter(df, "Month Name", pp_months)
    if cp.empty:
        st.warning("No data for the selected period. Please adjust the month picker.")
        return

    

    # 3.1 — Header controls row
    adv_jcs = advisor_summary(cp, adv_col=ADV_COL, as_index=True)["JC_Nos."].sum()
    valid_advisors = sorted(adv_jcs[adv_jcs >= 5].index.tolist())
    valid_advisors = [a for a in valid_advisors if a != "Unassigned"]

    if not valid_advisors:
        st.warning("No advisors with 5+ JCs in the selected period.")
        return

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        metric = st.radio("Metric", ["Net Labour", "Net Parts", "Discount%", "Oil Qty"], horizontal=True, key="mom_metric")

    selected_advs = st.session_state.get("filter_advisor", [])
    if len(selected_advs) != 1:
        st.info("Please select exactly **one Advisor** from the Page Filters above to view the Advisor MoM report.")
        return
        
    sel_adv = selected_advs[0]
    adv_data = cp[(cp[ADV_COL] == sel_adv)]
    all_adv_data = cp

    metric_col = {"Net Labour": "Net_Labour", "Net Parts": "Net_Parts", "Oil Qty": "Oil_Sale_Qty"}.get(metric, "Net_Labour")

    # 3.2 — KPI cards row (5 cards)
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px"></div>', unsafe_allow_html=True)

    adv_monthly = monthly_summary(adv_data, as_index=False)[metric_col].sum().sort_values("Month_Sort")
    if not adv_monthly.empty:
        latest_val = adv_monthly[metric_col].iloc[-1]
        prior_val = adv_monthly[metric_col].iloc[-2] if len(adv_monthly) > 1 else 0
        mom_delta = latest_val - prior_val if len(adv_monthly) > 1 else 0

        fmt_fn = fmt_inr if metric in ["Net Labour", "Net Parts"] else fmt_num
        this_month_name = adv_monthly["Month Name"].iloc[-1] if not adv_monthly.empty else "N/A"
        last_month_name = adv_monthly["Month Name"].iloc[-2] if len(adv_monthly) > 1 else "N/A"
        _3m_avg = adv_monthly[metric_col].tail(3).mean() if len(adv_monthly) >= 3 else adv_monthly[metric_col].mean()
        
        loc_monthly = monthly_summary(all_adv_data, as_index=False)[metric_col].sum().sort_values("Month_Sort")
        n_advs = all_adv_data[ADV_COL].nunique()
        loc_avg = loc_monthly[metric_col].mean() / max(n_advs, 1) if not loc_monthly.empty else 0
        
        # Determine Rank
        # For ranking we compare the overall sum of the metric in CP
        adv_totals = cp.groupby(ADV_COL, dropna=False)[metric_col].sum().sort_values(ascending=False)
        rank = adv_totals.index.get_loc(sel_adv) + 1 if sel_adv in adv_totals.index else "N/A"

        KPIGrid([
            {"label": f"This Month ({this_month_name})", "value": fmt_fn(latest_val), "cp": latest_val, "pp": prior_val, "invert_trend": (metric == "Discount%")},
            {"label": f"Last Month ({last_month_name})", "value": fmt_fn(prior_val)},
            {"label": "3M Avg", "value": fmt_fn(_3m_avg)},
            {"label": "Location Avg", "value": fmt_fn(loc_avg)},
            {"label": "Rank", "value": f"#{rank}"}
        ])

    # 3.3 — MoM sparkline (6-month rolling)
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px"></div>', unsafe_allow_html=True)
    last_6 = adv_monthly.tail(6) if len(adv_monthly) >= 6 else adv_monthly
    if not last_6.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=last_6["Month Name"], y=last_6[metric_col], mode='lines+markers', name=sel_adv, line=dict(color=C["primary"])))
        loc_6 = monthly_summary(all_adv_data, as_index=False)[metric_col].sum().sort_values("Month_Sort")
        loc_6 = loc_6[loc_6["Month Name"].isin(last_6["Month Name"].tolist())]
        n_adv = all_adv_data[ADV_COL].nunique()
        if not loc_6.empty and n_adv > 0:
            loc_6["Avg"] = loc_6[metric_col] / n_adv
            fig.add_trace(go.Scatter(x=loc_6["Month Name"], y=loc_6["Avg"], mode='lines', name="Location Avg", line=dict(color=C["gray"], dash='dash')))
        ChartCard(f"📈 {sel_adv} — {metric} Trend (Last 6M)", fig, height=350)

    # 3.4 — Multi-metric radar/spider chart
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px"></div>', unsafe_allow_html=True)
    radar_metrics = {
        "JC Volume": "JC_Nos.",
        "Labour/JC": "Net_Labour",
        "Parts/JC": "Net_Parts",
        "Oil/JC": "Oil_Sale_Qty",
        "Acc/JC": "Accessory_Sale",
        "Disc% (inv)": "Labour_Disc_Pct"
    }
    adv_radar = advisor_summary(adv_data, adv_col=ADV_COL, as_index=True).agg({m: "sum" for m in set(radar_metrics.values()) & set(adv_data.columns)}).reset_index()
    if not adv_radar.empty:
        adv_radar["Labour/JC"] = np.where(adv_radar["JC_Nos."] > 0, adv_radar["Net_Labour"] / adv_radar["JC_Nos."], 0)
        adv_radar["Parts/JC"] = np.where(adv_radar["JC_Nos."] > 0, adv_radar["Net_Parts"] / adv_radar["JC_Nos."], 0)
        adv_radar["Oil/JC"] = np.where(adv_radar["JC_Nos."] > 0, adv_radar.get("Oil_Sale_Qty", pd.Series([0])).iloc[0] / adv_radar["JC_Nos."], 0)
        adv_radar["Acc/JC"] = np.where(adv_radar["JC_Nos."] > 0, adv_radar.get("Accessory_Sale", pd.Series([0])).iloc[0] / adv_radar["JC_Nos."], 0)

        loc_radar = advisor_summary(all_adv_data, adv_col=ADV_COL, as_index=True).agg({m: "sum" for m in set(radar_metrics.values()) & set(all_adv_data.columns)}).reset_index()
        loc_radar["Labour/JC"] = np.where(loc_radar["JC_Nos."] > 0, loc_radar["Net_Labour"] / loc_radar["JC_Nos."], 0)
        loc_radar["Parts/JC"] = np.where(loc_radar["JC_Nos."] > 0, loc_radar["Net_Parts"] / loc_radar["JC_Nos."], 0)
        loc_radar["Oil/JC"] = np.where(loc_radar["JC_Nos."] > 0, loc_radar.get("Oil_Sale_Qty", pd.Series([0])).iloc[0] / loc_radar["JC_Nos."], 0)
        loc_radar["Acc/JC"] = np.where(loc_radar["JC_Nos."] > 0, loc_radar.get("Accessory_Sale", pd.Series([0])).iloc[0] / loc_radar["JC_Nos."], 0)
        loc_avg_radar = loc_radar.mean(numeric_only=True)

        radar_vals = []
        loc_vals = []
        for label, col in [("JC Volume", "JC_Nos."), ("Labour/JC", "Labour/JC"), ("Parts/JC", "Parts/JC"), ("Oil/JC", "Oil/JC"), ("Acc/JC", "Acc/JC")]:
            adv_v = adv_radar[col].iloc[0] if col in adv_radar.columns else 0
            loc_v = loc_avg_radar.get(col, 0)
            max_v = max(adv_v, loc_v, 1)
            radar_vals.append(min(adv_v / max_v * 100, 100))
            loc_vals.append(min(loc_v / max_v * 100, 100))

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=radar_vals + [radar_vals[0]], theta=["JC Vol", "Lab/JC", "Pts/JC", "Oil/JC", "Acc/JC", "JC Vol"], fill='toself', name=sel_adv, line_color=C["primary"]))
        fig.add_trace(go.Scatterpolar(r=loc_vals + [loc_vals[0]], theta=["JC Vol", "Lab/JC", "Pts/JC", "Oil/JC", "Acc/JC", "JC Vol"], fill='toself', name="Location Avg", line_color=C["gray"]))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=400)
        ChartCard(f"🕸️ {sel_adv} Performance Profile", fig, height=400)

    # 3.5 — MoM delta table
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px"></div>', unsafe_allow_html=True)
    
    sel_locs = adv_data["Location Name"].unique().tolist()
    all_adv_monthly = filter_valid_advisors(cp[cp["Location Name"].isin(sel_locs)], ADV_COL).groupby([ADV_COL, "Month_Sort", "Month Name"], as_index=False, dropna=False).agg(
        JCs=("JC_Nos.","sum"), NL=("Net_Labour","sum"), DL=("Labour Discount","sum"), PL=("Pre-GST Labour","sum")
    ).sort_values([ADV_COL, "Month_Sort"])
    all_adv_monthly["Disc%"] = calc_ratio(all_adv_monthly["DL"], all_adv_monthly["PL"], multiplier=100, fill_value=0)
    all_adv_monthly["JC_MoM"] = advisor_summary(all_adv_monthly, adv_col=ADV_COL, as_index=True)["JCs"].diff()
    all_adv_monthly["Lab_MoM"] = advisor_summary(all_adv_monthly, adv_col=ADV_COL, as_index=True)["NL"].diff()

    latest_month = all_adv_monthly["Month Name"].iloc[-1] if not all_adv_monthly.empty else None
    if latest_month:
        latest = all_adv_monthly[all_adv_monthly["Month Name"] == latest_month]
        prev = all_adv_monthly[all_adv_monthly["Month Name"] == all_adv_monthly["Month Name"].unique()[-2]] if len(all_adv_monthly["Month Name"].unique()) > 1 else pd.DataFrame()

        dt_rows = []
        for adv in latest[ADV_COL].unique():
            l_row = latest[latest[ADV_COL] == adv].iloc[0] if not latest[latest[ADV_COL] == adv].empty else None
            if l_row is not None:
                jc_mom = l_row["JC_MoM"] if not pd.isna(l_row["JC_MoM"]) else 0
                lab_mom = l_row["Lab_MoM"] if not pd.isna(l_row["Lab_MoM"]) else 0
                dt_rows.append({
                    "Advisor": adv,
                    "JCs": int(l_row["JCs"]),
                    "JC MoM": f"{jc_mom:+.0f}",
                    "Net Labour": fmt_inr(l_row["NL"]),
                    "Labour MoM": fmt_inr(lab_mom),
                    "Disc%": f"{l_row['Disc%']:.1f}%",
                })
        dt = pd.DataFrame(dt_rows).sort_values("JCs", ascending=False)
        TableCard(dt, height=300, index=False)

    # 3.6 — Rank movement heatmap
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px"></div>', unsafe_allow_html=True)
    if not all_adv_monthly.empty:
        month_ranks = []
        for m in all_adv_monthly["Month Name"].unique():
            m_data = all_adv_monthly[all_adv_monthly["Month Name"] == m].sort_values("JCs", ascending=False).reset_index(drop=True)
            m_data["Rank"] = range(1, len(m_data) + 1)
            month_ranks.append(m_data[[ADV_COL, "Month Name", "Rank"]])
        if month_ranks:
            ranks_df = pd.concat(month_ranks)
            rank_pivot = ranks_df.pivot(index=ADV_COL, columns="Month Name", values="Rank").fillna(0)
            fig = px.imshow(rank_pivot.values, x=rank_pivot.columns.tolist(), y=rank_pivot.index.tolist(), color_continuous_scale="RdYlGn_r", aspect="auto")
            ChartCard(f"🏅 Rank by JC Volume — {', '.join(sel_locs)}", fig, height=400)

    # 3.7 — Consistent underperformer flag
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px"></div>', unsafe_allow_html=True)
    def flag_underperformers(df_mom, metric_col, n_months=3):
        ups = []
        for adv in df_mom[ADV_COL].unique():
            adv_rows = df_mom[df_mom[ADV_COL] == adv].sort_values("Month_Sort")
            if len(adv_rows) >= n_months:
                for i in range(len(adv_rows) - n_months + 1):
                    window = adv_rows.iloc[i:i+n_months]
                    q25 = len(window) * 0.75
                    ranks = window[metric_col].rank(ascending=False)
                    if all(ranks > q25):
                        ups.append(adv)
                        break
        return list(set(ups))

    under = flag_underperformers(all_adv_monthly, "JCs", 3)
    if under:
        st.warning(f"⚠️ Consistent Underperformers (3+ months bottom quartile by JCs): {', '.join(under[:5])}{'...' if len(under) > 5 else ''}")
    else:
        st.success("✅ No consistent underperformers detected.")

    # 3.8 — Advisor coaching note
    st.markdown(f'<div style="margin-top:{T.SPACE_6}px"></div>', unsafe_allow_html=True)
    
    notes = []
    adv_disc = calc_ratio(calculate_labour_discount(adv_data), get_labour_sales(adv_data), multiplier=100, fill_value=0)
    adv_parts_jc = get_net_parts(adv_data) / get_jobcard_count(adv_data) if get_jobcard_count(adv_data) > 0 else 0
    loc_parts_jc = get_net_parts(all_adv_data) / get_jobcard_count(all_adv_data) if get_jobcard_count(all_adv_data) > 0 else 0
    adv_oil_jc = adv_data["Oil_Sale_Qty"].sum() / get_jobcard_count(adv_data) if get_jobcard_count(adv_data) > 0 else 0

    if adv_disc > 20:
        notes.append(f"Discount control needed: {adv_disc:.1f}% labour discount is above the 20% threshold.")
    if adv_parts_jc < loc_parts_jc * 0.8:
        notes.append(f"Parts upsell opportunity: Parts/JC is below location average. Focus on recommending genuine parts.")
    if adv_oil_jc < 1:
        notes.append(f"Oil penetration low: {adv_oil_jc:.1f} litres/JC. Target oil sale on every service visit.")

    if notes:
        note_text = "<br>".join(notes)
        st.markdown(f'<div style="background:var(--color-surface2);border-radius:{T.RADIUS_MD}px;padding:{T.SPACE_3}px;">{note_text}</div>', unsafe_allow_html=True)
        if st.button("📋 Copy Note", key="mom_copy_note"):
            st.write("Note copied to clipboard (simulated)")
    else:
        st.info("No specific coaching notes for this advisor.")
