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
    get_jobcard_count, get_fsc_income, get_otc_income, get_vor_charges, get_dealer_foc,
    get_internal_consumption
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
    apply_service_type_filter, apply_advisor_filter, apply_mp_pb_filter, split_cp_pp
)
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num
from utils.constants import ADV_COL, MP_COLORS, PLY, C

# Import shared UI helpers from app
from ui.kpi_cards import kpi
from ui.tables import html_table
from ui.traffic import yoy_badge, traffic_light, tgt_badge
from ui.helpers import apply_chart, clean_hover, _render_finding
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num

def render(df, pairs, comparison_mode=True, selected_months=None):
    # ── [DEBUG] Stage 3: render() entry ───────────────────────────────────────
    from services.logger import logger as _log
    _log.debug(f"[RENDER] margin.render: entered | df.shape={df.shape} | pairs={len(pairs)} | df.empty={df.empty}")
    st.caption(f"[DEBUG] margin.render: entered · df.shape={df.shape} · pairs={len(pairs)}")
    # ─────────────────────────────────────────────────────────────────────────
    if df.empty:
        st.caption("[DEBUG] margin.render: early return — df is empty")
        return
    st.caption("[DEBUG] margin.render: past empty guard")
    # df is already filtered by selected_months at main level, use it directly for current period
    cp = df.copy()
    
    kpis = ["Total Margin", "Net Labour", "Parts_Margin", "Oil_Margin", "OTC Income", "FSC Income"]
    c = st.columns(6)
    for i, k in enumerate(kpis):
        v = cp[k].sum() if k != "Net Labour" else (get_labour_sales(cp) - calculate_labour_discount(cp))
        with c[i]: kpi(k.replace("_", " "), fmt_inr(v))
    
    # Waterfall chart
    st.markdown('<div class="section-card"><div class="section-title">💰 Margin Waterfall</div>', unsafe_allow_html=True)
    gross_lab = get_labour_sales(cp)
    lab_disc = -calculate_labour_discount(cp)
    net_lab = gross_lab + lab_disc
    parts_margin = calculate_parts_margin(cp)
    oil_margin = cp["Oil_Margin"].sum()
    battery_margin = cp["Battery_Margin"].sum()
    tyre_margin = cp["Tyre_Margin"].sum()
    other_margin = cp["Other_Margin"].sum()
    fsc_income = get_fsc_income(cp)
    otc_income = get_otc_income(cp)
    vor_charges = -get_vor_charges(cp)
    dealer_foc = -get_dealer_foc(cp)
    internal_cons = -get_internal_consumption(cp)
    total_margin = calculate_total_margin(cp)
    
    labels = ["Gross Labour", "Labour Disc", "Net Labour", "Parts Margin", "Oil Margin", 
              "Battery+Tyre+Other", "FSC Income", "OTC Income", "VOR Charges", "Dealer FOC", 
              "Internal Cons", "Total Margin"]
    values = [gross_lab, lab_disc, net_lab, parts_margin, oil_margin, 
              battery_margin + tyre_margin + other_margin, fsc_income, otc_income, 
              vor_charges, dealer_foc, internal_cons, total_margin]
    
    fig = go.Figure(go.Waterfall(
        name="Margin Flow",
        orientation="v",
        measure=["relative"] * 11 + ["total"],
        x=labels,
        y=values,
        textposition="outside",
        text=[fmt_inr(v) for v in values],
        connector={"line":{"color":"rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        **PLY,
        height=400,
        xaxis_title="",
        yaxis_title="Amount (₹)",
        showlegend=False
    )
    st.plotly_chart(fig, width='stretch', key="ma_waterfall",
                    config={"displayModeBar": True, "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d","lasso2d"],
                            "toImageButtonOptions": {"format":"png","scale":2}})
    st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('<div class="section-card"><div class="section-title">💰 Category × Month Margin Matrix</div>', unsafe_allow_html=True)
    cats = ["Parts_Margin", "Accessory_Margin", "Oil_Margin", "Tyre_Margin", "Battery_Margin", "Other_Margin", "VOR Charges",
            "Total Parts Margin", "Net Labour", "OTC Income", "MSIL Labour Claim", "FSC Income", "Dealer FOC", "Internal Consumption", "Total Margin"]
    
    mo = cp.drop_duplicates("Month Name").sort_values("Month_Sort")["Month Name"].tolist()
    m_data = cp.groupby(["Month Name", "Month_Sort"], dropna=False).sum(numeric_only=True).reset_index().sort_values("Month_Sort")
    m_data["Total Parts Margin"] = m_data[["Parts_Margin", "Accessory_Margin", "Oil_Margin", "Tyre_Margin", "Battery_Margin", "Other_Margin", "VOR Charges"]].sum(axis=1)
    m_data["Total Margin"] = m_data["Total Margin"]
    
    rows = []
    prev_tm = 0
    for cat in cats:
        r = {"Category": f"<b>{cat}</b>" if "Total" in cat else cat}
        ct = 0
        for m in mo:
            lookup_cat = "Net_Labour" if cat == "Net Labour" else cat
            v = m_data[m_data["Month Name"]==m][lookup_cat].sum() if not m_data[m_data["Month Name"]==m].empty else 0
            r[m] = fmt_inr(v)
            if "Total" not in cat and v < 0: r[m] = f'<span class="cell-neg">{r[m]}</span>'
            ct += v
        r["Total CP"] = fmt_inr(ct)
        rows.append(r)
        
    # MoM
    r = {"Category": "<i>MoM Growth %</i>"}
    for m in mo:
        v = m_data[m_data["Month Name"]==m]["Total Margin"].sum() if not m_data[m_data["Month Name"]==m].empty else 0
        if prev_tm > 0: r[m] = fmt_pct((v-prev_tm)/prev_tm*100, True)
        else: r[m] = "—"
        prev_tm = v
    r["Total CP"] = "—"
    rows.append(r)
    
    html_table(pd.DataFrame(rows), height="600px")
    st.markdown('</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-card"><div class="section-title">📈 Total Margin Trend</div>', unsafe_allow_html=True)
        fig = px.area(m_data, x="Month Name", y="Total Margin", markers=True, color_discrete_sequence=[C["primary"]])
        fig.update_layout(**PLY); fig.update_layout(height=320, xaxis_title="", yaxis_title="Total Margin (₹)")
        st.plotly_chart(fig, width='stretch', key="ma_tr",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-card"><div class="section-title">🍰 Margin Mix</div>', unsafe_allow_html=True)
        md = m_data[["Parts_Margin", "Oil_Margin", "Net_Labour", "OTC Income", "FSC Income"]].sum().reset_index()
        md.columns = ["Cat", "Val"]
        md.loc[md["Cat"] == "Net_Labour", "Cat"] = "Net Labour"
        md = md[md["Val"] > 0]
        fig = px.pie(md, values="Val", names="Cat", hole=0.5, color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(**PLY); fig.update_layout(height=320, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, width='stretch', key="ma_mix",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
        
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-card"><div class="section-title">🏢 Location Margin</div>', unsafe_allow_html=True)
        lm = location_summary(cp, as_index=False)["Total Margin"].sum().sort_values("Total Margin", ascending=True)
        fig = px.bar(lm, x="Total Margin", y="Location Name", orientation="h", color_discrete_sequence=[C["green"]])
        fig.update_layout(**PLY); fig.update_layout(height=320, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, width='stretch', key="ma_loc",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-card"><div class="section-title">⚖️ WS vs BS Margin</div>', unsafe_allow_html=True)
        wbs = cp.groupby(["Month_Sort", "Month Name", "MP_PB"], as_index=False, dropna=False)["Total Margin"].sum().sort_values("Month_Sort")
        fig = px.bar(wbs, x="Month Name", y="Total Margin", color="MP_PB", color_discrete_map=MP_COLORS)
        fig.update_layout(**PLY); fig.update_layout(height=320, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, width='stretch', key="ma_wsbs",
                        config={"displayModeBar": True, "displaylogo": False,
                                "modeBarButtonsToRemove": ["select2d","lasso2d"],
                                "toImageButtonOptions": {"format":"png","scale":2}})
        st.markdown('</div>', unsafe_allow_html=True)
