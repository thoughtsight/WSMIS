import streamlit as st
import pandas as pd

def TableCard(df: pd.DataFrame, height: int = 400, index: bool = False):
    """
    Standardized Data Table wrapper.
    Renders a dataframe in a clean card container.
    """
    if df is None or df.empty:
        from .core import EmptyState
        EmptyState("No data available to display in this table.")
        return

    from ui.design_tokens import T
    st.markdown(f'<div class="table-card" style="background:var(--color-surface); border-radius:{T.RADIUS_LG}px; padding:{T.SPACE_4}px; border:1px solid var(--color-border); box-shadow:var(--shadow-sm); margin-bottom:{T.SPACE_4}px;">', unsafe_allow_html=True)
    
    # We use Streamlit's native dataframe rendering but wrapped in a card to maintain visual consistency.
    st.dataframe(df, use_container_width=True, height=height, hide_index=not index)
    
    st.markdown('</div>', unsafe_allow_html=True)
