import streamlit as st
from utils.calculations.common import calc_growth_pct

def MetricCard(label: str, value: str, sub: str = None, cp: float = None, pp: float = None, benchmark: str = None, target: str = None, invert_trend: bool = False):
    """
    Standardized Metric Card.
    invert_trend: If True, negative growth is good (green) and positive is bad (red). Example: Discounts.
    """
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    delta_html = ""
    
    if cp is not None and pp is not None:
        if pp <= 0 and cp > 0:
            delta_html = '<div class="kpi-delta-new" style="color:#007AFF; font-size:12px; font-weight:600; margin-top:4px;">New ✦</div>'
        elif pp > 0:
            pct = calc_growth_pct(cp, pp, fill_value=0)
            
            # Determine color based on invert_trend
            if pct >= 0:
                cls = "kpi-delta-neg" if invert_trend else "kpi-delta-pos"
                arrow = "▲"
            else:
                cls = "kpi-delta-pos" if invert_trend else "kpi-delta-neg"
                arrow = "▼"
                
            # Use inline styles if CSS classes are not fully updated yet to guarantee consistent Enterprise polish
            color = "#34C759" if "pos" in cls else "#FF3B30"
            delta_html = f'<div class="{cls}" style="color:{color}; font-size:12px; font-weight:600; margin-top:4px; display:flex; align-items:center; gap:2px;"><span>{arrow}</span> {abs(pct):.1f}%</div>'
            
    meta_parts = []
    if benchmark is not None:
        meta_parts.append(f'<span style="color:#86868b;">Bench:</span> {benchmark}')
    if target is not None:
        meta_parts.append(f'<span style="color:#86868b;">Target:</span> {target}')
        
    meta_html = f'<div class="kpi-meta" style="font-size:11px; margin-top:8px; border-top:1px solid #f5f5f7; padding-top:4px;">{" · ".join(meta_parts)}</div>' if meta_parts else ""
    
    html = f"""<div class="kpi-card" style="background:#fff; border-radius:12px; padding:16px; border:1px solid #e5e5ea; box-shadow:0 1px 2px rgba(0,0,0,0.02); height:100%; display:flex; flex-direction:column; justify-content:space-between;">
    <div>
        <div class="kpi-label" style="font-size:13px; color:#6E6E73; font-weight:500; margin-bottom:4px;">{label}</div>
        <div class="kpi-value" style="font-size:24px; font-weight:700; color:#1d1d1f; letter-spacing:-0.5px;">{value}</div>
        {sub_html}
        {delta_html}
    </div>
    {meta_html}
</div>"""
    st.markdown(html, unsafe_allow_html=True)

def KPIGrid(metrics: list):
    """
    Renders a responsive grid of metric cards.
    metrics: list of dicts with kwargs for MetricCard.
    """
    if not metrics:
        return
        
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            MetricCard(**metric)
