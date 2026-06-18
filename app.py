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

from ui.components.core import UniversalHeader, UniversalFooter

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
    NEXA_LOCATIONS, PB_SERVICE_TYPES, MONTH_SORT_ORDER, FY_MONTHS, SERVICE_ACCOUNT
)
from config.settings import HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD

PAGE_CAPABILITIES = {
    "Overview": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Executive": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Cockpit": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Profit & Loss": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Expense Analysis": {"default_period": "1M", "comparison_mode": False, "show_period_filter": True, "show_comparison_filter": False, "show_service_type_filter": False, "additional_module_filters": []},
    "Labour": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Parts": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Advisors": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": ["Advisor"]},
    "Advisor MoM": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": ["Advisor"]},
    "Discounts": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Leakage Center": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Margin": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Sales Mix": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Locations": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Trends": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Targets": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "Reports": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
    "System Health": {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True, "show_service_type_filter": True, "additional_module_filters": []},
}


# PAGE CONFIG & CSS
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Auto LLP MIS v1.0.0-rc1", page_icon="🚗")

from pathlib import Path
APPLE_CSS = f"<style>\n{Path('static/style.css').read_text(encoding='utf-8')}\n</style>"
st.markdown(APPLE_CSS, unsafe_allow_html=True)

from utils.constants import PLY, C, LOC_COLORS, MP_COLORS

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
from utils.filters import apply_month_filter, apply_location_filter, apply_location_group_filter, apply_service_type_filter, apply_advisor_filter, apply_mp_pb_filter, split_cp_pp

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
    df = clean_dataframe(df, ADV_COL, MONTH_SORT_ORDER, PB_SERVICE_TYPES)

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

