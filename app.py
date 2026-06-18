"""
WSMIS — Workshop Management Information System
Multi-Client  ·  Multi-Location Maruti Dealership
Apple Light-Theme Dashboard  ·  v1.0.0-rc1
"""

import time
START_TIME = time.time()

import streamlit as st

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from io import BytesIO
from sklearn.linear_model import LinearRegression
import sys
import os
import importlib.util

# Explicit import to load correct internal_audit_app.py from WSMIS directory
spec = importlib.util.spec_from_file_location(
    "internal_audit_app",
    os.path.join(os.path.dirname(__file__), "internal_audit_app.py")
)
internal_audit_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(internal_audit_app)

@st.cache_data(ttl=3600)  # Extended TTL to 1 hour (was 300s/5min)
def get_cached_audit_data():
    return internal_audit_app.load_data()

# Removed get_cached_missed_labour entirely since load_data() already computes res["missed"]


# CONSTANTS & CONFIG
from utils.constants import (
    ADV_COL, CLIENTS, EXCLUDE_SERVICE_TYPES, ARENA_LOCATIONS,
    NEXA_LOCATIONS, BS_SERVICE_TYPES, MONTH_SORT_ORDER, FY_MONTHS, SERVICE_ACCOUNT
)
from config.settings import HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD

# PAGE CONFIG & CSS
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Auto LLP MIS v1.0.0-rc1", page_icon="🚗")

