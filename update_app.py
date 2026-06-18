with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove Main Header
main_header_block = '''    # ── Main Header ───────────────────────────────────────────────
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
            st.rerun()'''
content = content.replace(main_header_block, '')

# 2. Remove Metadata Block
meta_block = '''    if data_loaded_time:
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
        )'''
content = content.replace(meta_block, '')

# 3. Add UniversalHeader after filters
target = '''    df_filtered, active_filter_count = render_global_filters(df)
    df_filtered, page_active_count = render_page_header_filters(df_filtered, st.session_state.get('current_page'))'''

new_header = '''    df_filtered, active_filter_count = render_global_filters(df)
    df_filtered, page_active_count = render_page_header_filters(df_filtered, st.session_state.get('current_page'))

    # ── Universal Header ──────────────────────────────────────────
    from ui.components.core import UniversalHeader, UniversalFooter
    synced_at_str = (st.session_state.get("data_synced_at") or data_loaded_time).strftime('%d %b %Y, %I:%M %p') if (data_loaded_time or st.session_state.get("data_synced_at")) else "Unknown"
    UniversalHeader(
        client_name=sel_client,
        report_title=page,
        selected_months=selected_months,
        synced_at=synced_at_str
    )'''
content = content.replace(target, new_header)

# 4. Add UniversalFooter at the end
footer_target = '''    else:
        st.error(f"Page '{page}' not found.")'''
new_footer = '''    else:
        st.error(f"Page '{page}' not found.")

    # ── Universal Footer ──────────────────────────────────────────
    from ui.components.core import UniversalFooter
    UniversalFooter()'''
content = content.replace(footer_target, new_footer)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