def render_month_picker(df, page):
    capabilities = PAGE_CAPABILITIES.get(page, {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True})
    all_months = sorted(df['Month Name'].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
    default_cp = [all_months[-1]] if all_months else []

    # Build preset options
    preset_options = ["Custom", "1M", "3M", "6M"]
    for fy_label, fy_month_list in FY_MONTHS.items():
        if any(m in fy_month_list for m in all_months):
            preset_options.append(fy_label)

    # Apply page specific capabilities to session state if visiting for the first time
    if st.session_state.get(f"last_visited_page") != page:
        st.session_state.month_preset = capabilities.get("default_period", "3M")
        st.session_state.last_preset = capabilities.get("default_period", "3M")
        st.session_state.comparison_mode_radio = "YoY" if capabilities.get("comparison_mode") else "None"
        
        preset = capabilities.get("default_period", "3M")
        if preset == "1M":
            st.session_state.selected_months_custom = [all_months[-1]] if all_months else []
        elif preset == "3M":
            st.session_state.selected_months_custom = all_months[-3:] if len(all_months) >= 3 else all_months
        elif preset == "6M":
            st.session_state.selected_months_custom = all_months[-6:] if len(all_months) >= 6 else all_months
        else:
            fy_list = FY_MONTHS.get(preset, [])
            st.session_state.selected_months_custom = [m for m in all_months if m in fy_list]
        st.session_state.last_visited_page = page

    # Initialize state
    if "month_preset" not in st.session_state:
        st.session_state.month_preset = "3M"
        st.session_state.last_preset = "3M"
        st.session_state.selected_months_custom = default_cp

    if "selected_months_custom" not in st.session_state:
        st.session_state.selected_months_custom = default_cp
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

    if not capabilities.get("show_period_filter") and not capabilities.get("show_comparison_filter"):
        return st.session_state.selected_months_custom, build_pairs(st.session_state.selected_months_custom, all_months, MONTH_SORT_ORDER, "YoY" if st.session_state.get("comparison_mode_radio") == "YoY" else "MoM"), capabilities.get("comparison_mode", False)

    # PAGE FILTERS (FilterToolbar UI)
    st.markdown('<div class="filter-toolbar" style="background:#f9f9fb; padding:12px 16px; border-radius:8px; border:1px solid #e5e5ea; margin-bottom:16px;">', unsafe_allow_html=True)
    
    # We figure out how many columns we need
    show_svc = capabilities.get("show_service_type_filter", False)
    show_adv = "Advisor" in capabilities.get("additional_module_filters", [])
    col_count = 3 # Period, Comparison Mode, Reset
    if show_svc: col_count += 1
    if show_adv: col_count += 1
    
    cols = st.columns(col_count)
    col_idx = 0
    
    with cols[col_idx]:
        preset = st.selectbox("Period", preset_options, index=preset_options.index(st.session_state.month_preset) if st.session_state.month_preset in preset_options else 1, key="month_preset", on_change=on_preset_change)
    col_idx += 1
    
    with cols[col_idx]:
        if hasattr(st, "segmented_control"):
            mode_label = st.segmented_control("Comparison", ["YoY", "MoM"], default="YoY", key="comparison_mode_radio")
        else:
            mode_label = st.radio("Comparison", ["YoY", "MoM"], horizontal=True, key="comparison_mode_radio")
        comparison_mode = (mode_label == "YoY")
    col_idx += 1
    
    if show_svc:
        with cols[col_idx]:
            svc_type_opts = sorted(df['Service Type'].dropna().unique().tolist())
            svc_type = st.multiselect("Service Type", svc_type_opts, default=[], key="filter_svc_type_single", placeholder="All")
            st.session_state.filter_svc_type = svc_type
        col_idx += 1
        
    if show_adv:
        with cols[col_idx]:
            adv_opts = ["All"] + sorted(df[ADV_COL].dropna().unique().tolist())
            advisor = st.selectbox("Advisor", adv_opts, key="filter_adv_single")
            st.session_state.filter_advisor = [advisor] if advisor != "All" else []
        col_idx += 1

    with cols[col_idx]:
        st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
        if st.button("🔄 Reset Page", key="clear_page"):
            for key in ["filter_svc_type_single", "filter_adv_single", "filter_svc_type", "filter_advisor", "month_preset", "selected_months_custom", "comparison_mode_radio", "last_preset"]:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    is_custom = st.session_state.get("month_preset", "3M") == "Custom"
    
    if is_custom:
        selected_months = st.multiselect("Custom Months", all_months, key="selected_months_custom", on_change=on_custom_change)
    else:
        selected_months = st.session_state.selected_months_custom
            
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
                    st.warning(f"No prior-period data found in dataset for {mode_label} comparison.")

    return selected_months, pairs, comparison_mode

def render_page_header_filters(df, page):
    # Now just apply the service/advisor filters set in render_month_picker
    active_count = 0
    d = df
    svc_type = st.session_state.get("filter_svc_type", [])
    advisor = st.session_state.get("filter_advisor", [])
    if svc_type: 
        d = apply_service_type_filter(d, 'Service Type', svc_type)
        active_count += 1
    if advisor: 
        d = apply_advisor_filter(d, ADV_COL, advisor)
        active_count += 1
    return d, active_count

def render_global_filters(df):
    active_count = 0
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🌍 Global Filters")
        
        loc_group = st.multiselect("Location Group", ["Arena", "Nexa", "Other"], key="filter_loc_group")
        available_locs = sorted(df['Location Name'].dropna().unique().tolist())
        if loc_group: available_locs = [l for l in available_locs if df[df['Location Name'] == l]['Location Group'].iloc[0] in loc_group]
        location = st.multiselect("Location", available_locs, key="filter_location")
        mp_pb = st.radio("Business Unit", ["All", "MP", "PB"], horizontal=True, key="filter_mp_pb")
        
        st.markdown("---")
        st.markdown("### ⚙ Actions")
        if st.button("🧹 Reset All Filters", use_container_width=True, key="clear_all_filters"):
            for key in ["filter_loc_group", "filter_location", "filter_svc_type", "filter_advisor", "filter_mp_pb", "month_preset", "selected_months_custom", "comparison_mode_radio", "last_preset", "filter_svc_type_single", "filter_adv_single"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    d = df
    if loc_group: 
        d = apply_location_group_filter(d, 'Location Group', loc_group)
        active_count += 1
    if location: 
        d = apply_location_filter(d, 'Location Name', location)
        active_count += 1
    if mp_pb and mp_pb != "All": 
        d = apply_mp_pb_filter(d, 'MP_PB', mp_pb)
        active_count += 1
        
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
            from views.labour import render
        safe_render(render, df_filtered_full, pairs, comparison_mode, selected_months)
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

    # ── Universal Footer ──────────────────────────────────────────
    UniversalFooter()

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



    if df is None or df.empty:
        st.warning("No data found.")
        return

    # ── Month picker & filters ─────────────────────────────────────
    selected_months, pairs, comparison_mode = render_month_picker(df, st.session_state.get('current_page'))
    df_filtered, active_filter_count = render_global_filters(df)
    df_filtered, page_active_count = render_page_header_filters(df_filtered, st.session_state.get('current_page'))

    # ── Universal Header ──────────────────────────────────────────
    synced_at_str = (st.session_state.get("data_synced_at") or data_loaded_time).strftime('%d %b %Y, %I:%M %p') if (data_loaded_time or st.session_state.get("data_synced_at")) else "Unknown"
    UniversalHeader(
        client_name=sel_client,
        report_title=st.session_state.get('current_page', 'Cockpit'),
        selected_months=selected_months,
        synced_at=synced_at_str
    )

    # ── Prepare data for tabs with comparison support ───────────────
    # For tabs that need comparison (YoY/MoM), include both CP and PP months
    cp_months = selected_months if selected_months else []
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
