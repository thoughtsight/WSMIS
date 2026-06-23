# utils/constants.py

# Shared Configuration Values
ADV_COL = "Advisior Name"   # column name as it appears in the Google Sheet (typo preserved)

# Category colour mapping for Parts module charts
# Uses design tokens for consistency across the application
from ui.design_tokens import T
CATEGORY_COLORS = {
    "Standard Parts": T.COLOR_PRIMARY,
    "Oil": T.COLOR_SUCCESS,
    "Accessories": T.COLOR_WARNING,
    "Tyres": T.COLOR_DANGER,
    "Battery": "#7C3AED",  # Purple - not in standard tokens
    "Other": "#8E8E93",   # Gray - not in standard tokens
}

CLIENTS = {
    "Rukmani Motors": {
        "sheet_id": "1RUodK2UyYlG86DyGV3-0iyR7bdvkPLgeJJ0VlReHG_A",
        "sheet_tab": "JC_TAT(24-25)",
        "arena_locations": {"ALPR","Bhavra","DN","Dhar","Dharam","GBS",
                            "Jobat","MG","Rajgarh","Simrol","Arvindo","SOW(A)","Rajod","Bagh"},
        "nexa_locations": {"Palda","FT","NSD","SOW(N)"},
        "logo": "🚗",
        "primary_color": "#0071E3",
    },
}

EXCLUDE_SERVICE_TYPES = ["Credit Note", "Top Up"]
ARENA_LOCATIONS = {"ALPR","Bhavra","DN","Dhar","Dharam","GBS","Jobat","MG",
                   "Rajgarh","Simrol","Arvindo","SOW(A)","Rajod","Bagh",
                   "GANDHWANI-3S(RO)","PORT BLAIR"}
NEXA_LOCATIONS = {"Palda","FT","NSD","SOW(N)"}
PB_SERVICE_TYPES = {"BR"}
PB_LOCATIONS = {"PBA", "SOW(PB)"}

# Month order and Financial Year mappings
MONTH_SORT_ORDER = {
    # FY 24-25
    "Jan-2024":1,"Feb-2024":2,"Mar-2024":3,"Apr-2024":4,"May-2024":5,"Jun-2024":6,
    "Jul-2024":7,"Aug-2024":8,"Sep-2024":9,"Oct-2024":10,"Nov-2024":11,"Dec-2024":12,
    # FY 25-26
    "Jan-2025":13,"Feb-2025":14,"Mar-2025":15,"Apr-2025":16,"May-2025":17,"Jun-2025":18,
    "Jul-2025":19,"Aug-2025":20,"Sep-2025":21,"Oct-2025":22,"Nov-2025":23,"Dec-2025":24,
    # FY 26-27
    "Jan-2026":25,"Feb-2026":26,"Mar-2026":27,"Apr-2026":28,"May-2026":29,"Jun-2026":30,
    "Jul-2026":31,"Aug-2026":32,"Sep-2026":33,"Oct-2026":34,"Nov-2026":35,"Dec-2026":36,
    # FY 27-28
    "Jan-2027":37,"Feb-2027":38,"Mar-2027":39,"Apr-2027":40,"May-2027":41,"Jun-2027":42,
    "Jul-2027":43,"Aug-2027":44,"Sep-2027":45,"Oct-2027":46,"Nov-2027":47,"Dec-2027":48,
    # FY 28-29
    "Jan-2028":49,"Feb-2028":50,"Mar-2028":51,"Apr-2028":52,"May-2028":53,"Jun-2028":54,
    "Jul-2028":55,"Aug-2028":56,"Sep-2028":57,"Oct-2028":58,"Nov-2028":59,"Dec-2028":60,
}

FY_MONTHS = {
    "FY 24-25": ["Apr-2024","May-2024","Jun-2024","Jul-2024","Aug-2024","Sep-2024","Oct-2024","Nov-2024","Dec-2024","Jan-2025","Feb-2025","Mar-2025"],
    "FY 25-26": ["Apr-2025","May-2025","Jun-2025","Jul-2025","Aug-2025","Sep-2025","Oct-2025","Nov-2025","Dec-2025","Jan-2026","Feb-2026","Mar-2026"],
    "FY 26-27": ["Apr-2026","May-2026","Jun-2026","Jul-2026","Aug-2026","Sep-2026","Oct-2026","Nov-2026","Dec-2026","Jan-2027","Feb-2027","Mar-2027"],
    "FY 27-28": ["Apr-2027","May-2027","Jun-2027","Jul-2027","Aug-2027","Sep-2027","Oct-2027","Nov-2027","Dec-2027","Jan-2028","Feb-2028","Mar-2028"],
}

SERVICE_ACCOUNT = "service_account.json"

# Plotly theme configuration — Executive Light v2.0
PLY = dict(
    template="simple_white",
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", color="#1D1D1F", size=12),
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    xaxis=dict(gridcolor="#F0F0F5", linecolor="#E5E5EA", tickfont=dict(size=12, family="Inter")),
    yaxis=dict(gridcolor="#F0F0F5", linecolor="#E5E5EA", tickfont=dict(size=12, family="Inter")),
    margin=dict(l=52, r=24, t=52, b=44),
    hoverlabel=dict(bgcolor="#FFFFFF", font_size=13, font_family="Inter, -apple-system, sans-serif", bordercolor="#E5E5EA"),
    legend=dict(bgcolor="rgba(255,255,255,0.92)", bordercolor="#E5E5EA", borderwidth=1,
                font=dict(size=12, family="Inter"), orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1),
)

# Plotly title styling (used separately to avoid duplicate key errors)
PLY_TITLE = dict(font=dict(size=16, color="#1D1D1F", family="Inter", weight=700), x=0.01, xanchor="left", pad=dict(t=4))


def get_ply_layout(**kwargs):
    """
    Get a clean PLY layout dict with additional kwargs merged in.
    Removes any conflicting keys to avoid duplicate argument errors.
    
    Usage:
        fig.update_layout(**get_ply_layout(title="My Title", height=300))
    """
    layout_cfg = dict(PLY)
    # Remove keys that might conflict with passed kwargs
    layout_cfg.pop("title", None)
    layout_cfg.pop("title_text", None)
    layout_cfg.update(kwargs)
    return layout_cfg

# Color palettes — Executive Light v2.0
# NOTE: green/red are WCAG AA compliant on-light text values (not fills).
# For chart fills / icon fills, use COLOR_SUCCESS_FILL / COLOR_DANGER_FILL from design_tokens.
C = {
    "primary": "#0071E3",
    "green":   "#1A7F37",   # 4.6:1 on white — WCAG AA ✅
    "red":     "#CF222E",   # 5.5:1 on white — WCAG AA ✅
    "orange":  "#B45309",   # 4.7:1 on white — WCAG AA ✅
    "gray":    "#8E8E93",
    "gold":    "#D4AF37",
    "purple":  "#7C3AED",
    "pink":    "#DB2777",
    "teal":    "#0891B2",
}
# Chart fill colours (for bars/markers on white background — not as text)
CHART_CP = "#0071E3"   # Current Period bars
CHART_PP = "#C0C0C8"   # Previous Period bars — lighter neutral
LOC_COLORS = {"Arena": "#0071E3", "Nexa": "#1A7F37", "Other": "#8E8E93"}
MP_COLORS = {"MP": "#0071E3", "PB": "#FF9500", "WS": "#0071E3", "BS": "#FF9500"}