APPLE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif !important; }
.stApp { background-color: #F5F5F7 !important; }

.kpi-card {
    background: #FFFFFF; border: 1px solid #E5E5EA; border-radius: 16px;
    padding: 18px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.05); text-align: center; transition: box-shadow 0.2s ease; height: 100%;
}
.kpi-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.10); }
.kpi-label { font-size: 11px; font-weight: 600; color: #6E6E73; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.kpi-value { font-size: 24px; font-weight: 700; color: #1D1D1F; line-height: 1.2; }
.kpi-sub { font-size: 11px; color: #8E8E93; margin-top: 2px; }
.kpi-delta-pos { color: #34C759; font-size: 13px; font-weight: 700; margin-top: 4px; }
.kpi-delta-neg { color: #FF3B30; font-size: 13px; font-weight: 700; margin-top: 4px; }
.kpi-delta-new { color: #0071E3; font-size: 13px; font-weight: 700; margin-top: 4px; }
.kpi-meta { font-size: 10px; color: #8E8E93; margin-top: 3px; letter-spacing: 0.2px; }
.badge-pos { background:#E8F9EE; color:#1A7F37; padding:2px 10px; border-radius:12px; font-weight:600; font-size:12px; display:inline-block; }
.badge-neg { background:#FFEBE9; color:#CF222E; padding:2px 10px; border-radius:12px; font-weight:600; font-size:12px; display:inline-block; }
.badge-new { background:#E8F0FE; color:#0071E3; padding:2px 10px; border-radius:12px; font-weight:600; font-size:12px; display:inline-block; }
.badge-warn { background:#FFF3E0; color:#E65100; padding:2px 10px; border-radius:12px; font-weight:600; font-size:12px; display:inline-block; }
.badge-neutral { background:#F5F5F7; color:#6E6E73; padding:2px 10px; border-radius:12px; font-weight:600; font-size:12px; display:inline-block; }
.badge-ws { background:#E3F2FD; color:#0D47A1; padding:2px 8px; border-radius:8px; font-weight:600; font-size:11px; }
.badge-bs { background:#FFF3E0; color:#E65100; padding:2px 8px; border-radius:8px; font-weight:600; font-size:11px; }
.traffic-light { display: inline-block; font-size: 12px; line-height: 1; }
.section-card { background: #FFFFFF; border: 1px solid #E5E5EA; border-radius: 16px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.05); margin-bottom: 16px; }
.section-title { font-size: 16px; font-weight: 700; color: #1D1D1F; margin-bottom: 14px; }
.header-bar { background: #FFFFFF; border: 1px solid #E5E5EA; border-radius: 16px; padding: 16px 24px; box-shadow: 0 1px 4px rgba(0,0,0,.05); margin-bottom: 12px; }
.brand-title { font-size: 22px; font-weight: 800; color: #1D1D1F; letter-spacing: -0.3px; }
.brand-sub { font-size: 12px; color: #6E6E73; margin-top: 2px; }
.period-tag-pp { display: inline-block; background: #F5F5F7; color: #6E6E73; padding: 3px 12px; border-radius: 8px; font-size: 11px; font-weight: 600; margin-right: 6px; }
.styled-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; border-radius: 12px; overflow: hidden; border: 1px solid #E5E5EA; }
.styled-table thead th { background: #F5F5F7; color: #6E6E73; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; padding: 10px 12px; text-align: right; border-bottom: 1px solid #E5E5EA; position: sticky; top: 0; z-index: 1; white-space: nowrap; }
.styled-table thead th:first-child { text-align: left; }
.styled-table tbody td { padding: 8px 12px; border-bottom: 1px solid #F0F0F5; color: #1D1D1F; text-align: right; white-space: nowrap; }
.styled-table tbody td:first-child { text-align: left; font-weight: 500; }
.styled-table tbody tr:hover { background: #FAFAFE; }
.styled-table tbody tr:last-child td { border-bottom: none; }
.styled-table tbody tr.total-row td { font-weight: 700; background: #F5F5F7; border-top: 2px solid #E5E5EA; }
.cell-neg { color: #FF3B30; font-weight: 600; }
.insight-card { background: #FFFFFF; border: 1px solid #E5E5EA; border-radius: 14px; padding: 16px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.05); margin-bottom: 10px; border-left: 4px solid #0071E3; }
.insight-card.pos { border-left-color: #34C759; }
.insight-card.neg { border-left-color: #FF3B30; }
.insight-card.warn { border-left-color: #FF9500; }
.insight-title { font-size: 14px; font-weight: 700; color: #1D1D1F; margin-bottom: 3px; }
.insight-stat { font-size: 12px; color: #6E6E73; }
.stTabs [data-baseweb="tab-list"] { gap: 0; background: #FFFFFF; border-radius: 12px; padding: 4px; border: 1px solid #E5E5EA; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 16px; font-weight: 600; font-size: 13px; color: #6E6E73; }
.stTabs [aria-selected="true"] { background: #0071E3 !important; color: #FFFFFF !important; border-radius: 8px !important; }
.stDownloadButton > button { background: #FFFFFF !important; border: 1px solid #E5E5EA !important; color: #1D1D1F !important; border-radius: 10px !important; font-weight: 600 !important; }
.stDownloadButton > button:hover { border-color: #0071E3 !important; color: #0071E3 !important; }
.stMultiSelect [data-baseweb="tag"] { background: #0071E3 !important; border-radius: 8px !important; }
header[data-testid="stHeader"] { background: rgba(245,245,247,0.95) !important; }
footer { visibility: hidden; }
/* Switcher custom styles */
div[role="radiogroup"] { flex-wrap: nowrap; overflow-x: auto; gap: 0 !important; }
div[role="radiogroup"] > label > div:first-of-type { display: none !important; }
div[role="radiogroup"] > label { 
    padding: 6px 14px !important; background: #F5F5F7; border-radius: 20px; 
    border: 1px solid #E5E5EA; margin-right: 6px !important; margin-bottom: 0px !important; 
    cursor: pointer; white-space: nowrap; display: inline-flex; align-items: center; justify-content: center;
}
div[role="radiogroup"] > label[data-checked="true"], div[role="radiogroup"] > label:has(input:checked) { 
    background: #0071E3 !important; border-color: #0071E3 !important; box-shadow: 0 2px 8px rgba(0, 113, 227, 0.3);
}
div[role="radiogroup"] > label[data-checked="true"] p, div[role="radiogroup"] > label:has(input:checked) p { 
    color: white !important; font-weight: 600; 
}
/* Scorecard table cell coloring */
.score-green { background: #E8F9EE; color: #1A7F37; font-weight: 600; border-radius: 6px; padding: 2px 8px; }
.score-yellow { background: #FFF3E0; color: #E65100; font-weight: 600; border-radius: 6px; padding: 2px 8px; }
.score-red { background: #FFEBE9; color: #CF222E; font-weight: 600; border-radius: 6px; padding: 2px 8px; }
/* Insight cards */
.insight-card { background: #F5F5F7; border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #E5E5EA; }
.insight-card.pos { background: #E8F5E9; border-color: #C8E6C9; }
.insight-card.warn { background: #FFF3E0; border-color: #FFE0B2; }
.insight-title { font-size: 13px; font-weight: 600; color: #6E6E73; margin-bottom: 6px; }
.insight-stat { font-size: 14px; font-weight: 500; color: #1D1D1F; }
/* Location health cards */
.loc-card { background: #FFFFFF; border: 1px solid #E5E5EA; border-radius: 16px;
            padding: 16px 18px; margin-bottom: 12px; transition: box-shadow 0.2s; }
.loc-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); }
.loc-card-title { font-size: 16px; font-weight: 700; color: #1D1D1F; margin-bottom: 8px; }
.loc-metric { font-size: 12px; color: #6E6E73; }
.loc-metric-val { font-size: 14px; font-weight: 600; color: #1D1D1F; }
/* Forecast section */
.forecast-card { background: linear-gradient(135deg, #E8F0FE, #FFFFFF);
                 border: 1px solid #B5D4F4; border-radius: 16px; padding: 20px; }
.forecast-note { font-size: 11px; color: #8E8E93; font-style: italic; margin-top: 8px; }
/* Alert banner */
.alert-banner { background: #FFEBE9; border: 1px solid #FFCCCB; border-radius: 12px;
                padding: 12px 16px; margin-bottom: 12px; color: #CF222E; font-weight: 600; }
.info-banner { background: #E8F0FE; border: 1px solid #B5D4F4; border-radius: 12px;
               padding: 12px 16px; margin-bottom: 12px; color: #185FA5; font-weight: 600; }
/* Month picker preset buttons */
.preset-active { background: #0071E3 !important; color: white !important; }
/* Multiselect selection highlighting */
.stMultiSelect [data-baseweb="tag"] { background: #0071E3 !important; color: white !important; border-radius: 8px !important; }
/* Selectbox selection */
.stSelectbox > div > div > div[data-baseweb="select"] { border-color: #0071E3 !important; }
/* Expander highlighting */
details[open] > summary { color: #0071E3 !important; font-weight: 600; }
/* Tab selection */
.stTabs [data-baseweb="tab"][aria-selected="true"] { 
    background: #0071E3 !important; 
    color: white !important; 
    border-radius: 8px 8px 0 0;
}
/* ── Fullscreen: scale up all chart text ── */
:-webkit-full-screen .js-plotly-plot .gtitle { font-size: 18px !important; }
:-webkit-full-screen .js-plotly-plot .xtick text,
:-webkit-full-screen .js-plotly-plot .ytick text { font-size: 14px !important; }
:-webkit-full-screen .js-plotly-plot .legend text { font-size: 13px !important; }
:-webkit-full-screen .js-plotly-plot .bar text,
:-webkit-full-screen .js-plotly-plot .textpoint { font-size: 14px !important; font-weight: 700 !important; }
:fullscreen .js-plotly-plot .gtitle { font-size: 18px !important; }
:fullscreen .js-plotly-plot .xtick text,
:fullscreen .js-plotly-plot .ytick text { font-size: 14px !important; }
:fullscreen .js-plotly-plot .bar text { font-size: 14px !important; font-weight: 700 !important; }
/* ── Compact sticky header ── */
.top-header { position: sticky; top: 0; z-index: 999;
    background: rgba(255,255,255,0.97); backdrop-filter: blur(12px);
    border-bottom: 1px solid #E5E5EA; padding: 10px 24px;
    display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.top-header .brand { font-size: 18px; font-weight: 800; color: #1D1D1F; white-space: nowrap; }
.top-header .data-ts { font-size: 11px; color: #8E8E93; white-space: nowrap; }
/* ── Target achievement badges ── */
.tgt-green  { background:#E8F9EE; color:#1A7F37; padding:3px 10px; border-radius:10px; font-weight:700; font-size:12px; }
.tgt-yellow { background:#FFF3E0; color:#E65100; padding:3px 10px; border-radius:10px; font-weight:700; font-size:12px; }
.tgt-red    { background:#FFEBE9; color:#CF222E; padding:3px 10px; border-radius:10px; font-weight:700; font-size:12px; }
/* ── Negative labour alert ── */
.neg-lab-alert { background:#FFEBE9; border-left:4px solid #FF3B30; border-radius:10px;
    padding:12px 16px; margin-bottom:10px; }
.neg-lab-alert b { color:#CF222E; }
/* ── Rank movement ── */
.rank-up   { color:#34C759; font-weight:700; }
.rank-dn   { color:#FF3B30; font-weight:700; }
.rank-eq   { color:#8E8E93; font-weight:600; }
/* ── Mobile responsive ── */
@media (max-width: 1024px) {
    [data-testid="stHorizontalBlock"] > div { min-width: 48% !important; flex: 1 1 48% !important; }
    .section-card { padding: 14px !important; }
    .kpi-card  { padding: 10px 12px !important; }
    .kpi-value { font-size: 18px !important; }
    .styled-table { font-size: 11px !important; }
    div[data-testid="stHorizontalBlock"]:has(.js-plotly-plot) > div { min-width: 100% !important; }
}
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] > div { min-width: 100% !important; }
    .kpi-value { font-size: 16px !important; }
    .kpi-card  { padding: 10px 12px !important; }
}
</style>
"""
st.markdown(APPLE_CSS, unsafe_allow_html=True)

from utils.constants import PLY, C, LOC_COLORS, WS_COLORS

# FORMATTERS & UTILS
from ui.formatters import fmt_inr, fmt_inr_full, fmt_inr_short, fmt_pct, fmt_num








def classify_location(name, client_config=None):
    if client_config:
        if name in client_config["arena_locations"]: return "Arena"
        if name in client_config["nexa_locations"]: return "Nexa"
    else:
        # Fallback uses first client in CLIENTS dict
        first = list(CLIENTS.values())[0]
        if name in first["arena_locations"]: return "Arena"
        if name in first["nexa_locations"]: return "Nexa"
    return "Other"

from utils.loaders import load_targets, load_unbilled_sheets, load_raw_worksheet, load_raw_expense, TARGET_COLS
from services.financial_service import FinancialService
from utils.calculations.common import calc_ratio, calc_growth_pct
from utils.calculations.fact_metrics import get_vor_charges
from ui.helpers import render_neg_labour_alert
from services.logger import logger
from services.error_handler import safe_render

from utils.aggregations import location_summary, advisor_summary, monthly_summary
from utils.filters import apply_month_filter, apply_location_filter, apply_location_group_filter, apply_service_type_filter, apply_advisor_filter, apply_ws_bs_filter, split_cp_pp

# DATA LOADING
from services.logging_service import log_performance

@st.cache_data(ttl=300)
@log_performance(page_context="Data Loader")
def load_data(client_config):
    sheet_id = client_config["sheet_id"]
    sheet_tab = client_config["sheet_tab"]
    arena_locs = client_config["arena_locations"]
    nexa_locs = client_config["nexa_locations"]
    
    df = load_raw_worksheet(sheet_id, sheet_tab)
    
    # Exclusions
    df = df[~df['Service Type'].isin(EXCLUDE_SERVICE_TYPES)]
    
    # Deterministic DataFrame Cleaning
    from utils.cleaning import clean_dataframe
    df = clean_dataframe(df, ADV_COL, MONTH_SORT_ORDER, BS_SERVICE_TYPES)

    df['Location Group'] = df['Location Name'].apply(lambda x: classify_location(x, client_config))
    
    # Load Expense data
    exp_df = load_raw_expense(sheet_id)
    
    return df, exp_df

# ALERT SYSTEM
def compute_alerts(df_cp, df_pp):
    alerts = []
    
    # Alert 1: Labour discount > 25% for any location this period
    loc_disc = location_summary(df_cp, as_index=True).agg(
        L=('Pre-GST Labour','sum'), D=('Labour Discount','sum'))
    loc_disc['D%'] = calc_ratio(loc_disc['D'], loc_disc['L'], multiplier=100, fill_value=np.nan)
    high_disc = loc_disc[loc_disc['D%'] > HIGH_DISC_ALERT].index.tolist()
    if high_disc:
        alerts.append(('red', f"⚠️ High Labour Discount: {', '.join(high_disc)} exceed {HIGH_DISC_ALERT}% threshold"))
    
    # Alert 2: Any location with YoY decline > 15%
    loc_cp = location_summary(df_cp, as_index=True)['Net_Labour'].sum()
    loc_pp = location_summary(df_pp, as_index=True)['Net_Labour'].sum()
    for loc in loc_cp.index:
        if loc in loc_pp.index and loc_pp[loc] > 50000:
            yoy = calc_growth_pct(loc_cp[loc], loc_pp[loc], fill_value=np.nan) if loc_pp[loc] and not np.isnan(loc_pp[loc]) else np.nan
            if not np.isnan(yoy) and yoy < -YOY_DECLINE_ALERT:
                alerts.append(('red', f"📉 {loc} declined {abs(yoy):.1f}% YoY in Net Labour"))
    
    # Alert 3: VOR charges this period (elevated excess stock charges)
    vor = get_vor_charges(df_cp)
    if vor < -VOR_ALERT_THRESHOLD:
        alerts.append(('yellow', f"🔧 Elevated VOR charges at {fmt_inr(abs(vor))} — excess stock review needed"))
    
    # Alert 4: New location (appears in CP but not in PP)
    new_locs = set(df_cp['Location Name'].unique()) - set(df_pp['Location Name'].unique())
    if new_locs:
        alerts.append(('blue', f"🆕 New locations active this period: {', '.join(new_locs)}"))
    
    return alerts



# MONTH PICKER & GLOBAL FILTERS
def build_pairs(selected_months, all_months, month_sort, comparison_mode="YoY"):
    # Build reverse lookup for performance
    rev = {v: k for k, v in month_sort.items()}
    offset = -12 if comparison_mode == "YoY" else -1
    pairs = []
    for cm in sorted(selected_months, key=lambda x: month_sort.get(x, 99)):
        cm_sort = month_sort.get(cm, 99)
        pm = rev.get(cm_sort + offset)
        if pm and pm in all_months:
            pairs.append((cm, pm, cm_sort))
    return pairs

def render_month_picker(df):
    all_months = sorted(df['Month Name'].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
    latest_month = [all_months[-1]] if all_months else []

    # Build preset options
    preset_options = ["Custom", "1M", "3M", "6M"]
    for fy_label, fy_month_list in FY_MONTHS.items():
        if any(m in fy_month_list for m in all_months):
            preset_options.append(fy_label)

    # Initialize state: only set if missing from session_state
    if "month_preset" not in st.session_state:
        st.session_state.month_preset = "3M"
        st.session_state.last_preset = "3M"
        st.session_state.selected_months_custom = latest_month

    if "selected_months_custom" not in st.session_state:
        st.session_state.selected_months_custom = latest_month
    else:
        # On every rerun: filter invalid months, reset to latest if empty
        st.session_state.selected_months_custom = [
            m for m in st.session_state.selected_months_custom
            if m in all_months
        ]
        if not st.session_state.selected_months_custom:
            st.session_state.selected_months_custom = latest_month

    # Callback for when user clicks a radio button
    def on_preset_change():
        preset = st.session_state.month_preset
        if preset != "Custom":
            if preset == "1M":
                st.session_state.selected_months_custom = [all_months[-1]] if all_months else []
            elif preset == "3M":
                st.session_state.selected_months_custom = all_months[-3:] if len(all_months) >= 3 else all_months
            elif preset == "6M":
                st.session_state.selected_months_custom = all_months[-6:] if len(all_months) >= 6 else all_months
            else:
                fy_list = FY_MONTHS.get(preset, [])
                st.session_state.selected_months_custom = [m for m in all_months if m in fy_list]
        st.session_state.last_preset = preset

    # Callback for when user manually changes the multiselect
    def on_custom_change():
        st.session_state.month_preset = "Custom"
        st.session_state.last_preset = "Custom"

    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([0.8, 6.5, 1.7, 1.5])
    
    with c1:
        st.markdown('<div style="padding:16px 0;font-size:13px;font-weight:600;color:#6E6E73;">Period</div>', unsafe_allow_html=True)
    with c2:
        preset = st.radio("Select Period", preset_options, horizontal=True, key="month_preset", label_visibility="collapsed", on_change=on_preset_change)
    with c3:
        mode_label = st.radio("Comparison Mode", ["YoY", "MoM"], horizontal=True, key="comparison_mode_radio", label_visibility="collapsed")
        comparison_mode = (mode_label == "YoY")
    with c4:
        if st.button("🔄 Reset All", width='stretch', key="clear_all"):
            for key in ["filter_loc_group", "filter_location", "filter_svc_type", "filter_adv", "month_preset", "selected_months_custom", "comparison_mode_radio", "last_preset"]:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    is_custom = st.session_state.get("month_preset", "3M") == "Custom"
    
    if is_custom:
        selected_months = st.multiselect("Current Period (CP)", all_months, key="selected_months_custom", on_change=on_custom_change)
    else:
        selected_months = st.session_state.selected_months_custom
        preset_val = st.session_state.get("month_preset", "3M")
        if preset_val != "Custom":
            st.markdown(f'<div style="margin-bottom:12px;font-size:14px;color:#1d1d1f;font-weight:500;">Selected Period: Last {preset_val}</div>', unsafe_allow_html=True)
            
    pairs = build_pairs(selected_months, all_months, MONTH_SORT_ORDER, "YoY" if comparison_mode else "MoM")

    if is_custom:
        if pairs:
            pair_tags = " ".join(f'<span style="background:#E8F0FE;color:#0071E3;padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600;margin-right:4px;">{cm} ↔ {pm}</span>' for cm, pm, _ in pairs)
            st.markdown(f'<div style="margin-bottom:12px;font-size:12px;color:#6E6E73;"><b>Matched Pairs ({mode_label}):</b><br>{pair_tags}</div>', unsafe_allow_html=True)
        else:
            if selected_months:
                if len(selected_months) == 1 and not comparison_mode:
                    st.warning("Select 2+ months for MoM comparison, or switch to YoY mode.")
                else:
                    st.warning(f"No prior-period data found in dataset for {mode_label} comparison. "
                               f"Check that the sheet contains data for the prior period.")

    return selected_months, pairs, comparison_mode

def render_global_filters(df):
    # Read previous filter state for label
    def _count():
        n = 0
        if st.session_state.get("filter_loc_group"): n += 1
        if st.session_state.get("filter_location"): n += 1
        if st.session_state.get("filter_svc_type"): n += 1
        if st.session_state.get("filter_advisor"): n += 1
        if st.session_state.get("filter_ws_bs", "All") != "All": n += 1
        return n
    active_count = _count()
    with st.sidebar:
        st.markdown("---")
        label = f"### 🔍 Global Filters ({active_count})" if active_count else "### 🔍 Global Filters"
        st.markdown(label)
        
        loc_group = st.multiselect(
            "Location Group",
            ["Arena", "Nexa", "Other"],
            default=[],
            key="filter_loc_group"
        )

        available_locs = sorted(df['Location Name'].dropna().unique().tolist())
        if loc_group:
            available_locs = [l for l in available_locs if df[df['Location Name'] == l]['Location Group'].iloc[0] in loc_group]
        location = st.multiselect(
            "Location",
            available_locs,
            default=[],
            key="filter_location"
        )

        svc_type = st.multiselect(
            "Service Type",
            sorted(df['Service Type'].dropna().unique().tolist()),
            default=[],
            key="filter_svc_type"
        )

        advisor = st.multiselect(
            "Advisor",
            sorted(df[ADV_COL].dropna().unique().tolist()),
            default=[],
            key="filter_advisor"
        )

        ws_bs = st.radio(
            "WS/BS",
            ["All", "WS", "BS"],
            horizontal=True,
            key="filter_ws_bs"
        )
        
        st.markdown("---")
        st.markdown("### ⚙ Actions")
        if st.button("🧹 Reset All", use_container_width=True, key="clear_filters"):
            for key in ["filter_loc_group", "filter_location", "filter_svc_type", "filter_advisor", "filter_ws_bs"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # Apply filters
    d = df
    d = apply_location_group_filter(d, 'Location Group', loc_group)
    d = apply_location_filter(d, 'Location Name', location)
    d = apply_service_type_filter(d, 'Service Type', svc_type)
    d = apply_advisor_filter(d, ADV_COL, advisor)
    d = apply_ws_bs_filter(d, 'WS_BS', ws_bs)
    
    return d, active_count

# TABS


# COCKPIT MOVED TO pages.cockpit



# LEAKAGE SHARED HELPERS
# Leakage functions are now imported globally from services.financial_service






# NEW TABS








# TAB: TARGET VS ACTUAL



# TAB: INTERNAL AUDIT REPORT





def sidebar_navigation():
    with st.sidebar:
        st.markdown("### 🚗 Navigation")
        st.markdown("---")
    
        # Helper for active state buttons
        def nav_btn(label, target_page):
            # Using 'secondary' for inactive, 'primary' for active
            is_active = st.session_state.get("current_page") == target_page
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, use_container_width=True, type=btn_type):
                st.session_state["current_page"] = target_page
                st.rerun()

        # 📊 OVERVIEW
        with st.expander("📊 OVERVIEW"):
            nav_btn("Cockpit", "Cockpit")
            nav_btn("Overview", "Overview")
            nav_btn("Executive", "Executive")
    
        # 💰 REVENUE
        with st.expander("💰 REVENUE"):
            nav_btn("Labour", "Labour")
            nav_btn("Parts", "Parts")
            nav_btn("Margin", "Margin")
            nav_btn("Sales Mix", "Sales Mix")
            nav_btn("Discounts", "Discounts")
            nav_btn("Leakage Center", "Leakage Center")

        # 👥 PEOPLE
        with st.expander("👥 PEOPLE"):
            nav_btn("Advisors", "Advisors")
            nav_btn("Advisor MoM", "Advisor MoM")

        # 📈 PERFORMANCE
        with st.expander("📈 PERFORMANCE"):
            nav_btn("Locations", "Locations")
            nav_btn("Trends", "Trends")
            nav_btn("Targets", "Targets")

        # 🏦 FINANCE
        with st.expander("🏦 FINANCE"):
            nav_btn("Expense Analysis", "Expense Analysis")
            nav_btn("Profit & Loss", "Profit & Loss")

        # 🛠 ADMIN
        with st.expander("🛠 ADMIN"):
            nav_btn("Reports", "Reports")
            nav_btn("Internal Audit", "Internal Audit")
            nav_btn("Audit Intelligence", "Audit Intelligence")

        # ⚙️ OPERATIONS (Hidden)
        if st.query_params.get("admin") == "true":
            with st.expander("⚙️ OPERATIONS"):
                nav_btn("System Health", "System Health")

def render_page_router(df_filtered_full, df_filtered_cp, df_filtered, pairs, alerts, comparison_mode, selected_months, targets_df, client_config, exp_df_filtered_cp=None):
    page = st.session_state.get("current_page", "Cockpit")

    if page == "Cockpit":
        with st.spinner("Loading Cockpit..."):
            from views.cockpit import render
        render(df_filtered_full, pairs, alerts, comparison_mode, selected_months)
    elif page == "Overview":
        with st.spinner("Crunching numbers..."):
            from views.overview import render
        safe_render(render, df_filtered_full, pairs, alerts, comparison_mode, selected_months)
    elif page == "Labour":
        with st.spinner("Crunching numbers..."):
            from views.yoy import render
        safe_render(render, df_filtered_full, pairs, "Net_Labour", "ly", "Labour", comparison_mode, selected_months)
    elif page == "Parts":
        with st.spinner("Crunching numbers..."):
            from views.yoy import render
        safe_render(render, df_filtered_full, pairs, "Net_Parts", "py", "Parts", comparison_mode, selected_months)
    elif page == "Margin":
        with st.spinner("Crunching numbers..."):
            from views.margin import render
        safe_render(render, df_filtered_cp, pairs, comparison_mode, selected_months)
    elif page == "Discounts":
        with st.spinner("Crunching numbers..."):
            from views.discount import render
        safe_render(render, df_filtered_cp, pairs, comparison_mode, selected_months)
    elif page == "Leakage Center":
        with st.spinner("Crunching numbers..."):
            from views.leakage import render
        safe_render(render, df_filtered_full, pairs, comparison_mode, selected_months)
    elif page == "Sales Mix":
        with st.spinner("Crunching numbers..."):
            from views.sales_mix import render
        safe_render(render, df_filtered_cp, pairs, comparison_mode, selected_months)
    elif page == "Advisors":
        with st.spinner("Crunching numbers..."):
            from views.advisor import render
        safe_render(render, df_filtered_cp, pairs, comparison_mode, selected_months)
    elif page == "Advisor MoM":
        with st.spinner("Crunching numbers..."):
            from views.advisor_mom import render
        safe_render(render, df_filtered_full, pairs, comparison_mode, selected_months)
    elif page == "Locations":
        with st.spinner("Crunching numbers..."):
            from views.locations import render
        safe_render(render, df_filtered_cp, pairs, comparison_mode, selected_months)
    elif page == "Trends":
        with st.spinner("Crunching numbers..."):
            from views.trends import render
        safe_render(render, df_filtered_full, pairs, comparison_mode, selected_months)
    elif page == "Targets":
        with st.spinner("Crunching numbers..."):
            from views.targets import render
        safe_render(render, df_filtered_cp, targets_df, pairs)
    elif page == "Reports":
        with st.status("📄 Generating reports...", expanded=False) as _s:
            from views.reports import render
        safe_render(render, df_filtered_cp, pairs, comparison_mode, selected_months)
        _s.update(label="Reports ready", state="complete", expanded=False)
    elif page == "Executive":
        with st.status("📊 Building executive summary...", expanded=False) as _s:
            from views.executive import render
        safe_render(render, df_filtered_full, pairs, comparison_mode, selected_months)
        _s.update(label="Executive summary ready", state="complete", expanded=False)
    elif page == "Expense Analysis":
        with st.spinner("Loading Expense Analysis..."):
            from views.expense import render
        safe_render(render, exp_df_filtered_cp, selected_months)
    elif page == "Profit & Loss":
        with st.spinner("Loading Profit & Loss..."):
            from views.pnl import render
        safe_render(render, df_filtered_cp, exp_df_filtered_cp, selected_months)
    elif page == "Audit Intelligence":
        with st.spinner("Loading Audit Intelligence..."):
            from views.audit_intelligence import render
        safe_render(render, df_filtered_full, pairs, alerts, comparison_mode, selected_months)
    elif page == "Internal Audit":
        with st.status("🔍 Running audit analysis...", expanded=False) as _s:
            st.caption("⏳ Exception scan · Leakage detection · Risk register")
            from views.internal_audit import render
        safe_render(render, df_filtered, client_config, cp=df_filtered_cp)
        _s.update(label="Audit analysis complete", state="complete", expanded=False)
    elif page == "System Health":
        with st.spinner("Loading System Health..."):
            from views.system_health import render
        safe_render(render, df_filtered_full, exp_df_filtered_cp)
    else:
        st.error(f"Page '{page}' not found.")

def main():
    # ── Environment Validation (once per session) ───────────────────
    if "env_validated" not in st.session_state:
        from config.environment import validate_environment
        validate_environment()
        st.session_state["env_validated"] = True

    # ── Pilot Access Control ────────────────────────────────────────
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Check for deployment password in Streamlit Secrets or Environment
    deployment_password = None
    try:
        deployment_password = st.secrets.get("DEPLOYMENT_PASSWORD")
    except Exception:
        # No secrets file configured
        pass
    deployment_password = deployment_password or os.environ.get("DEPLOYMENT_PASSWORD")

    if deployment_password and not st.session_state["authenticated"]:
        st.markdown("""
        <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#F5F5F7;">
            <div style="background:#FFFFFF;padding:40px;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.1);text-align:center;max-width:400px;">
                <div style="font-size:48px;margin-bottom:16px;">🔐</div>
                <h2 style="margin:0 0 8px 0;color:#1D1D1F;">WSMIS Pilot</h2>
                <p style="color:#8E8E93;margin-bottom:24px;">Enter deployment password to continue</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        password = st.text_input("Password", type="password", key="deploy_password", label_visibility="collapsed")
        if st.button("Access", key="deploy_access", use_container_width=True):
            if password == deployment_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid password")
        return

    if "last_refresh" not in st.session_state:
        st.session_state["last_refresh"] = datetime.now().strftime("%H:%M")
    if "data_synced_at" not in st.session_state:
        st.session_state["data_synced_at"] = None
    if "selected_months" not in st.session_state:
        st.session_state["selected_months"] = None
    if "preset_applied" not in st.session_state:
        st.session_state["preset_applied"] = False
    if "last_preset" not in st.session_state:
        st.session_state["last_preset"] = "Custom"
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Cockpit"
    if "startup_time" not in st.session_state:
        st.session_state["startup_time"] = round(time.time() - START_TIME, 2)

    client_names = list(CLIENTS.keys())

    # ── Sidebar Navigation ────────────────────────────────────────
    sidebar_navigation()

    # ── Sidebar Workspace ─────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🏢 Workspace")
        sel_client = st.selectbox("Client", client_names, key="client_sel", label_visibility="collapsed")

    # ── Main Header ───────────────────────────────────────────────
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown(
            '<div style="font-size:24px;font-weight:800;color:#1D1D1F;margin-bottom:-10px;">'
            '🚗 WSMIS <span style="font-size:14px;font-weight:500;color:#8E8E93;">v1.0.0-rc1</span></div>',
            unsafe_allow_html=True
        )
    with h2:
        if st.button("🔄 Refresh", width='stretch', key="main_refresh"):
            st.cache_data.clear()
            st.session_state["last_refresh"] = datetime.now().strftime("%H:%M")
            st.session_state["data_synced_at"] = datetime.now()
            st.rerun()

    # ── Load data ─────────────────────────────────────────────────
    df = None
    exp_df = None
    targets_df = pd.DataFrame(columns=TARGET_COLS)
    data_loaded_time = None
    try:
        with st.spinner("Loading data from Google Sheets..."):
            df, exp_df = load_data(CLIENTS[sel_client])
            targets_df = load_targets(CLIENTS[sel_client]["sheet_id"])
            data_loaded_time = datetime.now()
            if st.session_state.get("data_synced_at") is None:
                st.session_state["data_synced_at"] = data_loaded_time
    except Exception as e:
        st.error(f"❌ Error loading sheet: {e}")
        return

    if data_loaded_time:
        synced_at = st.session_state.get("data_synced_at") or data_loaded_time
        age_hours = (datetime.now() - synced_at).total_seconds() / 3600
        freshness_icon  = "🟡" if age_hours > 24 else "🟢"
        freshness_label = "Stale — sync recommended" if age_hours > 24 else "Healthy"
        st.markdown(
            f"<div style='font-size:12px;color:#8E8E93;margin-top:-10px;margin-bottom:10px;'>"
            f"📅 Last Synced: <b>{synced_at.strftime('%d %b %Y, %I:%M %p')}</b>"
            f" &nbsp;|&nbsp; {len(df):,} records"
            f" &nbsp;|&nbsp; {freshness_icon} {freshness_label}</div>",
            unsafe_allow_html=True
        )

    if df is None or df.empty:
        st.warning("No data found.")
        return

    # ── Month picker & filters ─────────────────────────────────────
    if st.session_state.get("current_page") != "Internal Audit":
        selected_months, pairs, comparison_mode = render_month_picker(df)
        df_filtered, active_filter_count = render_global_filters(df)
    else:
        selected_months, pairs, comparison_mode = [], [], False
        df_filtered, active_filter_count = df, 0

    # ── Prepare data for tabs with comparison support ───────────────
    # For tabs that need comparison (YoY/MoM), include both CP and PP months
    cp_months = [p[0] for p in pairs]
    pp_months = [p[1] for p in pairs]
    all_comparison_months = list(set(cp_months + pp_months))

    # df_filtered_full: includes both CP and PP months for comparison tabs
    df_filtered_full = apply_month_filter(df_filtered, "Month Name", all_comparison_months)

    # df_filtered_cp: only CP months for tabs that don't need comparison
    df_filtered_cp = apply_month_filter(df_filtered, "Month Name", selected_months) if selected_months else df_filtered

    # ── Filter exp_df ──────────────────────────────────────────────
    exp_df_filtered_cp = exp_df if exp_df is not None else pd.DataFrame()
    if not exp_df_filtered_cp.empty:
        # Apply global location filter
        filter_location = st.session_state.get("filter_location")
        if filter_location:
            exp_df_filtered_cp = apply_location_filter(exp_df_filtered_cp, "Location", filter_location)
        elif st.session_state.get("filter_loc_group"):
            # If group is filtered but not specific locations, filter by group locs
            group_locs = [l for l in CLIENTS[sel_client]["arena_locations"] + CLIENTS[sel_client]["nexa_locations"] 
                          if classify_location(l, CLIENTS[sel_client]) in st.session_state.get("filter_loc_group")]
            exp_df_filtered_cp = apply_location_filter(exp_df_filtered_cp, "Location", group_locs)
            
        # Apply month filter
        if selected_months:
            exp_df_filtered_cp = apply_month_filter(exp_df_filtered_cp, "Month Name", selected_months)

    # ── Alerts (use comparison data) ───────────────────────────────
    cp = apply_month_filter(df_filtered_full, "Month Name", cp_months)
    pp = apply_month_filter(df_filtered_full, "Month Name", pp_months)
    alerts = compute_alerts(cp, pp)

    # Negative labour — always visible
    render_neg_labour_alert(cp)

    # Period summary pill
    if selected_months and pp_months:
        sorted_cp = sorted(selected_months, key=lambda x: MONTH_SORT_ORDER.get(x, 99))
        sorted_pp = sorted(pp_months, key=lambda x: MONTH_SORT_ORDER.get(x, 99))
        st.markdown(
            f'<div style="background:#E8F0FE;border-radius:8px;padding:5px 14px;'
            f'font-size:12px;font-weight:600;color:#185FA5;display:inline-block;margin-bottom:8px;">'
            f'📅 {sorted_cp[0]} → {sorted_cp[-1]} '
            f'vs {sorted_pp[0]} → {sorted_pp[-1]} '
            f'&nbsp;|  {len(df_filtered_cp):,} rows '
            f'&nbsp;|  {df_filtered_cp["Location Name"].nunique()} locations'
            f'</div>',
            unsafe_allow_html=True
        )



    # ── Page Router ───────────────────────────────────────────────
    render_page_router(df_filtered_full, df_filtered_cp, df_filtered, pairs, alerts, comparison_mode, selected_months, targets_df, CLIENTS[sel_client], exp_df_filtered_cp)

if __name__ == "__main__":
    main()
