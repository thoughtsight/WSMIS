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

    st.markdown('<div class="table-card" style="background:#fff; border-radius:12px; padding:16px; border:1px solid #e5e5ea; box-shadow:0 1px 2px rgba(0,0,0,0.02); margin-bottom:16px;">', unsafe_allow_html=True)
    
    # We use Streamlit's native dataframe rendering but wrapped in a card to maintain visual consistency.
    st.dataframe(df, use_container_width=True, height=height, hide_index=not index)
    
    st.markdown('</div>', unsafe_allow_html=True)
