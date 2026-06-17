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
BS_SERVICE_TYPES = {"BR"}

# Month order and Financial Year mappings
MONTH_SORT_ORDER = {
    # FY 24-25
    "Jan-24":1,"Feb-24":2,"Mar-24":3,"Apr-24":4,"May-24":5,"Jun-24":6,
    "Jul-24":7,"Aug-24":8,"Sep-24":9,"Oct-24":10,"Nov-24":11,"Dec-24":12,
    # FY 25-26
    "Jan-25":13,"Feb-25":14,"Mar-25":15,"Apr-25":16,"May-25":17,"Jun-25":18,
    "Jul-25":19,"Aug-25":20,"Sep-25":21,"Oct-25":22,"Nov-25":23,"Dec-25":24,
    # FY 26-27
    "Jan-26":25,"Feb-26":26,"Mar-26":27,"Apr-26":28,"May-26":29,"Jun-26":30,
    "Jul-26":31,"Aug-26":32,"Sep-26":33,"Oct-26":34,"Nov-26":35,"Dec-26":36,
    # FY 27-28
    "Jan-27":37,"Feb-27":38,"Mar-27":39,"Apr-27":40,"May-27":41,"Jun-27":42,
    "Jul-27":43,"Aug-27":44,"Sep-27":45,"Oct-27":46,"Nov-27":47,"Dec-27":48,
    # FY 28-29
    "Jan-28":49,"Feb-28":50,"Mar-28":51,"Apr-28":52,"May-28":53,"Jun-28":54,
    "Jul-28":55,"Aug-28":56,"Sep-28":57,"Oct-28":58,"Nov-28":59,"Dec-28":60,
}

FY_MONTHS = {
    "FY 24-25": ["Apr-24","May-24","Jun-24","Jul-24","Aug-24","Sep-24","Oct-24","Nov-24","Dec-24","Jan-25","Feb-25","Mar-25"],
    "FY 25-26": ["Apr-25","May-25","Jun-25","Jul-25","Aug-25","Sep-25","Oct-25","Nov-25","Dec-25","Jan-26","Feb-26","Mar-26"],
    "FY 26-27": ["Apr-26","May-26","Jun-26","Jul-26","Aug-26","Sep-26","Oct-26","Nov-26","Dec-26","Jan-27","Feb-27","Mar-27"],
    "FY 27-28": ["Apr-27","May-27","Jun-27","Jul-27","Aug-27","Sep-27","Oct-27","Nov-27","Dec-27","Jan-28","Feb-28","Mar-28"],
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
WS_COLORS  = {"WS": "#0071E3", "BS": "#FF9500"}
