EXECUTIVE_THEME_CSS = """
<style>
/* Premium Charcoal Theme - Design Standard for WSMIS */
/* Background: #26282B, Border: #36393F, Section: #1F2125 */

/* Executive Summary Layout Container */
.exec-heading {
    font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
    color: #a1a1a6; margin: 16px 0 8px 0;
}
.kpi-wrapper {
    display: flex; gap: 12px; margin-bottom: 12px;
}

/* Base KPI Card - Premium Charcoal - Denser Layout */
.kpi-box {
    flex: 1; background: #1F2125; border: 1px solid #36393F; border-radius: 8px;
    padding: 10px 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}
.kpi-title {
    font-size: 13px; font-weight: 600; color: #a1a1a6; text-transform: uppercase;
    margin-bottom: 6px; letter-spacing: 0.5px;
}
.kpi-val {
    font-size: 42px; font-weight: 700; color: #ffffff; line-height: 1.1; margin-bottom: 6px;
}
.kpi-footer {
    display: flex; align-items: baseline; gap: 8px; font-size: 13px; font-weight: 500;
}

/* Delta Pills - Rounded with Background */
.delta-pill {
    display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 12px;
    font-size: 12px; font-weight: 600; letter-spacing: 0.3px;
}
.delta-pill.pos {
    background: rgba(52, 199, 89, 0.15); color: #34c759;
}
.delta-pill.neg {
    background: rgba(255, 59, 48, 0.15); color: #ff3b30;
}

/* Indicators */
.g-pos { color: #34c759; font-weight: 600; }
.g-neg { color: #ff3b30; font-weight: 600; }
.pp-val { color: #d0d0d0; font-weight: 600; font-size: 13px; }

/* Service Panels (PMS/Bodyshop) - Premium Charcoal */
.svc-panel { padding: 10px 14px; }
.svc-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 1px solid #36393F;
}
.svc-row:last-child { border-bottom: none; padding-bottom: 0; }
.svc-label { color: #a1a1a6; font-size: 12px; font-weight: 600; }
.svc-vals { display: flex; align-items: baseline; justify-content: flex-end; gap: 10px; }
.svc-cp { color: #ffffff; font-weight: 700; width: 90px; text-align: right; font-size: 18px; }
.svc-cp-tag { color: #34c759; font-size: 11px; font-weight: 600; margin-left: 2px; }
.svc-pp { color: #d0d0d0; font-weight: 600; width: 80px; text-align: right; font-size: 15px; }

/* AI Narrative Band */
.ai-band {
    background: #1F2125; border: 1px solid #36393F; border-radius: 8px;
    padding: 12px 16px; margin: 16px 0; color: #e0e0e0; font-size: 13px; line-height: 1.5;
}

/* Section Titles */
.section-title {
    font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;
    color: #a1a1a6; margin: 20px 0 12px 0;
}

/* Insight Cards */
.insight-card {
    background: #1F2125; border: 1px solid #36393F; border-radius: 8px;
    padding: 12px; margin-bottom: 8px;
}
.insight-card.pos { border-left: 3px solid #34c759; }
.insight-card.neg { border-left: 3px solid #ff3b30; }
.insight-title { font-size: 11px; font-weight: 600; color: #a1a1a6; margin-bottom: 4px; }
.insight-stat { font-size: 13px; color: #e0e0e0; }

/* Executive Table Header Styling */
[data-testid="stDataFrame"] th {
    background: #2a2d32 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-bottom: 2px solid #36393F !important;
}
</style>
"""
