import streamlit as st
from typing import List, Dict

def FilterToolbar(capabilities: dict, all_months: List[str], advisors: List[str] = None):
    """
    Standardized Filter Toolbar dynamically driven by page capabilities.
    Returns a dictionary of the selected filters.
    """
    from ui.design_tokens import T
    st.markdown(f'<div class="filter-toolbar" style="padding:{T.SPACE_3}px {T.SPACE_4}px; border-radius:{T.RADIUS_MD}px; border:1px solid var(--color-border); margin-bottom:{T.SPACE_4}px;">', unsafe_allow_html=True)
    
    selections = {}
    
    # We use columns to layout the active filters side-by-side
    active_filters = []
    if capabilities.get("show_period_filter"): active_filters.append("period")
    if capabilities.get("show_comparison_filter"): active_filters.append("comparison")
    if capabilities.get("show_service_type_filter"): active_filters.append("service_type")
    
    module_filters = capabilities.get("additional_module_filters", [])
    for mf in module_filters:
        active_filters.append(mf.lower())
        
    if not active_filters:
        st.markdown('</div>', unsafe_allow_html=True)
        return selections

    cols = st.columns(len(active_filters) + 1) # +1 for Reset button
    
    col_idx = 0
    
    if capabilities.get("show_period_filter"):
        with cols[col_idx]:
            default_p = capabilities.get("default_period", "3M")
            preset_options = ["1M", "3M", "6M", "YTD", "Custom"]
            preset = st.selectbox("Period", preset_options, index=preset_options.index(default_p) if default_p in preset_options else 1, key="comp_period")
            selections["preset"] = preset
            
            if preset == "Custom":
                selected_months = st.multiselect("Custom Months", all_months, default=all_months[-3:] if len(all_months) >= 3 else all_months, key="comp_custom_months")
                selections["selected_months"] = selected_months
            else:
                selections["selected_months"] = [] # Handled by the backend logic later
        col_idx += 1
                
    if capabilities.get("show_comparison_filter"):
        with cols[col_idx]:
            mode = st.radio("Comparison", ["YoY", "MoM"], horizontal=True, key="comp_compare")
            selections["comparison_mode"] = (mode == "YoY")
        col_idx += 1
        
    if capabilities.get("show_service_type_filter"):
        with cols[col_idx]:
            svc = st.selectbox("Service Type", ["All", "Free", "Paid", "Running Repair", "Accidental"], key="comp_svc")
            selections["service_type"] = svc if svc != "All" else None
        col_idx += 1
        
    for mf in module_filters:
        with cols[col_idx]:
            if mf == "Advisor" and advisors:
                adv = st.selectbox("Advisor", ["All"] + advisors, key="comp_adv")
                selections["advisor"] = adv if adv != "All" else None
        col_idx += 1
        
    with cols[-1]:
        st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
        if st.button("🔄 Reset", key="comp_reset"):
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)
    return selections
