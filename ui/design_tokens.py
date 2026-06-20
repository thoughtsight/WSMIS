"""
WSMIS Design Tokens v2.0 — Executive Light
Single source of truth for the entire visual system.

All colours, spacing, typography, radius, shadows and chart defaults
live here. Nothing else in the codebase should hardcode these values.

Usage:
    from ui.design_tokens import T
    color = T.COLOR_PRIMARY          # "#0071E3"
    size  = T.TYPE_XL                # 32
    space = T.SPACE_4                # 16
"""


class T:
    """
    WSMIS Design Token Registry.
    All values are either str (hex / CSS) or int (px).
    """

    # ─────────────────────────────────────────────────────────────────────────
    # TYPOGRAPHY SCALE  (Major Third: 1.25×, base 11px)
    # ─────────────────────────────────────────────────────────────────────────
    TYPE_XS   = 11   # Metadata · Timestamps · Badges · Axis ticks
    TYPE_SM   = 12   # Table cells · Axis labels · Secondary labels
    TYPE_BASE = 14   # Body text · Insight cards · Tooltips
    TYPE_MD   = 16   # Section headings · Card subtitles
    TYPE_LG   = 20   # Page sub-headings
    TYPE_XL   = 32   # KPI values  (platform standard)
    TYPE_2XL  = 40   # KPI hero on large screen / presentation

    FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"

    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM  = 500
    WEIGHT_SEMIBOLD= 600
    WEIGHT_BOLD    = 700
    WEIGHT_EXTRABOLD=800

    # ─────────────────────────────────────────────────────────────────────────
    # SPACING SCALE  (4px base unit — every value is a multiple of 4)
    # ─────────────────────────────────────────────────────────────────────────
    SPACE_1  = 4
    SPACE_2  = 8
    SPACE_3  = 12
    SPACE_4  = 16
    SPACE_5  = 20
    SPACE_6  = 24
    SPACE_8  = 32
    SPACE_10 = 40
    SPACE_12 = 48

    # ─────────────────────────────────────────────────────────────────────────
    # BORDER RADIUS
    # ─────────────────────────────────────────────────────────────────────────
    RADIUS_SM = 6    # Badges · Pills · Small chips
    RADIUS_MD = 8    # Cards · Inputs · Buttons  (main standard)
    RADIUS_LG = 10   # Section cards · Report header

    # ─────────────────────────────────────────────────────────────────────────
    # COLOUR PALETTE — Application
    # ─────────────────────────────────────────────────────────────────────────

    # Backgrounds
    COLOR_APP_BG    = "#F2F2F7"   # App shell — soft neutral grey (NOT white)
    COLOR_SURFACE   = "#FFFFFF"   # Cards · Panels · Inputs
    COLOR_SURFACE2  = "#F8F8FA"   # Table alternates · Subtler surfaces

    # Borders & Dividers
    COLOR_BORDER     = "#E5E5EA"  # Card borders · Input borders
    COLOR_BORDER_SUB = "#F0F0F5"  # Table row dividers (lighter)
    COLOR_DIVIDER    = "#D4AF37"  # Gold — report header accent ONLY

    # Text
    COLOR_TEXT_PRIMARY   = "#1D1D1F"  # Headings · Values · Body
    COLOR_TEXT_SECONDARY = "#6E6E73"  # Labels · Muted content
    COLOR_TEXT_TERTIARY  = "#8E8E93"  # Placeholders · Metadata

    # ─────────────────────────────────────────────────────────────────────────
    # COLOUR PALETTE — Semantic (on light backgrounds — WCAG AA compliant)
    # ─────────────────────────────────────────────────────────────────────────

    COLOR_PRIMARY   = "#0071E3"   # Accent · Links · Active state
    COLOR_NEW       = "#0071E3"   # New location / first period badge

    # On-surface semantic text (dark enough for WCAG AA on white)
    COLOR_SUCCESS   = "#1A7F37"   # Green text on light  — 4.6:1 ✅
    COLOR_DANGER    = "#CF222E"   # Red text on light    — 5.5:1 ✅
    COLOR_WARNING   = "#B45309"   # Amber text on light  — 4.7:1 ✅

    # Icon / graphic semantic (these FAIL as text on white — use fill only)
    COLOR_SUCCESS_FILL = "#34C759"  # Green fill for dark backgrounds / icons
    COLOR_DANGER_FILL  = "#FF3B30"  # Red fill for dark backgrounds / icons

    # Badge backgrounds (light tinted fills)
    COLOR_SUCCESS_BG = "#E8F9EE"  # Light green badge background
    COLOR_DANGER_BG  = "#FFEBE9"  # Light red badge background
    COLOR_WARNING_BG = "#FFF3E0"  # Light amber badge background
    COLOR_INFO_BG    = "#E8F0FE"  # Light blue badge background

    # ─────────────────────────────────────────────────────────────────────────
    # ELEVATION (Shadows)
    # ─────────────────────────────────────────────────────────────────────────
    SHADOW_SM = "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)"
    SHADOW_MD = "0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.07)"
    SHADOW_LG = "0 10px 15px rgba(0,0,0,0.07), 0 4px 6px rgba(0,0,0,0.05)"

    # ─────────────────────────────────────────────────────────────────────────
    # CHART PALETTE
    # ─────────────────────────────────────────────────────────────────────────
    CHART_CP      = "#0071E3"   # Current Period bars
    CHART_PP      = "#C0C0C8"   # Previous Period bars (light neutral, not grey)
    CHART_GROWTH  = "#FF9500"   # Growth % line overlay
    CHART_POS_MKR = "#1A7F37"   # Positive growth markers / dots
    CHART_NEG_MKR = "#CF222E"   # Negative growth markers / dots

    # ─────────────────────────────────────────────────────────────────────────
    # CHART TYPOGRAPHY — responsive by size (Major Second: 1.125×)
    # Each dict: title / axis_title / axis_tick / label / legend / tooltip
    # ─────────────────────────────────────────────────────────────────────────
    CHART_TYPE = {
        "small": {
            "title": 14, "axis_title": 12, "axis_tick": 11,
            "label": 12, "legend": 11, "tooltip": 12,
            "height": 280, "margin": {"t": 40, "b": 40, "l": 48, "r": 20},
            "line_width": 2.0, "marker": 7,
        },
        "medium": {
            "title": 16, "axis_title": 13, "axis_tick": 12,
            "label": 13, "legend": 12, "tooltip": 13,
            "height": 360, "margin": {"t": 52, "b": 52, "l": 52, "r": 24},
            "line_width": 2.5, "marker": 9,
        },
        "large": {
            "title": 18, "axis_title": 14, "axis_tick": 13,
            "label": 14, "legend": 13, "tooltip": 14,
            "height": 440, "margin": {"t": 60, "b": 60, "l": 60, "r": 32},
            "line_width": 3.0, "marker": 11,
        },
        "full": {
            "title": 22, "axis_title": 16, "axis_tick": 14,
            "label": 16, "legend": 14, "tooltip": 15,
            "height": 520, "margin": {"t": 72, "b": 72, "l": 72, "r": 40},
            "line_width": 3.5, "marker": 13,
        },
    }

    # ─────────────────────────────────────────────────────────────────────────
    # LEGACY ALIASES  (maps old constants.py "C" dict to tokens)
    # ─────────────────────────────────────────────────────────────────────────
    # These allow existing code using C["primary"] to continue working
    # while gradually migrating to T.COLOR_PRIMARY.
    C = {
        "primary":  "#0071E3",
        "green":    "#1A7F37",   # updated to accessible on-light green
        "red":      "#CF222E",   # updated to accessible on-light red
        "orange":   "#FF9500",
        "gray":     "#8E8E93",
        "gold":     "#D4AF37",
        "purple":   "#7C3AED",
        "pink":     "#DB2777",
        "teal":     "#0891B2",
    }
