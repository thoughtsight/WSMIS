import streamlit as st

def render_developer_diagnostics(ctx):
    """
    Renders a collapsible developer diagnostics panel to verify the AppContext
    and TargetProvider state. This should be used during RC1 verification.
    """
    with st.expander("🛠️ Developer Diagnostics (RC1)"):
        st.write("### Active Filters")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Business Unit:** {st.session_state.get('filter_mp_pb', 'All')}")
            st.write(f"**Business View:** {st.session_state.get('filter_mp_pb', 'All')}")
        with col2:
            st.write(f"**Location:** {st.session_state.get('filter_location', 'All')}")
            st.write(f"**Service Type:** {st.session_state.get('filter_svc_type', 'All')}")
        with col3:
            st.write(f"**Advisor:** {st.session_state.get('filter_advisor', 'All')}")
            st.write(f"**Cross-filter status:** {'Active' if any([st.session_state.get('filter_location'), st.session_state.get('filter_advisor')]) else 'Inactive'}")
        
        st.divider()
        st.write("### AppContext Pipeline")
        st.write(f"**Selected Months:** {ctx.selected_months}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("#### df_filtered (Global)")
            if ctx.df_filtered is not None and not ctx.df_filtered.empty:
                st.write(f"Row count: {len(ctx.df_filtered)}")
                st.write(f"Min Month: {ctx.df_filtered['Month Name'].min()}")
                st.write(f"Max Month: {ctx.df_filtered['Month Name'].max()}")
            else:
                st.write("Empty")
                
        with col2:
            st.write("#### df_filtered_cp (Current Period)")
            if ctx.df_filtered_cp is not None and not ctx.df_filtered_cp.empty:
                st.write(f"Row count: {len(ctx.df_filtered_cp)}")
                st.write(f"Min Month: {ctx.df_filtered_cp['Month Name'].min()}")
                st.write(f"Max Month: {ctx.df_filtered_cp['Month Name'].max()}")
            else:
                st.write("Empty")
                
        with col3:
            st.write("#### df_filtered_full (6M History)")
            if ctx.df_filtered_full is not None and not ctx.df_filtered_full.empty:
                st.write(f"Row count: {len(ctx.df_filtered_full)}")
                st.write(f"Min Month: {ctx.df_filtered_full['Month Name'].min()}")
                st.write(f"Max Month: {ctx.df_filtered_full['Month Name'].max()}")
            else:
                st.write("Empty")
        
        st.divider()
        st.write("### Period Breakdown")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("#### Current Period (CP)")
            if ctx.df_filtered_cp is not None and not ctx.df_filtered_cp.empty:
                st.write(f"**CP Months:** {sorted(ctx.df_filtered_cp['Month Name'].unique().tolist())}")
                st.write(f"**CP Rows:** {len(ctx.df_filtered_cp)}")
            else:
                st.write("Empty")
        with col2:
            st.write("#### Previous Period (PP)")
            if ctx.pairs:
                pp_months = [p[1] for p in ctx.pairs]
                st.write(f"**PP Months:** {sorted(pp_months)}")
                pp_rows = len(ctx.df_filtered_full[ctx.df_filtered_full['Month Name'].isin(pp_months)]) if ctx.df_filtered_full is not None else 0
                st.write(f"**PP Rows:** {pp_rows}")
            else:
                st.write("No PP data")
        with col3:
            st.write("#### Forecast (6M History)")
            if ctx.df_filtered_full is not None and not ctx.df_filtered_full.empty:
                st.write(f"**Forecast Rows:** {len(ctx.df_filtered_full)}")
            else:
                st.write("Empty")
                
        st.divider()
        st.write("### TargetProvider State")
        if hasattr(ctx, 'target_provider') and ctx.target_provider is not None:
            raw = ctx.target_provider._raw_df
            st.write(f"Raw Targets Loaded: {len(raw)} rows")
            if not raw.empty:
                st.write(f"**Target Month(s):** {sorted(raw['Month Name'].unique().tolist())}")
                st.dataframe(raw.head(5), use_container_width=True)
                
            st.write("#### Active Period Targets (Aggregated)")
            if not ctx.df_filtered_cp.empty:
                cp_locs = ctx.df_filtered_cp["Location Name"].unique().tolist()
                cp_months = ctx.df_filtered_cp["Month Name"].unique().tolist()
                
                rev_tgt = ctx.target_provider.get_revenue_target(cp_locs, cp_months)
                parts_tgt = ctx.target_provider.get_parts_target(cp_locs, cp_months)
                
                # compute weights - TargetProvider handles this internally
                disc_tgt = ctx.target_provider.get_discount_target(cp_locs, cp_months, ctx.df_filtered_cp)
                
                st.write(f"- Revenue Target: {rev_tgt:,.2f}")
                st.write(f"- Parts Target: {parts_tgt:,.2f}")
                st.write(f"- Discount Target (Weighted): {disc_tgt:.2f}%")
            else:
                st.write("No active period data to calculate targets for.")
        else:
            st.error("TargetProvider not initialized in AppContext.")
