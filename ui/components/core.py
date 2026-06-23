import streamlit as st

def UniversalHeader(client_name: str, report_title: str, selected_months: list, synced_at: str):
    """
    Universal Report Header matching the approved enterprise design.
    """
    
    # Official display names mapping
    DISPLAY_TITLES = {
        "Cockpit": "Executive Command Center",
        "Overview": "Workshop Overview",
        "Executive": "Executive Dashboard",
        "Labour": "Labour Revenue",
        "Parts": "Parts Revenue",
        "Margin": "Margin Analysis",
        "Sales Mix": "Sales Mix",
        "Discounts": "Discount Analysis",
        "Leakage Center": "Leakage Center",
        "Advisors": "Advisor Performance",
        "Advisor MoM": "Advisor MoM Performance",
        "Locations": "Location Performance",
        "Trends": "Performance Trends",
        "Targets": "Target vs Actual",
        "Reports": "Automated Reports",
        "Expense Analysis": "Expense Analysis",
        "Profit & Loss": "Profit & Loss",
        "Internal Audit": "Internal Audit",
        "Audit Intelligence": "Audit Intelligence",
        "System Health": "System Health"
    }
    official_title = DISPLAY_TITLES.get(report_title, report_title)

    # Format period
    if not selected_months:
        period_str = "All Periods"
    elif len(selected_months) == 1:
        period_str = selected_months[0]
    elif len(selected_months) == 2:
        period_str = f"{selected_months[0]} & {selected_months[1]}"
    else:
        period_str = f"{selected_months[0]} to {selected_months[-1]}"

    st.markdown(f'''
    <div class="report-header">
        <div class="rh-left">
            <div class="rh-client">{client_name}</div>
            <div class="rh-title">{official_title}</div>
            <div class="rh-period">{period_str}</div>
        </div>
        <div class="rh-right-container">
            <div class="rh-divider"></div>
            <div class="rh-right">
                <div class="rh-firm">Saurabh A Jain & Co.</div>
                <div class="rh-sub">Chartered Accountants • Internal Audit</div>
                <div class="rh-confidential-container"><span class="rh-confidential">CONFIDENTIAL</span></div>
                <div class="rh-bottom">
                    <span>🗓 Synced: {synced_at}</span>
                    <span class="rh-pipe">|</span>
                    <span>v1.0.0-rc1</span>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def UniversalFooter():
    """
    Universal Report Footer for all pages.
    """
    st.markdown(f'''
    <div class="report-footer">
        <div class="rf-top">Strictly Confidential · For Internal Use Only · Unauthorised reproduction is strictly prohibited.</div>
        <div class="rf-bottom">
            <div>Saurabh A Jain & Co. (Chartered Accountants)</div>
            <div><a href="mailto:support@autollp.in" style="color:inherit; text-decoration:none;">support@autollp.in</a></div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def EmptyState(message: str = "No data available for this period", 
               sub: str = "Adjust the period or location filter to view results"):
    """
    Renders a premium empty state with icon, message, and sub-message.
    """
    html = f"""
    <div class="empty-state">
      <svg class="empty-state-icon" width="40" height="40" viewBox="0 0 24 24" 
           fill="none" stroke="currentColor" stroke-width="1.5" 
           stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
      </svg>
      <p class="empty-state-title">{message}</p>
      <p class="empty-state-sub">{sub}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def AlertBanner(message: str, type: str = "warning"):
    """
    Standardized Alert Banner (e.g. High Discount Warnings).
    types: warning, error, info, success
    """
    from ui.design_tokens import T
    bg_colors = {
        "warning": T.COLOR_WARNING_BG,
        "error": T.COLOR_DANGER_BG,
        "info": T.COLOR_INFO_BG,
        "success": T.COLOR_SUCCESS_BG
    }
    border_colors = {
        "warning": T.COLOR_WARNING,
        "error": T.COLOR_DANGER,
        "info": T.COLOR_PRIMARY,
        "success": T.COLOR_SUCCESS
    }
    icons = {
        "warning": "⚠️",
        "error": "🚨",
        "info": "ℹ️",
        "success": "✅"
    }
    
    bg = bg_colors.get(type, bg_colors["info"])
    border = border_colors.get(type, border_colors["info"])
    icon = icons.get(type, icons["info"])

    html = f'''<div style="background:{bg}; border-left:4px solid {border}; padding:{T.SPACE_3}px {T.SPACE_4}px; border-radius:{T.RADIUS_SM}px; margin-bottom:{T.SPACE_4}px; display:flex; align-items:center; gap:{T.SPACE_3}px;">
    <span style="font-size:18px;">{icon}</span>
    <span style="color:var(--color-text-primary); font-size:{T.TYPE_BASE}px; font-weight:500;">{message}</span>
</div>'''
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)

def spacer(height: int = 16):
    """Renders a vertical spacer."""
    st.markdown(f'<div style="height:{height}px;"></div>', unsafe_allow_html=True)

def section_card(content: str):
    """Renders content inside a standardized surface card."""
    from ui.design_tokens import T
    html = f'<div class="section-card" style="background:var(--color-surface); border-radius:{T.RADIUS_LG}px; padding:{T.SPACE_4}px; border:1px solid var(--color-border); box-shadow:var(--shadow-sm); margin-bottom:{T.SPACE_4}px;">{content}</div>'
    st.markdown(html, unsafe_allow_html=True)

def section_title(title: str):
    """Renders a standard section title."""
    from ui.design_tokens import T
    html = f'<div class="section-title" style="font-size:{T.TYPE_MD}px; font-weight:600; color:var(--color-text-primary); margin-bottom:{T.SPACE_3}px;">{title}</div>'
    st.markdown(html, unsafe_allow_html=True)

def badge(text: str, variant: str = "info"):
    """
    Renders a status badge inline.
    Variants: info, success, warning, danger, new
    """
    from ui.design_tokens import T
    colors = {
        "info": {"bg": T.COLOR_INFO_BG, "color": T.COLOR_PRIMARY},
        "success": {"bg": T.COLOR_SUCCESS_BG, "color": T.COLOR_SUCCESS},
        "warning": {"bg": T.COLOR_WARNING_BG, "color": T.COLOR_WARNING},
        "danger": {"bg": T.COLOR_DANGER_BG, "color": T.COLOR_DANGER},
        "new": {"bg": T.COLOR_INFO_BG, "color": T.COLOR_NEW},
    }
    style = colors.get(variant, colors["info"])
    return f'<span style="background:{style["bg"]}; color:{style["color"]}; padding:2px 8px; border-radius:{T.RADIUS_SM}px; font-size:{T.TYPE_XS}px; font-weight:600;">{text}</span>'

def divider():
    """Renders a standard divider."""
    from ui.design_tokens import T
    st.markdown(f'<hr style="border:0; border-top:1px solid var(--color-border); margin:{T.SPACE_4}px 0;" />', unsafe_allow_html=True)
