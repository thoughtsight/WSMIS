import os

def rewrite_app_py():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Insert PAGE_CAPABILITIES
    page_capabilities_code = """
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
"""
    if "PAGE_CAPABILITIES =" not in content:
        content = content.replace("from config.settings import HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD", 
                                  "from config.settings import HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD\n" + page_capabilities_code)

    # 2. Modify render_month_picker to accept page_capabilities overrides
    target_month_picker = """def render_month_picker(df):
    all_months = sorted(df['Month Name'].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
    default_cp = [all_months[-1]] if all_months else []

    # Initialize state
    if "month_preset" not in st.session_state:
        st.session_state.month_preset = "3M"
        st.session_state.last_preset = "3M"
        st.session_state.selected_months_custom = default_cp"""
    
    new_month_picker = """def render_month_picker(df, page):
    capabilities = PAGE_CAPABILITIES.get(page, {"default_period": "3M", "comparison_mode": True, "show_period_filter": True, "show_comparison_filter": True})
    
    all_months = sorted(df['Month Name'].unique(), key=lambda x: MONTH_SORT_ORDER.get(x, 99))
    default_cp = [all_months[-1]] if all_months else []

    # Apply page specific capabilities to session state if visiting for the first time
    if st.session_state.get(f"last_visited_page") != page:
        st.session_state.month_preset = capabilities["default_period"]
        st.session_state.last_preset = capabilities["default_period"]
        st.session_state.comparison_mode_radio = "YoY" if capabilities["comparison_mode"] else "None"
        
        preset = capabilities["default_period"]
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
        st.session_state.selected_months_custom = default_cp"""
        
    content = content.replace(target_month_picker, new_month_picker)

    # 3. Modify rendering of filters (hide based on capabilities)
    target_header_bar = """    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([0.8, 6.5, 1.7, 1.5])"""
    new_header_bar = """    if not capabilities["show_period_filter"] and not capabilities["show_comparison_filter"]:
        return st.session_state.selected_months_custom, build_pairs(st.session_state.selected_months_custom, all_months, MONTH_SORT_ORDER, "YoY" if st.session_state.get("comparison_mode_radio") == "YoY" else "MoM"), capabilities["comparison_mode"]

    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([0.8, 6.5, 1.7, 1.5])"""
    content = content.replace(target_header_bar, new_header_bar)
    
    # Update invocation of render_month_picker
    content = content.replace("selected_months, pairs, comparison_mode = render_month_picker(df)", "selected_months, pairs, comparison_mode = render_month_picker(df, st.session_state.get('current_page'))")

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    rewrite_app_py()
    print("Done")
