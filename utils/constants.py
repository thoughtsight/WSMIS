# utils/constants.py

# Shared Configuration Values
ADV_COL = "Advisior Name"   # column name as it appears in the Google Sheet (typo preserved)

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

# Month order and Financial Year mappings
MONTH_SORT_ORDER = {
    # FY 24-25
    "January-2024":1,"February-2024":2,"March-2024":3,"April-2024":4,"May-2024":5,"June-2024":6,
    "July-2024":7,"August-2024":8,"September-2024":9,"October-2024":10,"November-2024":11,"December-2024":12,
    # FY 25-26
    "January-2025":13,"February-2025":14,"March-2025":15,"April-2025":16,"May-2025":17,"June-2025":18,
    "July-2025":19,"August-2025":20,"September-2025":21,"October-2025":22,"November-2025":23,"December-2025":24,
    # FY 26-27
    "January-2026":25,"February-2026":26,"March-2026":27,"April-2026":28,"May-2026":29,"June-2026":30,
    "July-2026":31,"August-2026":32,"September-2026":33,"October-2026":34,"November-2026":35,"December-2026":36,
    # FY 27-28
    "January-2027":37,"February-2027":38,"March-2027":39,"April-2027":40,"May-2027":41,"June-2027":42,
    "July-2027":43,"August-2027":44,"September-2027":45,"October-2027":46,"November-2027":47,"December-2027":48,
    # FY 28-29
    "January-2028":49,"February-2028":50,"March-2028":51,"April-2028":52,"May-2028":53,"June-2028":54,
    "July-2028":55,"August-2028":56,"September-2028":57,"October-2028":58,"November-2028":59,"December-2028":60,
}

FY_MONTHS = {
    "FY 24-25": ["April-2024","May-2024","June-2024","July-2024","August-2024","September-2024","October-2024","November-2024","December-2024","January-2025","February-2025","March-2025"],
    "FY 25-26": ["April-2025","May-2025","June-2025","July-2025","August-2025","September-2025","October-2025","November-2025","December-2025","January-2026","February-2026","March-2026"],
    "FY 26-27": ["April-2026","May-2026","June-2026","July-2026","August-2026","September-2026","October-2026","November-2026","December-2026","January-2027","February-2027","March-2027"],
    "FY 27-28": ["April-2027","May-2027","June-2027","July-2027","August-2027","September-2027","October-2027","November-2027","December-2027","January-2028","February-2028","March-2028"],
}

SERVICE_ACCOUNT = "service_account.json"

# Plotly theme configuration
PLY = dict(
    template="simple_white",
    font=dict(family="Inter, -apple-system, sans-serif", color="#1D1D1F", size=12),
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    xaxis=dict(gridcolor="#F0F0F5", linecolor="#E5E5EA", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#F0F0F5", linecolor="#E5E5EA", tickfont=dict(size=11)),
    margin=dict(l=48, r=24, t=52, b=40),
    hoverlabel=dict(bgcolor="#FFFFFF", font_size=13, font_family="Inter", bordercolor="#E5E5EA"),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E5E5EA", borderwidth=1,
                font=dict(size=11), orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1),
    title=dict(font=dict(size=14, color="#1D1D1F", family="Inter"), x=0.01, xanchor="left", pad=dict(t=4)),
)

# Color palettes
C = {"primary":"#0071E3", "green":"#34C759", "red":"#FF3B30", "orange":"#FF9500",
     "gray":"#8E8E93", "gold":"#C8860A", "purple":"#AF52DE", "pink":"#FF2D55", "teal":"#5AC8FA"}
LOC_COLORS = {"Arena": "#0071E3", "Nexa": "#34C759", "Other": "#8E8E93"}
MP_COLORS  = {"MP": "#0071E3", "PB": "#FF9500"}
