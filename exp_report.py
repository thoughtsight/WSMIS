"""
RKM Motors — Expense Analysis Report Module
=============================================
Mirrors audit_report.py architecture.
Provides: CSS, JS, HTML builders for EXP tab in app.py.

Features:
  • Executive-first layout: KPIs → Charts → Location drill-down
  • Expense Mix interactive category cards
  • Two-column executive dashboard (cost centres + donut + vendors)
  • Monthly trend: budget vs actual, MoM trend
  • Location analysis with expandable rows
  • Transaction drilldown panel
  • 7 executive insights + action panel
  • Location → Expense Group → Expense Name collapsible tree
  • MoM % change table with colour-coded cells
  • AI-style alerts: spikes, sustained growth, high-share expenses
  • Summary dashboard across all locations
  • Trend sparkline cells
"""

import re
import pandas as pd
import numpy as np
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

MONTH_ORDER = [
    'Apr-25','May-25','Jun-25','Jul-25','Aug-25','Sep-25',
    'Oct-25','Nov-25','Dec-25','Jan-26','Feb-26','Mar-26','Apr-26'
]

# Canonical name map (handles CAPS duplicates from Google Sheet)
EXP_NAME_MAP = {
    'FREE SERVICE EXP- OTHER DEALERS': 'Free Service Exp- Other Dealers',
    'OTHER ITEM PURCHASE':             'Other Item Purchase',
    'PAINTING CONTRACTOR':             'Painting Contractor',
    'PAINTING MATERIAL PURCHASE':      'Painting Material Purchase',
    'WASHING CONTRACTOR':              'Washing Contractor',
    'VALUE ADDES SERVICES':            'Value Addes Services',
}

# Expense display order / grouping (from the sheet structure)
GROUP_ORDER = ['Direct Expenses', 'Indirect Expenses']

# Alert thresholds
MOM_SPIKE_THRESHOLD   = 30.0   # % — flag single-month spike
SUSTAINED_MONTHS      = 3       # consecutive months rising to flag sustained
HIGH_SHARE_THRESHOLD  = 0.35   # > 35% of location total → flag dominance
NEGATIVE_ALERT        = -40.0  # sudden large drop (possible data entry error)

# Expense mix category keywords for card classification
EXPENSE_CATEGORIES = {
    'Fuel':      ['fuel', 'petrol', 'diesel'],
    'Salary':    ['salary', 'wages', 'staff', 'manpower'],
    'Warranty':  ['warranty', 'warranty claim', 'free service'],
    'Marketing': ['marketing', 'advertis', 'promotion', 'digital'],
    'Utilities': ['electricity', 'water', 'telephone', 'internet', 'utility'],
    'Parts':     ['parts', 'spares', 'accessories', 'lubricant'],
    'Admin':     ['admin', 'stationery', 'office', 'printing', 'postage'],
    'Others':    [],
}

# ═══════════════════════════════════════════════════════════════
#  CSS — Executive Dashboard
# ═══════════════════════════════════════════════════════════════

EXP_CSS = """
/* ── EXP Executive Dashboard ── */
:root{
  --blue:#2563EB;--blue-lt:#EFF6FF;--blue-mid:#BFDBFE;
  --red:#DC2626;--red-lt:#FEF2F2;--red-mid:#FECACA;
  --amber:#D97706;--amber-lt:#FFFBEB;--amber-mid:#FDE68A;
  --green:#16A34A;--green-lt:#F0FDF4;--green-mid:#BBF7D0;
  --neutral:var(--color-text-secondary);--border:#E5E7EB;--surface:#F8FAFC;
  --card:#fff;--text:#111827;--text-sub:#4B5563;--text-xs:var(--color-text-secondary);
}

/* ── Layout ── */
.exp-wrap{max-width:1320px;margin:0 auto;padding:10px 12px}

/* ── Executive Header — compact single line ── */
.exp-exec-hdr{
  background:linear-gradient(135deg,#1E3A8A 0%,#1D4ED8 100%);
  border-radius:10px;padding:10px 16px;margin-bottom:8px;
  display:flex;justify-content:space-between;align-items:center;
  box-shadow:0 2px 8px rgba(30,58,138,.18)
}
.exp-hdr-left{display:flex;align-items:center;gap:12px}
.exp-hdr-eyebrow{font-size:9px;font-weight:700;letter-spacing:.12em;
                 text-transform:uppercase;color:rgba(255,255,255,.55);
                 border-right:1px solid rgba(255,255,255,.2);padding-right:12px;
                 white-space:nowrap}
.exp-hdr-title{font-size:15px;font-weight:700;color:#fff;letter-spacing:-.02em;line-height:1}
.exp-hdr-title em{color:#93C5FD;font-style:normal}
.exp-hdr-sub{font-size:10px;color:rgba(255,255,255,.55);margin-left:8px;white-space:nowrap}
.exp-hdr-right{display:flex;align-items:center;gap:8px;flex-shrink:0}
.exp-hdr-period-pill{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);
                     border-radius:6px;padding:4px 10px;display:flex;align-items:center;gap:8px}
.exp-hdr-period-val{font-size:11px;font-weight:600;color:#fff}
.exp-hdr-period-lbl{font-size:9px;color:rgba(255,255,255,.5);border-left:1px solid rgba(255,255,255,.2);padding-left:8px}

/* ── Alert Banner ── */
.exp-alert-banner{
  background:#FEF2F2;border:1px solid var(--red-mid);border-radius:8px;
  padding:8px 14px;margin-bottom:8px;
  display:flex;align-items:center;gap:10px
}
.exp-alert-banner-icon{font-size:14px;flex-shrink:0}
.exp-alert-banner-body{flex:1;min-width:0;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.exp-alert-banner-head{font-size:11px;font-weight:600;color:var(--red);white-space:nowrap}
.exp-alert-banner-items{display:flex;flex-wrap:wrap;gap:4px}
.exp-alert-pill{font-size:9px;font-weight:500;padding:1px 8px;border-radius:20px;
                white-space:nowrap}
.exp-alert-pill.red{background:var(--red-lt);color:var(--red);border:1px solid var(--red-mid)}
.exp-alert-pill.amber{background:var(--amber-lt);color:var(--amber);border:1px solid var(--amber-mid)}
.exp-alert-pill.blue{background:#EFF6FF;color:#1E40AF;border:1px solid #BFDBFE}
.exp-alert-cnt-badge{flex-shrink:0;font-size:10px;font-weight:700;
                     background:var(--red);color:#fff;border-radius:20px;
                     padding:2px 9px;white-space:nowrap}

/* ── KPI Cards — tighter, denser ── */
.exp-kpi-row{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:8px}
.exp-kpi-card{background:var(--card);border:1px solid var(--border);border-radius:8px;
              padding:10px 12px;position:relative;overflow:hidden}
.exp-kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
                      border-radius:8px 8px 0 0}
.exp-kpi-card.blue::before{background:var(--blue)}
.exp-kpi-card.red::before{background:var(--red)}
.exp-kpi-card.amber::before{background:var(--amber)}
.exp-kpi-card.green::before{background:var(--green)}
.exp-kpi-card.neutral::before{background:#CBD5E1}
.exp-kpi-lbl{font-size:9px;font-weight:600;color:var(--text-xs);
             text-transform:uppercase;letter-spacing:.07em;margin-bottom:5px}
.exp-kpi-val{font-size:19px;font-weight:700;letter-spacing:-.03em;line-height:1;color:var(--text)}
.exp-kpi-val.red{color:var(--red)}.exp-kpi-val.amber{color:var(--amber)}
.exp-kpi-val.green{color:var(--green)}.exp-kpi-val.blue{color:var(--blue)}
.exp-kpi-sub{font-size:9px;color:var(--text-xs);margin-top:3px;line-height:1.3}
.exp-kpi-delta{display:inline-flex;align-items:center;gap:2px;font-size:9px;
               font-weight:700;padding:1px 5px;border-radius:3px;margin-top:3px}
.exp-kpi-delta.up{background:var(--red-lt);color:var(--red)}
.exp-kpi-delta.dn{background:var(--green-lt);color:var(--green)}
.exp-kpi-delta.fl{background:var(--surface);color:var(--neutral)}

/* ── Expense Mix Cards — inline strip ── */
.exp-mix-section{background:var(--card);border:1px solid var(--border);
                 border-radius:8px;padding:10px 14px;margin-bottom:8px}
.exp-mix-title{font-size:11px;font-weight:600;color:var(--text);margin-bottom:8px;
               display:flex;justify-content:space-between;align-items:center}
.exp-mix-title span{font-size:9px;color:var(--text-xs);font-weight:400}
.exp-mix-grid{display:grid;grid-template-columns:repeat(8,1fr);gap:6px}
.exp-mix-card{border:1px solid var(--border);border-radius:7px;padding:8px 6px;
              cursor:pointer;transition:all .15s;text-align:center;background:var(--surface)}
.exp-mix-card:hover{border-color:var(--blue);background:var(--blue-lt);transform:translateY(-1px)}
.exp-mix-card.active{border-color:var(--blue);background:var(--blue-lt)}
.exp-mix-card-icon{font-size:15px;margin-bottom:3px}
.exp-mix-card-name{font-size:9px;font-weight:600;color:var(--text);margin-bottom:2px}
.exp-mix-card-amt{font-size:10px;font-weight:700;color:var(--blue)}
.exp-mix-card-pct{font-size:9px;color:var(--text-xs)}
.exp-mix-card-bar{height:2px;background:var(--border);border-radius:2px;
                  margin-top:5px;overflow:hidden}
.exp-mix-card-fill{height:100%;border-radius:2px;background:var(--blue);transition:width .3s}

/* ── Two-column layout ── */
.exp-two-col{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px}
.exp-three-col{display:grid;grid-template-columns:3fr 2fr;gap:8px;margin-bottom:8px}

/* ── Panel card ── */
.exp-panel-card{background:var(--card);border:1px solid var(--border);
                border-radius:8px;overflow:hidden}
.exp-panel-hdr{background:var(--surface);padding:8px 14px;border-bottom:1px solid var(--border);
               display:flex;justify-content:space-between;align-items:center}
.exp-panel-hdr-title{font-size:11px;font-weight:600;color:var(--text)}
.exp-panel-hdr-sub{font-size:9px;color:var(--text-xs)}
.exp-panel-body{padding:10px 14px}

/* ── Top Cost Centres list — tighter rows ── */
.exp-cost-list{display:flex;flex-direction:column;gap:6px}
.exp-cost-row{display:flex;align-items:center;gap:8px}
.exp-cost-rank{font-size:9px;font-weight:700;color:var(--text-xs);width:14px;
               flex-shrink:0;text-align:center}
.exp-cost-info{flex:1;min-width:0}
.exp-cost-name{font-size:11px;font-weight:600;color:var(--text);
               white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.exp-cost-sub{font-size:9px;color:var(--text-xs)}
.exp-cost-bar-wrap{flex:1;min-width:50px}
.exp-cost-bar-track{height:3px;background:var(--surface);border-radius:2px;overflow:hidden}
.exp-cost-bar-fill{height:100%;border-radius:2px;transition:width .4s}
.exp-cost-amt{font-size:11px;font-weight:700;color:var(--blue);
              white-space:nowrap;flex-shrink:0;min-width:52px;text-align:right}
.exp-cost-delta{font-size:9px;font-weight:600;padding:1px 4px;border-radius:3px;flex-shrink:0}
.exp-cost-delta.up{background:var(--red-lt);color:var(--red)}
.exp-cost-delta.dn{background:var(--green-lt);color:var(--green)}
.exp-cost-delta.fl{background:var(--surface);color:var(--neutral)}

/* ── Donut chart ── */
.exp-donut-wrap{display:flex;flex-direction:column;align-items:center}
.exp-donut-legend{display:flex;flex-direction:column;gap:4px;width:100%;margin-top:8px}
.exp-donut-leg-row{display:flex;align-items:center;gap:6px;font-size:10px}
.exp-donut-leg-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.exp-donut-leg-name{flex:1;color:var(--text-sub)}
.exp-donut-leg-val{font-weight:600;color:var(--text)}
.exp-donut-leg-pct{color:var(--text-xs);width:28px;text-align:right}

/* ── Vendor table ── */
.exp-vendor-list{display:flex;flex-direction:column;gap:0}
.exp-vendor-row{display:flex;align-items:center;gap:8px;padding:5px 0;
                border-bottom:1px solid var(--surface)}
.exp-vendor-row:last-child{border-bottom:none}
.exp-vendor-num{font-size:9px;color:var(--text-xs);width:14px;text-align:center;flex-shrink:0}
.exp-vendor-name{flex:1;font-size:11px;font-weight:500;color:var(--text);min-width:0;
                 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.exp-vendor-cat{font-size:9px;color:var(--text-xs);padding:1px 5px;
                background:var(--surface);border-radius:3px;flex-shrink:0}
.exp-vendor-amt{font-size:11px;font-weight:600;color:var(--text);flex-shrink:0;min-width:52px;text-align:right}

/* ── Monthly trend chart ── */
.exp-trend-wrap{background:var(--card);border:1px solid var(--border);
                border-radius:8px;padding:12px 14px;margin-bottom:8px}
.exp-trend-title{font-size:11px;font-weight:600;color:var(--text);margin-bottom:10px;
                 display:flex;justify-content:space-between;align-items:center}
.exp-trend-legend{display:flex;gap:12px;font-size:10px;color:var(--text-sub)}
.exp-trend-leg-item{display:flex;align-items:center;gap:4px}
.exp-trend-leg-dot{width:10px;height:3px;border-radius:2px}
.exp-chart-area{width:100%;height:140px;position:relative}
.exp-chart-svg{width:100%;height:100%;overflow:visible}

/* ── Location analysis ── */
.exp-loc-analysis{background:var(--card);border:1px solid var(--border);
                  border-radius:8px;margin-bottom:8px;overflow:hidden}
.exp-loc-analysis-hdr{background:var(--surface);padding:8px 14px;border-bottom:1px solid var(--border);
                      display:flex;justify-content:space-between;align-items:center}
.exp-loc-tbl{width:100%;border-collapse:collapse;font-size:12px}
.exp-loc-tbl th{background:var(--surface);font-size:9px;font-weight:600;text-transform:uppercase;
                letter-spacing:.06em;color:var(--text-xs);padding:7px 12px;
                border-bottom:1px solid var(--border);white-space:nowrap;text-align:right}
.exp-loc-tbl th:first-child{text-align:left}
.exp-loc-tbl td{padding:7px 12px;border-bottom:1px solid #F3F4F6;
                vertical-align:middle;text-align:right;color:#374151}
.exp-loc-tbl td:first-child{text-align:left}
.exp-loc-tbl tr.exp-loc-main-row{cursor:pointer}
.exp-loc-tbl tr.exp-loc-main-row:hover td{background:var(--surface)}
.exp-loc-tbl tr.exp-loc-expand-row{display:none;background:#FAFBFD}
.exp-loc-tbl tr.exp-loc-expand-row td{padding:10px 12px;border-bottom:1px solid var(--border)}
.exp-loc-tbl tr.exp-tot-row td{background:#EEF2F8;font-weight:700;
                                border-top:2px solid var(--border)}
.exp-loc-name{font-weight:600;color:var(--blue);font-size:12px}
.exp-loc-code{font-size:9px;color:var(--text-xs)}
.exp-loc-expand-inner{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.exp-loc-expand-kpi{background:var(--card);border:1px solid var(--border);
                    border-radius:6px;padding:8px 10px}
.exp-loc-expand-kpi-lbl{font-size:9px;font-weight:600;text-transform:uppercase;
                         letter-spacing:.05em;color:var(--text-xs);margin-bottom:3px}
.exp-loc-expand-kpi-val{font-size:15px;font-weight:700;color:var(--text)}
.exp-loc-expand-kpi-sub{font-size:9px;color:var(--text-xs);margin-top:1px}
.exp-loc-alert-list{margin-top:6px;display:flex;flex-direction:column;gap:3px}
.exp-loc-alert-item{display:flex;align-items:flex-start;gap:6px;font-size:10px;
                    padding:4px 8px;border-radius:5px;background:var(--card);
                    border:1px solid var(--border)}
.exp-expand-arr{display:inline-block;font-size:9px;color:var(--text-xs);
                margin-right:5px;transition:transform .15s}

/* ── Transaction drilldown ── */
.exp-txn-wrap{background:var(--card);border:1px solid var(--border);
              border-radius:8px;margin-bottom:8px;overflow:hidden}
.exp-txn-tbl{width:100%;border-collapse:collapse;font-size:12px}
.exp-txn-tbl th{background:var(--surface);font-size:9px;font-weight:600;text-transform:uppercase;
                letter-spacing:.06em;color:var(--text-xs);padding:7px 12px;
                border-bottom:1px solid var(--border);white-space:nowrap;text-align:right}
.exp-txn-tbl th:first-child,.exp-txn-tbl th:nth-child(2){text-align:left}
.exp-txn-tbl td{padding:6px 12px;border-bottom:1px solid #F3F4F6;
                vertical-align:middle;text-align:right;color:#374151}
.exp-txn-tbl td:first-child,.exp-txn-tbl td:nth-child(2){text-align:left}
.exp-txn-cat-pill{font-size:9px;font-weight:500;padding:1px 6px;border-radius:3px;
                  background:var(--blue-lt);color:var(--blue);border:1px solid var(--blue-mid)}
.exp-txn-hi{font-weight:700;color:var(--red)}

/* ── Insights — two-column grid ── */
.exp-insights-wrap{background:var(--card);border:1px solid var(--border);
                   border-radius:8px;margin-bottom:8px;overflow:hidden}
.exp-insights-hdr{background:linear-gradient(90deg,#1E3A8A,#1D4ED8);
                  padding:9px 14px;display:flex;justify-content:space-between;align-items:center}
.exp-insights-hdr-title{font-size:11px;font-weight:700;color:#fff;letter-spacing:.01em}
.exp-insights-hdr-sub{font-size:9px;color:rgba(255,255,255,.6)}
.exp-insights-list{padding:6px 12px 10px;
                   display:grid;grid-template-columns:1fr 1fr;gap:0 24px}
.exp-insight-row{display:flex;align-items:flex-start;gap:8px;padding:7px 0;
                 border-bottom:1px solid var(--surface)}
.exp-insight-row:last-child{border-bottom:none}
.exp-insight-rank{font-size:9px;font-weight:700;color:#fff;
                  width:17px;height:17px;border-radius:50%;background:var(--blue);
                  display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}
.exp-insight-icon{font-size:13px;flex-shrink:0;margin-top:1px}
.exp-insight-body{flex:1;min-width:0}
.exp-insight-head{font-size:11px;font-weight:600;color:var(--text);margin-bottom:1px;line-height:1.3}
.exp-insight-detail{font-size:10px;color:var(--text-sub);line-height:1.4}
.exp-insight-impact{font-size:8px;font-weight:700;padding:1px 6px;border-radius:3px;
                    letter-spacing:.05em;flex-shrink:0;align-self:flex-start;margin-top:2px;white-space:nowrap}
.exp-insight-impact.hi{background:var(--red-lt);color:var(--red)}
.exp-insight-impact.mid{background:var(--amber-lt);color:var(--amber)}
.exp-insight-impact.lo{background:var(--green-lt);color:var(--green)}

/* ── Action Panel — compact grid ── */
.exp-action-wrap{background:#F0F6FF;border:1px solid #C7DCFA;border-radius:8px;
                 padding:10px 14px;margin-bottom:8px}
.exp-action-title{font-size:11px;font-weight:700;color:#1E3A8A;margin-bottom:8px;
                  display:flex;align-items:center;justify-content:space-between}
.exp-action-title-right{font-size:9px;font-weight:400;color:var(--blue)}
.exp-action-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:7px}
.exp-action-card{background:var(--card);border:1px solid var(--border);border-radius:7px;
                 padding:9px 11px;display:flex;align-items:flex-start;gap:8px}
.exp-action-icon{font-size:15px;flex-shrink:0;margin-top:1px}
.exp-action-body{flex:1;min-width:0}
.exp-action-trigger{font-size:10px;font-weight:700;color:var(--text);margin-bottom:3px}
.exp-action-steps{font-size:9px;color:var(--text-sub);line-height:1.55}
.exp-action-steps span{display:block;padding-left:10px;position:relative}
.exp-action-steps span::before{content:'→';position:absolute;left:0;color:var(--blue)}
.exp-action-badge{font-size:8px;font-weight:700;padding:1px 5px;border-radius:3px;letter-spacing:.04em;
                  flex-shrink:0;align-self:flex-start;margin-top:1px;white-space:nowrap}
.exp-action-badge.hi{background:var(--red-lt);color:var(--red)}
.exp-action-badge.mid{background:var(--amber-lt);color:var(--amber)}

/* ── Loc selector bar ── */
.exp-loc-bar{background:var(--card);border:1px solid var(--border);border-radius:12px;
             padding:9px 16px;margin-bottom:12px;
             display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.exp-loc-bar label{font-size:11px;font-weight:500;color:var(--text-sub);white-space:nowrap}
.exp-loc-bar select{font-size:13px;font-family:inherit;padding:6px 10px;
                    border:1px solid var(--border);border-radius:10px;
                    background:var(--surface);color:var(--text);outline:none;cursor:pointer;flex:1;max-width:400px}
.exp-loc-bar select:focus{border-color:var(--blue)}

/* ── Page nav pills ── */
.exp-page-nav{display:flex;justify-content:center;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.epnav{padding:7px 20px;border-radius:20px;font-size:12px;font-weight:500;
       cursor:pointer;user-select:none;border:1px solid var(--border);
       background:var(--card);color:var(--text-sub);transition:background .15s,color .15s}
.epnav.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.epnav:hover:not(.on){background:#F0F4FA;color:var(--blue)}

/* ── Location section ── */
.exp-loc-sec{display:none}
.exp-loc-heading{background:var(--card);border:1px solid var(--border);
                 border-left:3px solid var(--blue);border-radius:0 12px 12px 0;
                 padding:10px 16px;margin-bottom:12px;
                 display:flex;justify-content:space-between;align-items:center}
.exp-loc-heading-name{font-size:13px;font-weight:600;color:var(--blue)}
.exp-loc-heading-sub{font-size:11px;color:var(--text-xs);margin-top:2px}

/* ── KPI row (location-level) ── */
.exp-kpi-row-loc{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
                 gap:8px;margin-bottom:14px}
.exp-kpi{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px 16px}
.exp-kpi-lbl-sm{font-size:10px;font-weight:500;color:var(--text-xs);text-transform:uppercase;
                letter-spacing:.05em;margin-bottom:8px}
.exp-kpi-val-sm{font-size:20px;font-weight:500;line-height:1}
.exp-kpi-val-sm.hi{color:var(--green)}.exp-kpi-val-sm.mid{color:var(--amber)}
.exp-kpi-val-sm.lo{color:var(--red)}.exp-kpi-val-sm.neu{color:var(--text)}
.exp-kpi-sub-sm{font-size:10px;color:var(--text-xs);margin-top:4px}

/* ── Section card ── */
.exp-sec{background:var(--card);border:1px solid var(--border);border-radius:14px;
         margin-bottom:12px;overflow:hidden}
.exp-sec-hdr{background:#F8F9FB;padding:9px 16px;font-size:12px;font-weight:500;
             display:flex;justify-content:space-between;align-items:center;
             flex-wrap:wrap;gap:6px;border-bottom:1px solid var(--border);cursor:pointer;
             user-select:none}
.exp-sec-hdr:hover{background:#F0F4FA}
.exp-sec-body{overflow-x:auto}

/* ── Group row ── */
.exp-grp-row{background:#EEF3FA;cursor:pointer;user-select:none}
.exp-grp-row:hover{background:#E3EDF8}
.exp-grp-row td{padding:8px 12px;font-size:12px;font-weight:500;color:var(--blue);
                border-bottom:1px solid #D6E4F5}
.exp-name-row{background:var(--card);cursor:pointer;user-select:none}
.exp-name-row:hover{background:#F8F9FB}
.exp-name-row td{padding:7px 12px;font-size:12px;color:#374151;border-bottom:1px solid var(--surface)}
.exp-tot-row td{padding:8px 12px;font-size:12px;font-weight:600;color:var(--text);
                background:#F0F4F8;border-top:2px solid var(--border)}

/* ── MoM cell colouring ── */
.mom-hi{color:var(--green);font-weight:600}.mom-mid{color:var(--amber);font-weight:500}
.mom-lo{color:var(--red);font-weight:600}.mom-neu{color:var(--text-sub)}
.mom-spike{background:var(--red-lt);color:#991B1B;font-weight:700;border-radius:4px;
           padding:1px 5px;white-space:nowrap}
.mom-drop{background:var(--green-lt);color:#065F46;font-weight:600;border-radius:4px;
          padding:1px 5px;white-space:nowrap}
.mom-blank{color:#D1D5DB}

/* ── Amount cells ── */
td.amt{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
th.amt{text-align:right}
.amt-total{font-weight:600}

/* ── Arrow indicator ── */
.arr{display:inline-block;width:14px;font-size:9px;color:var(--text-xs);margin-right:3px;
     transition:transform .15s}

/* ── Alert section ── */
.exp-alert-sec{background:var(--card);border:1px solid var(--red-mid);border-radius:14px;
               margin-bottom:12px;overflow:hidden}
.exp-alert-hdr{background:var(--red-lt);padding:10px 16px;display:flex;
               justify-content:space-between;align-items:center;
               border-bottom:1px solid var(--red-mid)}
.exp-alert-title{font-size:12px;font-weight:500;color:#991B1B;
                 display:flex;align-items:center;gap:8px}
.exp-alert-dot{width:8px;height:8px;border-radius:50%;background:#EF4444;
               animation:expulse 1.8s infinite}
@keyframes expulse{0%,100%{opacity:1}50%{opacity:.35}}
.exp-alert-cnt{font-size:10px;font-weight:500;padding:3px 10px;border-radius:20px;
               background:#FEE2E2;color:#991B1B;border:1px solid var(--red-mid)}
.exp-alert-ok{font-size:10px;color:#065F46;background:var(--green-lt);
              padding:3px 10px;border-radius:20px;border:1px solid var(--green-mid)}
.exp-alert-list{padding:10px 14px;display:flex;flex-direction:column;gap:6px}
.exp-alert-card{background:#FFF7F7;border:1px solid var(--red-mid);border-radius:10px;
                padding:10px 14px;display:flex;align-items:flex-start;gap:10px}
.exp-alert-card.warn{background:var(--amber-lt);border-color:var(--amber-mid)}
.exp-alert-card.info{background:#EFF6FF;border-color:#BFDBFE}
.exp-alert-icon{font-size:16px;flex-shrink:0;margin-top:1px}
.exp-alert-body{flex:1;min-width:0}
.exp-alert-head{font-size:12px;font-weight:500;color:var(--text);margin-bottom:2px}
.exp-alert-detail{font-size:11px;color:var(--text-sub);line-height:1.4}
.exp-alert-badge{display:inline-block;font-size:10px;font-weight:600;padding:2px 8px;
                 border-radius:20px;white-space:nowrap;margin-left:6px}
.exp-alert-badge.red{background:#FEE2E2;color:#991B1B}
.exp-alert-badge.amber{background:#FEF3C7;color:#92400E}
.exp-alert-badge.blue{background:#DBEAFE;color:#1E40AF}
.exp-alert-badge.green{background:var(--green-lt);color:#065F46}

/* ── Dashboard table ── */
.exp-dash-wrap{overflow-x:auto}
.exp-dash-tbl{width:100%;border-collapse:collapse;font-size:12px}
.exp-dash-tbl th{background:#F8F9FB;font-size:10px;font-weight:500;
                 text-transform:uppercase;letter-spacing:.05em;color:var(--text-xs);
                 padding:8px 12px;text-align:right;border-bottom:1px solid var(--border);
                 white-space:nowrap}
.exp-dash-tbl th:first-child{text-align:left}
.exp-dash-tbl td{padding:8px 12px;border-bottom:1px solid var(--surface);
                 vertical-align:middle;text-align:right;color:#374151}
.exp-dash-tbl td:first-child{text-align:left;font-weight:500}
.exp-dash-tbl tr:hover td{background:#F8F9FB;cursor:pointer}
.exp-dash-tbl tr.dash-tot td{background:#F0F4F8;font-weight:600;
                              border-top:2px solid var(--border)}
.dash-loc-name{font-weight:500;color:var(--blue);font-size:12px}
.dash-loc-sub{font-size:10px;color:var(--text-xs);margin-top:1px}

/* ── Bar cell ── */
.bar-cell{display:flex;align-items:center;gap:8px;min-width:140px}
.bar-track{flex:1;height:5px;background:#F0F4F8;border-radius:3px;overflow:hidden}
.bar-fill{height:100%;border-radius:3px}
.bar-fill.hi{background:var(--green)}.bar-fill.mid{background:var(--amber)}
.bar-fill.lo{background:var(--red)}
.bar-label{font-size:11px;font-weight:500;white-space:nowrap;min-width:70px;text-align:right}
.bar-label.hi{color:var(--green)}.bar-label.mid{color:var(--amber)}
.bar-label.lo{color:var(--red)}

/* ── Sparkline ── */
.spark{display:inline-flex;align-items:flex-end;gap:1px;height:18px;vertical-align:middle}
.spark-bar{width:4px;border-radius:1px 1px 0 0;flex-shrink:0}

/* ── Trend pill ── */
.trend-up{color:var(--red);font-size:10px;font-weight:600}
.trend-dn{color:var(--green);font-size:10px;font-weight:600}
.trend-fl{color:var(--text-xs);font-size:10px}

/* ── Legend ── */
.exp-legend{display:flex;gap:14px;padding:7px 16px;font-size:10px;color:var(--text-xs);
            border-top:1px solid var(--surface);flex-wrap:wrap}

/* ── Tabs ── */
.exp-tab-row{display:flex;gap:0;background:var(--card);border:1px solid var(--border);
             border-radius:12px;overflow:hidden;margin-bottom:12px}
.exp-tab{flex:1;padding:8px 14px;font-size:11px;font-weight:500;
         text-align:center;cursor:pointer;color:var(--text-sub);
         border-right:1px solid var(--border);transition:background .12s,color .12s;
         user-select:none}
.exp-tab:last-child{border-right:none}
.exp-tab.on{background:var(--blue);color:#fff}
.exp-tab:hover:not(.on){background:#F0F4FA;color:var(--blue)}
.exp-panel{display:none}.exp-panel.on{display:block}

/* ── Section divider ── */
.exp-section-label{font-size:10px;font-weight:700;letter-spacing:.1em;
                   text-transform:uppercase;color:var(--text-xs);
                   padding:8px 2px 6px;margin-bottom:4px;
                   border-bottom:1px solid var(--border);margin-bottom:10px}

/* ── Responsive ── */
@media(max-width:900px){
  .exp-kpi-row{grid-template-columns:repeat(3,1fr)}
  .exp-mix-grid{grid-template-columns:repeat(4,1fr)}
  .exp-two-col,.exp-three-col{grid-template-columns:1fr}
}
@media(max-width:640px){
  .exp-wrap{padding:10px 8px}
  .exp-exec-hdr{flex-direction:column;gap:10px;padding:14px 16px}
  .exp-kpi-row{grid-template-columns:repeat(2,1fr);gap:6px}
  .exp-mix-grid{grid-template-columns:repeat(2,1fr)}
  .exp-sec-body{overflow-x:auto;-webkit-overflow-scrolling:touch}
  .exp-dash-tbl{min-width:480px}
}
@media print{
  .exp-loc-bar,.exp-page-nav{display:none!important}
  .exp-loc-sec{display:block!important}
}
"""

# ═══════════════════════════════════════════════════════════════
#  JAVASCRIPT
# ═══════════════════════════════════════════════════════════════

EXP_JS = """
/* ── Toggle group rows ── */
function expTog(id){
  var rows=document.querySelectorAll('.ep-'+id);
  var arrow=document.getElementById('earr_'+id);
  var hidden=rows.length>0&&rows[0].style.display==='none';
  rows.forEach(function(r){r.style.display=hidden?'':'none';});
  if(arrow)arrow.textContent=hidden?'\\u25BC':'\\u25B6';
}

/* ── Switch location in selector ── */
function expSwitchLoc(val){
  document.querySelectorAll('.exp-loc-sec').forEach(function(s){s.style.display='none';});
  if(val){
    var el=document.getElementById('els_'+val);
    if(el)el.style.display='block';
    var pn=document.querySelector('.exp-page-nav');
    if(pn)pn.style.display=(val==='__ALL__'?'none':'');
    if(val!=='__ALL__'){
      var active=document.querySelector('.epnav.on');
      if(active)expShowPanel(active.dataset.ep,val);
    }
  }
}

/* ── Show panel within a location tab ── */
function expShowPanel(pid,lid){
  if(!lid){
    var sel=document.getElementById('exp-loc-sel');
    lid=sel?sel.value:'';
  }
  document.querySelectorAll('.epnav').forEach(function(b){b.classList.remove('on');});
  var b=document.querySelector('.epnav[data-ep="'+pid+'"]');
  if(b)b.classList.add('on');
  if(lid&&lid!=='__ALL__'){
    ['mom','alerts'].forEach(function(k){
      var el=document.getElementById('ep_'+lid+'_'+k);
      if(el)el.style.display=(k===pid?'block':'none');
    });
  }
}

/* ── Jump to location from dashboard click ── */
function expGoto(lid){
  var sel=document.getElementById('exp-loc-sel');
  if(sel){sel.value=lid;expSwitchLoc(lid);}
}

/* ── Cross-navigation placeholder for Dealer Audit and Revenue Leakage ── */
function expNavTo(module,lid){
  // Placeholder for future routing implementation
  // module: 'dealer_audit' or 'revenue_leakage'
  // lid: optional location ID for context
  console.log('Navigation to module:',module,'with location:',lid);
  alert('Cross-navigation to '+module+' will be implemented in future routing.');
}

/* ── Expense mix card filter ── */
function expMixFilter(cat){
  document.querySelectorAll('.exp-mix-card').forEach(function(c){
    c.classList.toggle('active',c.dataset.cat===cat);
  });
}

/* ── Location analysis expand row ── */
function expLocToggle(lid){
  var row=document.getElementById('exp-expand-'+lid);
  var arr=document.getElementById('exp-expand-arr-'+lid);
  if(!row)return;
  var open=row.style.display==='table-row';
  row.style.display=open?'none':'table-row';
  if(arr)arr.style.transform=open?'':'rotate(90deg)';
}

/* ── Animate bars on load ── */
function expAnimateBars(){
  document.querySelectorAll('[data-bar-w]').forEach(function(el){
    setTimeout(function(){el.style.width=el.dataset.barW+'%';},100);
  });
}

/* ── Donut chart builder ── */
function expBuildDonut(canvasId,data){
  var cvs=document.getElementById(canvasId);
  if(!cvs)return;
  var ctx=cvs.getContext('2d');
  var W=cvs.width,H=cvs.height,cx=W/2,cy=H/2,r=Math.min(W,H)/2-8,ri=r*0.6;
  var total=data.reduce(function(a,d){return a+d.val;},0);
  var angle=-Math.PI/2;
  data.forEach(function(d){
    var sweep=(d.val/total)*Math.PI*2;
    ctx.beginPath();
    ctx.moveTo(cx,cy);
    ctx.arc(cx,cy,r,angle,angle+sweep);
    ctx.closePath();
    ctx.fillStyle=d.color;
    ctx.fill();
    angle+=sweep;
  });
  ctx.beginPath();
  ctx.arc(cx,cy,ri,0,Math.PI*2);
  ctx.fillStyle='#fff';
  ctx.fill();
}

/* ── Trend line chart builder ── */
function expBuildTrend(svgId,actuals,labels){
  var svg=document.getElementById(svgId);
  if(!svg)return;
  var W=svg.clientWidth||svg.parentElement.clientWidth||600,H=140;
  svg.setAttribute('viewBox','0 0 '+W+' '+H);
  if(!actuals||actuals.length<2)return;
  var mx=Math.max.apply(null,actuals)||1;
  var mn=0;
  var pad={t:10,r:10,b:24,l:44};
  var cw=W-pad.l-pad.r,ch=H-pad.t-pad.b;
  var n=actuals.length;
  var pts=actuals.map(function(v,i){
    return {x:pad.l+(i/(n-1))*cw,y:pad.t+ch-(((v-mn)/(mx-mn))*ch)};
  });
  /* Grid lines */
  [0,.25,.5,.75,1].forEach(function(f){
    var y=pad.t+ch-(f*ch);
    var el=document.createElementNS('http://www.w3.org/2000/svg','line');
    el.setAttribute('x1',pad.l);el.setAttribute('x2',pad.l+cw);
    el.setAttribute('y1',y);el.setAttribute('y2',y);
    el.setAttribute('stroke','#E8ECF0');el.setAttribute('stroke-width','1');
    svg.appendChild(el);
  });
  /* Fill area */
  var fillD='M'+pts[0].x+','+pts[0].y;
  pts.forEach(function(p){fillD+=' L'+p.x+','+p.y;});
  fillD+=' L'+pts[pts.length-1].x+','+(pad.t+ch)+' L'+pts[0].x+','+(pad.t+ch)+' Z';
  var fill=document.createElementNS('http://www.w3.org/2000/svg','path');
  fill.setAttribute('d',fillD);
  fill.setAttribute('fill','rgba(24,95,165,.08)');
  svg.appendChild(fill);
  /* Line */
  var lineD='M'+pts[0].x+','+pts[0].y;
  pts.forEach(function(p){lineD+=' L'+p.x+','+p.y;});
  var line=document.createElementNS('http://www.w3.org/2000/svg','path');
  line.setAttribute('d',lineD);line.setAttribute('fill','none');
  line.setAttribute('stroke','#185FA5');line.setAttribute('stroke-width','2.5');
  line.setAttribute('stroke-linejoin','round');line.setAttribute('stroke-linecap','round');
  svg.appendChild(line);
  /* Dots */
  pts.forEach(function(p,i){
    var dot=document.createElementNS('http://www.w3.org/2000/svg','circle');
    dot.setAttribute('cx',p.x);dot.setAttribute('cy',p.y);dot.setAttribute('r','3.5');
    dot.setAttribute('fill','#185FA5');dot.setAttribute('stroke','#fff');
    dot.setAttribute('stroke-width','2');
    svg.appendChild(dot);
  });
  /* X labels (last 6) */
  var step=Math.ceil(n/6);
  labels.forEach(function(lbl,i){
    if(i%step!==0&&i!==n-1)return;
    var tx=document.createElementNS('http://www.w3.org/2000/svg','text');
    tx.setAttribute('x',pts[i].x);tx.setAttribute('y',H-4);
    tx.setAttribute('text-anchor','middle');tx.setAttribute('font-size','9');
    tx.setAttribute('fill','var(--color-text-secondary)');tx.textContent=lbl;
    svg.appendChild(tx);
  });
}

window.addEventListener('load',function(){
  var s=document.getElementById('exp-loc-sel');
  if(s&&s.options.length>0){
    s.value=s.options[0].value;
    expSwitchLoc(s.options[0].value);
  }
  expShowPanel('mom');
  expAnimateBars();

  /* Render donut if data exists */
  if(typeof window._expDonutData!=='undefined'){
    expBuildDonut('exp-donut-cvs',window._expDonutData);
  }
  /* Render trend if data exists */
  if(typeof window._expTrendActuals!=='undefined'){
    expBuildTrend('exp-trend-svg',window._expTrendActuals,window._expTrendLabels);
  }
});
"""

# ═══════════════════════════════════════════════════════════════
#  DATA PREPARATION  (UNCHANGED)
# ═══════════════════════════════════════════════════════════════

def prepare_exp_data(df_raw):
    """
    Clean and prepare the EXP sheet dataframe.
    Returns enriched DataFrame with computed MoM% per location+expense.
    """
    df = df_raw.copy()
    df = df.dropna(subset=['Location', 'Month Name', 'Expenses Name'])
    df['Expenses Rs.'] = pd.to_numeric(df['Expenses Rs.'], errors='coerce').fillna(0)
    df['Expenses Name'] = df['Expenses Name'].str.strip().replace(EXP_NAME_MAP)
    df['Location']      = df['Location'].str.strip()

    # Filter to valid months
    valid_months = set(MONTH_ORDER)
    df = df[df['Month Name'].isin(valid_months)]
    df['Month Name'] = pd.Categorical(df['Month Name'], categories=MONTH_ORDER, ordered=True)
    df = df.sort_values(['Location', 'Expenses Name', 'Month Name'])

    # Recompute MoM% (override sheet values since Apr-25 = NaN)
    df['MoM_Calc'] = df.groupby(['Location', 'Expenses Name'])['Expenses Rs.'].transform(
        lambda x: ((x - x.shift(1)) / x.shift(1).abs().replace(0, np.nan) * 100).round(1)
    )

    # Expense group fallback
    if 'Expenses Group' not in df.columns:
        df['Expenses Group'] = 'Indirect Expenses'
    df['Expenses Group'] = df['Expenses Group'].fillna('Indirect Expenses')

    return df


def get_available_months(df):
    """Return sorted list of months present in data."""
    months = [m for m in MONTH_ORDER if m in df['Month Name'].values]
    return months


def pivot_for_location(df, loc):
    """Return wide pivot: expense_name × month → amount, plus MoM% companion."""
    sub = df[df['Location'] == loc].copy()
    months = get_available_months(sub)

    amt_pivot = sub.pivot_table(
        index=['Expenses Group', 'Expenses Name'],
        columns='Month Name',
        values='Expenses Rs.',
        aggfunc='sum'
    ).fillna(0)

    mom_pivot = sub.pivot_table(
        index=['Expenses Group', 'Expenses Name'],
        columns='Month Name',
        values='MoM_Calc',
        aggfunc='mean'
    )
    return amt_pivot, mom_pivot, months


# ═══════════════════════════════════════════════════════════════
#  ALERT ENGINE  (UNCHANGED)
# ═══════════════════════════════════════════════════════════════

_ALERTS_CACHE = {}

def _precompute_alerts(df):
    alerts_dict = {loc: [] for loc in df['Location'].unique()}
    
    global_months = get_available_months(df)
    if len(global_months) < 2:
        return alerts_dict
        
    sub = df[df['Month Name'].isin(global_months)].copy()
    
    loc_months_dict = {}
    for loc, grp in sub.groupby('Location'):
        m_list = [m for m in global_months if m in grp['Month Name'].values]
        loc_months_dict[loc] = m_list
        
    amt_pvt = sub.pivot_table(index=['Location', 'Expenses Name'], columns='Month Name', values='Expenses Rs.', aggfunc='sum')
    mom_pvt = sub.pivot_table(index=['Location', 'Expenses Name'], columns='Month Name', values='MoM_Calc', aggfunc='mean')
    
    exists_mask = ~amt_pvt.isna()
    amt_pvt = amt_pvt.fillna(0)
    
    for loc in amt_pvt.index.levels[0]:
        loc_m = loc_months_dict.get(loc, [])
        if len(loc_m) < 2:
            continue
            
        l_m = loc_m[-1]
        p_m = loc_m[-2]
        
        try:
            loc_amt = amt_pvt.loc[loc]
            loc_mom = mom_pvt.loc[loc]
            loc_exist = exists_mask.loc[loc]
        except KeyError:
            continue
            
        last_amt = loc_amt[l_m] if l_m in loc_amt.columns else pd.Series(0, index=loc_amt.index)
        prev_amt = loc_amt[p_m] if p_m in loc_amt.columns else pd.Series(0, index=loc_amt.index)
        last_mom = loc_mom[l_m] if l_m in loc_mom.columns else pd.Series(np.nan, index=loc_mom.index)
        
        # 1. Spike Alert
        spike_mask = (last_mom >= MOM_SPIKE_THRESHOLD) & (last_amt > 5000) & last_mom.notna()
        for exp_name, is_true in spike_mask.items():
            if is_true:
                mom_val = last_mom.loc[exp_name]
                amt_val = last_amt.loc[exp_name]
                alerts_dict[loc].append({
                    'type': 'spike', 'icon': '⚠️',
                    'head': f'{exp_name} — Expense Spike in {l_m}',
                    'detail': f'Rose {mom_val:+.1f}% vs {p_m}. Amount: ₹{amt_val:,.0f}',
                    'badge_text': f'+{mom_val:.0f}%', 'badge_cls': 'red'
                })
                
        # 2. Sustained growth
        if len(loc_m) >= SUSTAINED_MONTHS:
            last_n_months = loc_m[-SUSTAINED_MONTHS:]
            mom_last_n = loc_mom[last_n_months]
            valid_sustained = mom_last_n.dropna(how='any')
            all_positive = (valid_sustained > 0).all(axis=1)
            
            first_of_last_n = last_n_months[0]
            amt_last_n = loc_amt[last_n_months]
            
            for exp_name, is_pos in all_positive.items():
                if is_pos:
                    end_amt = amt_last_n.loc[exp_name, l_m]
                    start_amt = amt_last_n.loc[exp_name, first_of_last_n]
                    if start_amt != 0:
                        total_growth = ((end_amt / start_amt) - 1) * 100
                        if total_growth > 10:
                            alerts_dict[loc].append({
                                'type': 'sustained', 'icon': '📈',
                                'head': f'{exp_name} — Rising for {SUSTAINED_MONTHS} Consecutive Months',
                                'detail': f'Grew {total_growth:.1f}% over last {SUSTAINED_MONTHS} months. Review if controllable.',
                                'badge_text': f'↑ {SUSTAINED_MONTHS}m streak', 'badge_cls': 'amber'
                            })
                            
        # 3. High share
        loc_total = last_amt.sum()
        if loc_total > 0:
            for exp_name, amt in last_amt.items():
                share = amt / loc_total
                if share >= HIGH_SHARE_THRESHOLD and amt > 10000:
                    alerts_dict[loc].append({
                        'type': 'share', 'icon': '🔍',
                        'head': f'{exp_name} — High Expense Share in {l_m}',
                        'detail': f'Represents {share*100:.1f}% of total location expenses (₹{amt:,.0f} of ₹{loc_total:,.0f})',
                        'badge_text': f'{share*100:.0f}% share', 'badge_cls': 'amber'
                    })
                    
        # 4. Sudden large drop
        drop_mask = (last_mom <= NEGATIVE_ALERT) & (prev_amt > 50000) & last_mom.notna()
        for exp_name, is_true in drop_mask.items():
            if is_true:
                mom_val = last_mom.loc[exp_name]
                p_amt = prev_amt.loc[exp_name]
                alerts_dict[loc].append({
                    'type': 'drop', 'icon': '📉',
                    'head': f'{exp_name} — Large Drop in {l_m}',
                    'detail': f'Fell {mom_val:.1f}% vs {p_m}. Prev: ₹{p_amt:,.0f}. Verify data.',
                    'badge_text': f'{mom_val:.0f}%', 'badge_cls': 'blue'
                })
                
        # 5. Zero-expense months
        last_2_months = loc_m[-2:]
        for exp_name in loc_amt.index:
            l_amt = last_amt.loc[exp_name]
            l_exist = loc_exist.loc[exp_name, l_m] if l_m in loc_exist.columns else False
            
            if l_exist and l_amt == 0:
                p_amts = loc_amt.loc[exp_name, last_2_months]
                if any(p_amts > 20000):
                    max_p = max(p_amts)
                    alerts_dict[loc].append({
                        'type': 'zero', 'icon': '🔶',
                        'head': f'{exp_name} — Zero in {l_m}',
                        'detail': f'Was ₹{max_p:,.0f} recently. May be missing entry.',
                        'badge_text': '₹0 posted', 'badge_cls': 'amber'
                    })

    return alerts_dict

from services.aggregation_cache import _get_df_hash

def generate_alerts(df, loc):
    """
    AI-style alerts for a location.
    Returns list of dicts: {type, icon, head, detail, badge_text, badge_cls}
    """
    df_id = _get_df_hash(df)
    
    # Simple cache eviction to prevent memory bloat over multiple streams
    if len(_ALERTS_CACHE) > 5:
        keys = list(_ALERTS_CACHE.keys())[:-5]
        for k in keys:
            del _ALERTS_CACHE[k]
            
    if df_id not in _ALERTS_CACHE:
        _ALERTS_CACHE[df_id] = _precompute_alerts(df)
        
    return _ALERTS_CACHE[df_id].get(loc, [])

_EXP_DASH_CACHE = {}

def _get_vectorized_exp_data(df, last_m):
    """F2: Vectorized Precomputations for the Dashboard and KPIs."""
    df_id = f"{_get_df_hash(df)}_{last_m}"
    if len(_EXP_DASH_CACHE) > 5:
        keys = list(_EXP_DASH_CACHE.keys())[:-5]
        for k in keys:
            del _EXP_DASH_CACHE[k]
            
    if df_id not in _EXP_DASH_CACHE:
        loc_totals = df.groupby(['Location', 'Month Name'])['Expenses Rs.'].sum().unstack(fill_value=0)
        loc_ytd = df.groupby('Location')['Expenses Rs.'].sum()
        
        last_m_df = df[df['Month Name'] == last_m]
        top_exp_dict = {}
        if not last_m_df.empty:
            loc_exp_sum = last_m_df.groupby(['Location', 'Expenses Name'])['Expenses Rs.'].sum().reset_index()
            loc_exp_sum_sorted = loc_exp_sum.sort_values(by=['Location', 'Expenses Rs.'], ascending=[True, False])
            top_expenses = loc_exp_sum_sorted.drop_duplicates(subset=['Location'])
            top_exp_dict = top_expenses.set_index('Location').apply(
                lambda row: (row['Expenses Name'], row['Expenses Rs.']), axis=1
            ).to_dict()
            
        _EXP_DASH_CACHE[df_id] = {
            'loc_totals': loc_totals,
            'loc_ytd': loc_ytd,
            'top_exp_dict': top_exp_dict
        }
        
    return _EXP_DASH_CACHE[df_id]


# ═══════════════════════════════════════════════════════════════
#  FORMATTERS  (UNCHANGED)
# ═══════════════════════════════════════════════════════════════

from ui.formatters import fmt_inr_exp as fmt_inr, fmt_inr_full_exp as fmt_inr_full

def mom_cell(v, show_blank=True):
    """Return TD HTML for a MoM% value."""
    try:
        f = float(v)
        if pd.isna(f):
            return '<td class="amt mom-blank">—</td>' if show_blank else '<td class="amt"></td>'
        if f >= MOM_SPIKE_THRESHOLD:
            return f'<td class="amt"><span class="mom-spike">▲ {f:+.1f}%</span></td>'
        elif f <= NEGATIVE_ALERT:
            return f'<td class="amt"><span class="mom-drop">▼ {f:.1f}%</span></td>'
        elif f > 10:
            return f'<td class="amt mom-mid">▲ {f:+.1f}%</td>'
        elif f > 0:
            return f'<td class="amt mom-neu">▲ {f:+.1f}%</td>'
        elif f < -10:
            return f'<td class="amt mom-hi">▼ {f:.1f}%</td>'
        elif f < 0:
            return f'<td class="amt mom-neu">▼ {f:.1f}%</td>'
        else:
            return f'<td class="amt mom-neu">0.0%</td>'
    except:
        return '<td class="amt mom-blank">—</td>'

def _loc_id(loc):
    return re.sub(r'[^A-Za-z0-9]', '_', loc)

def _sparkline(amounts, width=4, height=18):
    """Mini SVG sparkline from a list of amounts."""
    vals = [float(v) if not pd.isna(v) else 0 for v in amounts]
    if not vals or max(vals) == 0:
        return ''
    mx = max(vals) or 1
    bars = ''
    for v in vals[-8:]:  # last 8 months
        h = max(2, int((v / mx) * height))
        color = '#EF4444' if v == max(vals) else ('#93C5FD' if v < mx * 0.5 else '#60A5FA')
        bars += f'<div class="spark-bar" style="height:{h}px;background:{color}"></div>'
    return f'<span class="spark">{bars}</span>'


# ═══════════════════════════════════════════════════════════════
#  EXPENSE CATEGORY CLASSIFIER
# ═══════════════════════════════════════════════════════════════

def _classify_expense(name):
    """Map an expense name to a category bucket."""
    low = name.lower()
    for cat, keywords in EXPENSE_CATEGORIES.items():
        if cat == 'Others': continue
        if any(kw in low for kw in keywords):
            return cat
    return 'Others'

def _category_totals(df, loc=None, month=None):
    """Return {category: total_amount} dict."""
    mask = pd.Series(True, index=df.index)
    if loc:
        mask &= (df['Location'] == loc)
    if month:
        mask &= (df['Month Name'] == month)
    sub = df[mask].copy()
    sub['_cat'] = sub['Expenses Name'].apply(_classify_expense)
    return sub.groupby('_cat')['Expenses Rs.'].sum().to_dict()


# ═══════════════════════════════════════════════════════════════
#  EXECUTIVE KPI CARDS
# ═══════════════════════════════════════════════════════════════

def build_exec_kpis(df, locations, months):
    """6 executive KPI cards for the summary dashboard."""
    if not months:
        return ''

    last_m = months[-1]
    prev_m = months[-2] if len(months) > 1 else None

    all_sub  = df[df['Location'].isin(locations)]
    last_sub = all_sub[all_sub['Month Name'] == last_m]
    prev_sub = all_sub[all_sub['Month Name'] == prev_m] if prev_m else pd.DataFrame()

    total_last = last_sub['Expenses Rs.'].sum()
    total_prev = prev_sub['Expenses Rs.'].sum() if not prev_sub.empty else 0
    ytd_total  = all_sub['Expenses Rs.'].sum()

    # Budget placeholder (10% above last month, realistic stand-in)
    budget = total_last * 1.05
    variance = total_last - budget
    variance_pct = (variance / budget * 100) if budget else 0

    # Expense per location (proxy for per vehicle)
    exp_per_loc = total_last / len(locations) if locations else 0

    # Controllable Expense % (executive metric)
    # Controllable categories: Fuel, Salary, Marketing, Admin, Parts
    cat_tots_all = _category_totals(df[df['Location'].isin(locations)], month=last_m)
    controllable_cats = ['Fuel', 'Salary', 'Marketing', 'Admin', 'Parts']
    controllable_total = sum(cat_tots_all.get(cat, 0) for cat in controllable_cats)
    controllable_pct = (controllable_total / total_last * 100) if total_last else 0

    # Highest cost category
    cat_tots = _category_totals(df[df['Location'].isin(locations)], month=last_m)
    top_cat  = max(cat_tots, key=cat_tots.get) if cat_tots else '—'
    top_cat_amt = cat_tots.get(top_cat, 0)

    mom_pct  = ((total_last - total_prev) / abs(total_prev) * 100) if total_prev else 0
    mom_dir  = 'up' if mom_pct > 0 else ('dn' if mom_pct < 0 else 'fl')
    mom_sym  = '▲' if mom_pct > 0 else ('▼' if mom_pct < 0 else '→')
    mom_col  = 'red' if mom_pct > 10 else ('amber' if mom_pct > 0 else 'green')

    var_col  = 'red' if variance > 0 else 'green'
    var_sym  = '▲' if variance > 0 else '▼'

    def card(lbl, val, val_cls, sub, accent, delta_html=''):
        return (f'<div class="exp-kpi-card {accent}">'
                f'<div class="exp-kpi-lbl">{lbl}</div>'
                f'<div class="exp-kpi-val {val_cls}">{val}</div>'
                f'{delta_html}'
                f'<div class="exp-kpi-sub">{sub}</div>'
                f'</div>')

    def delta(val, cls, sym=''):
        return f'<div class="exp-kpi-delta {cls}">{sym} {val}</div>'

    cards = [
        card('Total Expense', fmt_inr(total_last), 'blue', f'YTD {fmt_inr(ytd_total)}', 'blue',
             delta(f'{abs(mom_pct):.1f}% vs {prev_m}', mom_dir, mom_sym)),
        card('Budget (Est.)', fmt_inr(budget), '', f'For {last_m}', 'neutral'),
        card('Budget Variance', fmt_inr(abs(variance)),
             var_col, f'{var_sym} {abs(variance_pct):.1f}% {"over" if variance>0 else "under"}',
             'red' if variance > 0 else 'green'),
        card('Exp · Per Location', fmt_inr(exp_per_loc), '', f'Avg across {len(locations)} locations', 'neutral'),
        card('Controllable Exp %', f'{controllable_pct:.0f}%', 'blue', f'{fmt_inr(controllable_total)} of {fmt_inr(total_last)} controllable', 'blue'),
        card('Highest Category', top_cat, 'amber', f'{fmt_inr(top_cat_amt)} in {last_m}', 'amber'),
    ]

    return '<div class="exp-kpi-row">' + ''.join(cards) + '</div>'


# ═══════════════════════════════════════════════════════════════
#  EXPENSE MIX CARDS
# ═══════════════════════════════════════════════════════════════

_CAT_ICONS = {
    'Fuel': '⛽', 'Salary': '👥', 'Warranty': '🔧',
    'Marketing': '📣', 'Utilities': '💡', 'Parts': '⚙️',
    'Admin': '📋', 'Others': '📦',
}
_CAT_COLORS = ['#185FA5','#3B6D11','#BA7517','#7C3AED','#0891B2',
               '#BE185D','#D97706','#6B7280']

def build_expense_mix(df, locations, months):
    """Interactive category cards showing expense breakdown."""
    if not months:
        return ''
    last_m = months[-1]
    cat_tots = _category_totals(df[df['Location'].isin(locations)], month=last_m)
    grand = sum(cat_tots.values()) or 1
    max_v = max(cat_tots.values()) if cat_tots else 1

    cards = ''
    for i, (cat, _) in enumerate(EXPENSE_CATEGORIES.items()):
        amt   = cat_tots.get(cat, 0)
        pct   = amt / grand * 100
        bar_w = int(amt / max_v * 100) if max_v else 0
        icon  = _CAT_ICONS.get(cat, '📦')
        color = _CAT_COLORS[i % len(_CAT_COLORS)]
        cards += (
            f'<div class="exp-mix-card" data-cat="{cat}" onclick="expMixFilter(\'{cat}\')">'
            f'<div class="exp-mix-card-icon">{icon}</div>'
            f'<div class="exp-mix-card-name">{cat}</div>'
            f'<div class="exp-mix-card-amt">{fmt_inr(amt)}</div>'
            f'<div class="exp-mix-card-pct">{pct:.1f}%</div>'
            f'<div class="exp-mix-card-bar">'
            f'<div class="exp-mix-card-fill" data-bar-w="{bar_w}" style="width:0%;background:{color}"></div>'
            f'</div></div>'
        )

    return (f'<div class="exp-mix-section">'
            f'<div class="exp-mix-title">Expense Mix'
            f'<span>Click a category to filter · {last_m}</span></div>'
            f'<div class="exp-mix-grid">{cards}</div>'
            f'</div>')


# ═══════════════════════════════════════════════════════════════
#  TOP COST CENTRES + DONUT
# ═══════════════════════════════════════════════════════════════

def build_exec_dashboard_two_col(df, locations, loc_map, months):
    """Two-column: top cost centres (left) + expense donut (right)."""
    if not months:
        return ''
    last_m = months[-1]
    prev_m = months[-2] if len(months) > 1 else None

    rows_data = []
    for loc in locations:
        sub = df[df['Location'] == loc]
        total_last = sub[sub['Month Name'] == last_m]['Expenses Rs.'].sum()
        total_prev = sub[sub['Month Name'] == prev_m]['Expenses Rs.'].sum() if prev_m else 0
        top_exp_ser = (sub[sub['Month Name'] == last_m]
                       .groupby('Expenses Name')['Expenses Rs.'].sum().nlargest(1))
        top_name = top_exp_ser.index[0].split('&')[0].strip()[:24] if len(top_exp_ser) else '—'
        mom = ((total_last - total_prev) / abs(total_prev) * 100) if total_prev else 0
        rows_data.append({'loc': loc, 'short': loc_map.get(loc, loc),
                          'amt': total_last, 'mom': mom, 'top_name': top_name})

    rows_data.sort(key=lambda x: x['amt'], reverse=True)
    max_amt = rows_data[0]['amt'] if rows_data else 1

    cost_rows = ''
    for i, rd in enumerate(rows_data[:10]):
        bar_w = int(rd['amt'] / max_amt * 100) if max_amt else 0
        mom_cls = 'up' if rd['mom'] > 5 else ('dn' if rd['mom'] < -5 else 'fl')
        mom_str = f'{"▲" if rd["mom"]>0 else "▼"}{abs(rd["mom"]):.1f}%'
        fill_color = '#EF4444' if bar_w > 70 else ('#F59E0B' if bar_w > 40 else '#185FA5')
        lid = _loc_id(rd['loc'])
        cost_rows += (
            f'<div class="exp-cost-row">'
            f'<div class="exp-cost-rank">{i+1}</div>'
            f'<div class="exp-cost-info">'
            f'<div class="exp-cost-name" title="{rd["loc"]}">{rd["short"]}</div>'
            f'<div class="exp-cost-sub">{rd["top_name"]}</div>'
            f'</div>'
            f'<div class="exp-cost-bar-wrap">'
            f'<div class="exp-cost-bar-track">'
            f'<div class="exp-cost-bar-fill" data-bar-w="{bar_w}" style="width:0%;background:{fill_color}"></div>'
            f'</div></div>'
            f'<div class="exp-cost-amt" onclick="expGoto(\'{lid}\')" style="cursor:pointer">{fmt_inr(rd["amt"])}</div>'
            f'<div class="exp-cost-delta {mom_cls}">{mom_str}</div>'
            f'</div>'
        )

    left_panel = (
        f'<div class="exp-panel-card">'
        f'<div class="exp-panel-hdr">'
        f'<div class="exp-panel-hdr-title">Top Cost Centres</div>'
        f'<div class="exp-panel-hdr-sub">{last_m} · Click amount to drill in</div>'
        f'</div>'
        f'<div class="exp-panel-body"><div class="exp-cost-list">{cost_rows}</div></div>'
        f'</div>'
    )

    # Donut data
    cat_tots = _category_totals(df[df['Location'].isin(locations)], month=last_m)
    grand = sum(cat_tots.values()) or 1
    donut_colors = _CAT_COLORS
    donut_data_js = ','.join(
        f'{{val:{v},color:"{donut_colors[i%len(donut_colors)]}"}}'
        for i, (k, v) in enumerate(cat_tots.items()) if v > 0
    )
    legend_rows = ''
    sorted_cats = sorted(cat_tots.items(), key=lambda x: x[1], reverse=True)
    for i, (cat, amt) in enumerate(sorted_cats):
        if amt <= 0: continue
        pct = amt / grand * 100
        color = donut_colors[list(cat_tots.keys()).index(cat) % len(donut_colors)]
        legend_rows += (
            f'<div class="exp-donut-leg-row">'
            f'<div class="exp-donut-leg-dot" style="background:{color}"></div>'
            f'<div class="exp-donut-leg-name">{cat}</div>'
            f'<div class="exp-donut-leg-val">{fmt_inr(amt)}</div>'
            f'<div class="exp-donut-leg-pct">{pct:.1f}%</div>'
            f'</div>'
        )

    right_panel = (
        f'<div class="exp-panel-card">'
        f'<div class="exp-panel-hdr">'
        f'<div class="exp-panel-hdr-title">Expense Mix</div>'
        f'<div class="exp-panel-hdr-sub">By category · {last_m}</div>'
        f'</div>'
        f'<div class="exp-panel-body">'
        f'<div class="exp-donut-wrap">'
        f'<canvas id="exp-donut-cvs" width="160" height="160"></canvas>'
        f'<div class="exp-donut-legend">{legend_rows}</div>'
        f'</div></div></div>'
        f'<script>window._expDonutData=[{donut_data_js}];</script>'
    )

    return f'<div class="exp-two-col">{left_panel}{right_panel}</div>'


# ═══════════════════════════════════════════════════════════════
#  MONTHLY TREND CHART
# ═══════════════════════════════════════════════════════════════

def build_monthly_trend(df, locations, months):
    """SVG trend line: actual expense per month."""
    if len(months) < 2:
        return ''
    all_sub = df[df['Location'].isin(locations)]
    actuals = []
    for m in months:
        actuals.append(float(all_sub[all_sub['Month Name'] == m]['Expenses Rs.'].sum()))

    actuals_js = '[' + ','.join(str(v) for v in actuals) + ']'
    labels_js  = '[' + ','.join(f'"{m}"' for m in months) + ']'

    # MoM pills
    mom_pills = ''
    for i in range(1, len(months)):
        if actuals[i-1]:
            chg = (actuals[i] - actuals[i-1]) / abs(actuals[i-1]) * 100
            cls = 'trend-up' if chg > 0 else ('trend-dn' if chg < 0 else 'trend-fl')
            sym = '▲' if chg > 0 else '▼'
            mom_pills += f'<span class="{cls}" style="margin-right:6px">{sym}{abs(chg):.1f}%</span>'

    return (
        f'<div class="exp-trend-wrap">'
        f'<div class="exp-trend-title">Monthly Expense Trend'
        f'<div class="exp-trend-legend">'
        f'<div class="exp-trend-leg-item">'
        f'<div class="exp-trend-leg-dot" style="background:#185FA5"></div>Actual</div>'
        f'</div></div>'
        f'<div class="exp-chart-area">'
        f'<svg id="exp-trend-svg" class="exp-chart-svg"></svg>'
        f'</div>'
        f'<div style="padding:8px 4px 0;font-size:10px;color:var(--color-text-secondary)">MoM: {mom_pills}</div>'
        f'</div>'
        f'<script>window._expTrendActuals={actuals_js};window._expTrendLabels={labels_js};</script>'
    )


# ═══════════════════════════════════════════════════════════════
#  LOCATION ANALYSIS TABLE (expandable rows)
# ═══════════════════════════════════════════════════════════════

def build_location_analysis(df, locations, loc_map, months):
    """Location table with expandable rows showing drilldown KPIs + alerts."""
    if not months:
        return ''
    last_m = months[-1]
    prev_m = months[-2] if len(months) > 1 else None

    rows_data = []
    
    if last_m:
        vec_data = _get_vectorized_exp_data(df, last_m)
        loc_totals = vec_data['loc_totals']
        loc_ytd_data = vec_data['loc_ytd']
        top_exp_dict = vec_data['top_exp_dict']
    else:
        loc_totals = pd.DataFrame()
        loc_ytd_data = pd.Series()
        top_exp_dict = {}
        
    for loc in locations:
        tlast = loc_totals.loc[loc, last_m] if loc in loc_totals.index and last_m in loc_totals.columns else 0
        tprev = loc_totals.loc[loc, prev_m] if prev_m and loc in loc_totals.index and prev_m in loc_totals.columns else 0
        ytd   = loc_ytd_data.loc[loc] if loc in loc_ytd_data.index else 0
        
        if loc in top_exp_dict:
            t_name, t_val = top_exp_dict[loc]
            top_name = t_name.split('&')[0].strip()[:26]
            top_share = t_val / tlast if tlast else 0
        else:
            top_name = '—'
            top_share = 0
        mom = ((tlast - tprev) / abs(tprev) * 100) if tprev else 0
        alerts = generate_alerts(df, loc)
        rows_data.append({
            'loc': loc, 'short': loc_map.get(loc, loc),
            'amt': tlast, 'ytd': ytd, 'mom': mom,
            'top_name': top_name, 'top_share': top_share,
            'alerts': alerts
        })

    rows_data.sort(key=lambda x: x['amt'], reverse=True)
    grand_last = sum(r['amt'] for r in rows_data)
    grand_ytd  = sum(r['ytd'] for r in rows_data)

    body = ''
    for rd in rows_data:
        lid = _loc_id(rd['loc'])
        mom = rd['mom']
        mom_col = '#991B1B' if mom > 10 else ('#BA7517' if mom > 0 else '#3B6D11')
        mom_str = f'{"▲" if mom>0 else "▼"} {abs(mom):.1f}%' if mom != 0 else '—'
        alert_cnt = len(rd['alerts'])
        alert_badge = (f'<span class="exp-alert-badge red" style="margin-left:6px">{alert_cnt} ⚠</span>'
                       if alert_cnt else '')

        # Expand arrow
        arr = f'<span class="exp-expand-arr" id="exp-expand-arr-{lid}">▶</span>'

        body += (
            f'<tr class="exp-loc-main-row" onclick="expLocToggle(\'{lid}\')">'
            f'<td><div class="exp-loc-name">{arr}{rd["short"]}{alert_badge}</div>'
            f'<div class="exp-loc-code">{rd["loc"]}</div></td>'
            f'<td style="font-weight:600">{fmt_inr(rd["amt"])}</td>'
            f'<td><span style="color:{mom_col};font-weight:600">{mom_str}</span></td>'
            f'<td>{fmt_inr(rd["ytd"])}</td>'
            f'<td style="font-size:11px;color:var(--color-text-secondary)">{rd["top_name"]}'
            f'<span style="font-size:9px;color:var(--color-text-secondary);margin-left:4px">{rd["top_share"]*100:.0f}%</span></td>'
            f'<td style="text-align:center">'
            f'{"<span style=\'color:#991B1B;font-weight:600\'>" + str(alert_cnt) + " ⚠</span>" if alert_cnt else "<span style=\'color:#3B6D11\'>✓</span>"}'
            f'</td></tr>'
        )

        # Expanded row: 3 mini KPIs + alerts
        exp_per_loc = fmt_inr(rd['amt'])
        cat_tots = _category_totals(df[df['Location'] == rd['loc']], month=last_m)
        top_cat  = max(cat_tots, key=cat_tots.get) if cat_tots else '—'

        alert_items = ''
        for a in rd['alerts'][:3]:
            alert_items += (f'<div class="exp-loc-alert-item">'
                            f'<span>{a["icon"]}</span>'
                            f'<span style="flex:1;color:#374151">{a["head"]}'
                            f'<span class="exp-alert-badge {a["badge_cls"]}" style="margin-left:6px">{a["badge_text"]}</span>'
                            f'</span></div>')
        if not rd['alerts']:
            alert_items = '<div style="font-size:10px;color:#3B6D11;padding:4px 0">✓ No anomalies detected</div>'

        expand_inner = (
            f'<div class="exp-loc-expand-inner">'
            f'<div class="exp-loc-expand-kpi">'
            f'<div class="exp-loc-expand-kpi-lbl">This Month</div>'
            f'<div class="exp-loc-expand-kpi-val">{exp_per_loc}</div>'
            f'<div class="exp-loc-expand-kpi-sub">MoM: {mom_str}</div>'
            f'</div>'
            f'<div class="exp-loc-expand-kpi">'
            f'<div class="exp-loc-expand-kpi-lbl">YTD Total</div>'
            f'<div class="exp-loc-expand-kpi-val">{fmt_inr(rd["ytd"])}</div>'
            f'<div class="exp-loc-expand-kpi-sub">{len(months)} months</div>'
            f'</div>'
            f'<div class="exp-loc-expand-kpi">'
            f'<div class="exp-loc-expand-kpi-lbl">Top Category</div>'
            f'<div class="exp-loc-expand-kpi-val" style="font-size:13px">{top_cat}</div>'
            f'<div class="exp-loc-expand-kpi-sub">{fmt_inr(cat_tots.get(top_cat,0))}</div>'
            f'</div>'
            f'</div>'
            f'<div class="exp-loc-alert-list">{alert_items}</div>'
            f'<div style="margin-top:8px;font-size:10px;display:flex;gap:12px;flex-wrap:wrap">'
            f'<span style="color:var(--blue);cursor:pointer;font-weight:500" '
            f'onclick="expGoto(\'{lid}\')">View full analysis →</span>'
            f'<span style="color:var(--text-sub);cursor:pointer;font-weight:500" '
            f'onclick="expNavTo(\'dealer_audit\',\'{lid}\')">Open Dealer Audit →</span>'
            f'<span style="color:var(--text-sub);cursor:pointer;font-weight:500" '
            f'onclick="expNavTo(\'revenue_leakage\',\'{lid}\')">Open Revenue Leakage →</span>'
            f'</div>'
        )

        body += (f'<tr class="exp-loc-expand-row" id="exp-expand-{lid}">'
                 f'<td colspan="6"><div style="padding:4px 0">{expand_inner}</div></td></tr>')

    # Grand total row
    body += (f'<tr class="exp-tot-row">'
             f'<td>ALL {len(locations)} LOCATIONS</td>'
             f'<td>{fmt_inr(grand_last)}</td>'
             f'<td></td>'
             f'<td>{fmt_inr(grand_ytd)}</td>'
             f'<td></td><td></td></tr>')

    return (
        f'<div class="exp-loc-analysis">'
        f'<div class="exp-loc-analysis-hdr">'
        f'<span style="font-size:12px;font-weight:600;color:var(--text)">Location Analysis</span>'
        f'<span style="font-size:10px;color:var(--text-xs)">Click row to expand · {last_m}</span>'
        f'</div>'
        f'<div style="overflow-x:auto">'
        f'<table class="exp-loc-tbl">'
        f'<thead><tr>'
        f'<th style="text-align:left;min-width:180px">Location</th>'
        f'<th>Expense · {last_m}</th>'
        f'<th>MoM%</th>'
        f'<th>YTD Total</th>'
        f'<th style="text-align:left">Top Expense</th>'
        f'<th>Alerts</th>'
        f'</tr></thead>'
        f'<tbody>{body}</tbody>'
        f'</table></div>'
        f'<div class="exp-legend"><span>Click any row to expand details</span>'
        f'<span style="color:#991B1B">⚠ = anomaly detected</span></div>'
        f'</div>'
    )


# ═══════════════════════════════════════════════════════════════
#  TRANSACTION DRILLDOWN
# ═══════════════════════════════════════════════════════════════

def build_transaction_drilldown(df, locations, months, top_n=15):
    """High-value expense transactions across all locations."""
    if not months:
        return ''
    last_m = months[-1]
    sub = df[df['Location'].isin(locations) & (df['Month Name'] == last_m)].copy()
    if sub.empty:
        return ''
    sub = sub.sort_values('Expenses Rs.', ascending=False).head(top_n)

    rows = ''
    for _, row in sub.iterrows():
        amt = row['Expenses Rs.']
        cat = _classify_expense(row['Expenses Name'])
        hi_cls = ' class="exp-txn-hi"' if amt > sub['Expenses Rs.'].quantile(0.8) else ''
        rows += (
            f'<tr>'
            f'<td>{row.get("Location","—")}</td>'
            f'<td>{row["Expenses Name"]}</td>'
            f'<td><span class="exp-txn-cat-pill">{cat}</span></td>'
            f'<td{hi_cls}>{fmt_inr_full(amt)}</td>'
            f'<td>{last_m}</td>'
            f'</tr>'
        )

    return (
        f'<div class="exp-txn-wrap">'
        f'<div class="exp-panel-hdr">'
        f'<div class="exp-panel-hdr-title">High-Value Transactions</div>'
        f'<div class="exp-panel-hdr-sub">Top {top_n} by amount · {last_m} · Red = top 20%</div>'
        f'</div>'
        f'<div style="overflow-x:auto">'
        f'<table class="exp-txn-tbl">'
        f'<thead><tr>'
        f'<th style="text-align:left">Location</th>'
        f'<th style="text-align:left">Expense</th>'
        f'<th style="text-align:left">Category</th>'
        f'<th>Amount</th>'
        f'<th>Month</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table></div></div>'
    )


# ═══════════════════════════════════════════════════════════════
#  EXECUTIVE INSIGHTS (7)
# ═══════════════════════════════════════════════════════════════

def build_exec_insights(df, locations, months):
    """Generate 7 business insights ordered by impact."""
    if not months:
        return ''
    last_m = months[-1]
    prev_m = months[-2] if len(months) > 1 else None
    all_sub = df[df['Location'].isin(locations)]

    insights = []

    # I1: Total expense trend
    total_last = all_sub[all_sub['Month Name'] == last_m]['Expenses Rs.'].sum()
    total_prev = all_sub[all_sub['Month Name'] == prev_m]['Expenses Rs.'].sum() if prev_m else 0
    if total_prev:
        mom = (total_last - total_prev) / abs(total_prev) * 100
        dir_word = 'increased' if mom > 0 else 'decreased'
        impact = 'hi' if abs(mom) > 15 else ('mid' if abs(mom) > 5 else 'lo')
        insights.append({
            'rank': 1, 'icon': '📊' if mom > 0 else '📉',
            'head': f'Total expenditure {dir_word} {abs(mom):.1f}% in {last_m}',
            'detail': f'Moved from {fmt_inr(total_prev)} to {fmt_inr(total_last)}, a {dir_word} of {fmt_inr(abs(total_last-total_prev))}. Requires {"immediate review" if abs(mom)>20 else "monitoring"}.',
            'impact': impact
        })

    # I2: Top cost centre
    loc_totals = {loc: all_sub[(all_sub['Location']==loc) & (all_sub['Month Name']==last_m)]['Expenses Rs.'].sum()
                  for loc in locations}
    top_loc = max(loc_totals, key=loc_totals.get) if loc_totals else None
    if top_loc:
        top_share = loc_totals[top_loc] / total_last * 100 if total_last else 0
        insights.append({
            'rank': 2, 'icon': '📍',
            'head': f'{top_loc} accounts for {top_share:.0f}% of total expenses',
            'detail': f'Highest spending location at {fmt_inr(loc_totals[top_loc])} in {last_m}. Review if disproportionate vs revenue contribution.',
            'impact': 'hi' if top_share > 30 else 'mid'
        })

    # I3: Top category
    cat_tots = _category_totals(all_sub, month=last_m)
    top_cat = max(cat_tots, key=cat_tots.get) if cat_tots else None
    if top_cat and total_last:
        cat_share = cat_tots[top_cat] / total_last * 100
        insights.append({
            'rank': 3, 'icon': _CAT_ICONS.get(top_cat, '📦'),
            'head': f'{top_cat} is the dominant expense category at {cat_share:.1f}%',
            'detail': f'{fmt_inr(cat_tots[top_cat])} spent on {top_cat.lower()} across all locations in {last_m}. Benchmark against industry norms.',
            'impact': 'hi' if cat_share > 35 else 'mid'
        })

    # I4: Most spiked expense
    spike_alerts = []
    for loc in locations:
        for a in generate_alerts(df, loc):
            if a['type'] == 'spike':
                spike_alerts.append((loc, a))
    if spike_alerts:
        loc_s, alert_s = spike_alerts[0]
        insights.append({
            'rank': 4, 'icon': '⚠️',
            'head': f'Expense spike detected at {loc_s}: {alert_s["head"].split(" — ")[0]}',
            'detail': alert_s['detail'] + ' This represents a significant deviation from expected spend.',
            'impact': 'hi'
        })
    else:
        insights.append({
            'rank': 4, 'icon': '✅',
            'head': 'No sudden expense spikes detected this month',
            'detail': f'All MoM changes are within the {MOM_SPIKE_THRESHOLD:.0f}% alert threshold. Continue routine monitoring.',
            'impact': 'lo'
        })

    # I5: Sustained growth
    sustained = []
    for loc in locations:
        for a in generate_alerts(df, loc):
            if a['type'] == 'sustained':
                sustained.append((loc, a))
    if sustained:
        loc_s, alert_s = sustained[0]
        insights.append({
            'rank': 5, 'icon': '📈',
            'head': f'Sustained cost creep at {loc_s}: {alert_s["head"].split(" — ")[0]}',
            'detail': alert_s['detail'] + ' Prolonged upward trends require root cause analysis before they become structural.',
            'impact': 'mid'
        })
    else:
        insights.append({
            'rank': 5, 'icon': '✅',
            'head': 'No sustained multi-month expense creep identified',
            'detail': 'No expense line has risen for 3+ consecutive months beyond threshold. Expense base appears stable.',
            'impact': 'lo'
        })

    # I6: YTD run rate
    n_months = len(months) or 1
    run_rate = total_last * 12
    ytd_total = all_sub['Expenses Rs.'].sum()
    insights.append({
        'rank': 6, 'icon': '📅',
        'head': f'Annualised expense run rate: {fmt_inr(run_rate)}',
        'detail': f'Based on {last_m} actuals of {fmt_inr(total_last)}. YTD spend is {fmt_inr(ytd_total)} over {n_months} months. Budget alignment to be verified.',
        'impact': 'mid'
    })

    # I7: Zero-data locations
    zero_locs = [loc for loc in locations
                 if all_sub[(all_sub['Location']==loc) & (all_sub['Month Name']==last_m)]['Expenses Rs.'].sum() == 0]
    if zero_locs:
        insights.append({
            'rank': 7, 'icon': '🔶',
            'head': f'{len(zero_locs)} location(s) show zero expenses in {last_m}',
            'detail': f'{", ".join(zero_locs[:3])} report no expenses. Verify data upload completeness for these locations.',
            'impact': 'mid'
        })
    else:
        insights.append({
            'rank': 7, 'icon': '✅',
            'head': 'All locations have reported expenses for ' + last_m,
            'detail': f'Data completeness confirmed across all {len(locations)} locations. No missing submissions detected.',
            'impact': 'lo'
        })

    rows = ''
    for ins in insights[:7]:
        rows += (
            f'<div class="exp-insight-row">'
            f'<div class="exp-insight-rank">{ins["rank"]}</div>'
            f'<div class="exp-insight-icon">{ins["icon"]}</div>'
            f'<div class="exp-insight-body">'
            f'<div class="exp-insight-head">{ins["head"]}</div>'
            f'<div class="exp-insight-detail">{ins["detail"]}</div>'
            f'</div>'
            f'<div class="exp-insight-impact {ins["impact"]}">'
            f'{"HIGH" if ins["impact"]=="hi" else ("MED" if ins["impact"]=="mid" else "LOW")}'
            f'</div></div>'
        )

    return (
        f'<div class="exp-insights-wrap">'
        f'<div class="exp-insights-hdr">'
        f'<div class="exp-insights-hdr-title">Executive Insights</div>'
        f'<div class="exp-insights-hdr-sub">7 insights · ordered by business impact</div>'
        f'</div>'
        f'<div class="exp-insights-list">{rows}</div>'
        f'</div>'
    )


# ═══════════════════════════════════════════════════════════════
#  EXECUTIVE ACTION PANEL
# ═══════════════════════════════════════════════════════════════

def build_action_panel(df, locations, months):
    """5–8 context-aware recommendations."""
    if not months:
        return ''
    last_m = months[-1]
    all_sub = df[df['Location'].isin(locations)]
    total_last = all_sub[all_sub['Month Name'] == last_m]['Expenses Rs.'].sum()
    cat_tots = _category_totals(all_sub, month=last_m)

    actions = []

    # Fuel recommendation
    fuel_amt = cat_tots.get('Fuel', 0)
    if fuel_amt > 0:
        fuel_share = fuel_amt / total_last * 100 if total_last else 0
        actions.append({
            'icon': '⛽', 'trigger': f'Fuel: {fmt_inr(fuel_amt)} ({fuel_share:.1f}% of total)',
            'steps': ['Review consumption logs per vehicle per location',
                      'Audit fuel vendors — compare rate cards',
                      'Consider GPS-based fuel monitoring system'],
            'badge': 'hi' if fuel_share > 20 else 'mid'
        })

    # Warranty
    warranty_amt = cat_tots.get('Warranty', 0)
    if warranty_amt > 0:
        actions.append({
            'icon': '🔧', 'trigger': f'Warranty claims: {fmt_inr(warranty_amt)}',
            'steps': ['Inspect repeat failure patterns by model',
                      'Review claim approval process for leakages',
                      'Target warranty cost below 2% of service revenue'],
            'badge': 'mid'
        })

    # Salary
    salary_amt = cat_tots.get('Salary', 0)
    if salary_amt > 0:
        sal_share = salary_amt / total_last * 100 if total_last else 0
        actions.append({
            'icon': '👥', 'trigger': f'Salary & wages: {fmt_inr(salary_amt)} ({sal_share:.1f}%)',
            'steps': ['Map headcount vs revenue contribution by location',
                      'Review overtime and contract staff utilisation',
                      'Benchmark staff cost per vehicle sold'],
            'badge': 'hi' if sal_share > 30 else 'mid'
        })

    # Spike locations
    spike_locs = []
    for loc in locations:
        for a in generate_alerts(df, loc):
            if a['type'] == 'spike':
                spike_locs.append(loc)
                break
    if spike_locs:
        actions.append({
            'icon': '⚠️', 'trigger': f'Expense spikes at: {", ".join(spike_locs[:3])}',
            'steps': ['Request invoice copies for flagged line items',
                      'Cross-check with purchase approvals',
                      'Implement pre-approval for items above threshold'],
            'badge': 'hi'
        })

    # Admin
    admin_amt = cat_tots.get('Admin', 0)
    if admin_amt > 0:
        actions.append({
            'icon': '📋', 'trigger': f'Admin costs: {fmt_inr(admin_amt)}',
            'steps': ['Digitalise stationery and printing spend',
                      'Consolidate vendor contracts for volume discounts'],
            'badge': 'mid'
        })

    # Marketing
    mkt_amt = cat_tots.get('Marketing', 0)
    if mkt_amt > 0:
        actions.append({
            'icon': '📣', 'trigger': f'Marketing spend: {fmt_inr(mkt_amt)}',
            'steps': ['Measure ROI per channel before next allocation',
                      'Prioritise digital over print for cost efficiency'],
            'badge': 'mid'
        })

    # Budget alignment
    actions.append({
        'icon': '🎯', 'trigger': 'Budget vs Actual alignment',
        'steps': ['Set location-wise monthly expense budgets',
                  'Automate variance alerts above 10%',
                  'Monthly expense review with location managers'],
        'badge': 'mid'
    })

    cards = ''
    for a in actions[:8]:
        steps_html = ''.join(f'<span>{s}</span>' for s in a['steps'])
        cards += (
            f'<div class="exp-action-card">'
            f'<div class="exp-action-icon">{a["icon"]}</div>'
            f'<div class="exp-action-body">'
            f'<div class="exp-action-trigger">{a["trigger"]}</div>'
            f'<div class="exp-action-steps">{steps_html}</div>'
            f'</div>'
            f'<div class="exp-action-badge {a["badge"]}">'
            f'{"URGENT" if a["badge"]=="hi" else "ACTION"}'
            f'</div></div>'
        )

    return (
        f'<div class="exp-action-wrap">'
        f'<div class="exp-action-title">🎯 Executive Action Panel'
        f'<span style="font-size:10px;font-weight:400;color:var(--blue)">'
        f'{len(actions[:8])} recommendations</span></div>'
        f'<div class="exp-action-grid">{cards}</div>'
        f'<div style="margin-top:12px;padding-top:12px;border-top:1px solid #C8DBF0;'
        f'display:flex;gap:10px;flex-wrap:wrap">'
        f'<button onclick="expNavTo(\'dealer_audit\')" '
        f'style="padding:6px 14px;border:1px solid var(--blue);background:var(--card);'
        f'color:var(--blue);border-radius:8px;font-size:11px;font-weight:500;cursor:pointer;'
        f'transition:background .15s">Open Dealer Audit →</button>'
        f'<button onclick="expNavTo(\'revenue_leakage\')" '
        f'style="padding:6px 14px;border:1px solid var(--blue);background:var(--card);'
        f'color:var(--blue);border-radius:8px;font-size:11px;font-weight:500;cursor:pointer;'
        f'transition:background .15s">Open Revenue Leakage →</button>'
        f'</div>'
        f'</div>'
    )


# ═══════════════════════════════════════════════════════════════
#  ALERT BANNER (top of page)
# ═══════════════════════════════════════════════════════════════

def build_alert_banner(df, locations, months):
    """Dynamic headline banner from top alerts."""
    if not months:
        return ''
    last_m = months[-1]

    all_alerts = []
    for loc in locations:
        for a in generate_alerts(df, loc):
            all_alerts.append((loc, a))

    if not all_alerts:
        return (
            '<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;'
            'padding:10px 16px;margin-bottom:12px;font-size:12px;color:#3B6D11;font-weight:500">'
            '✓ No anomalies detected across all locations — expense patterns are stable</div>'
        )

    # Build dynamic headline from top alerts
    spike_cnt     = sum(1 for _, a in all_alerts if a['type'] == 'spike')
    sustained_cnt = sum(1 for _, a in all_alerts if a['type'] == 'sustained')
    share_cnt     = sum(1 for _, a in all_alerts if a['type'] == 'share')

    headline_parts = []
    if spike_cnt:
        headline_parts.append(f'{spike_cnt} sudden expense spike{"s" if spike_cnt>1 else ""} detected')
    if sustained_cnt:
        headline_parts.append(f'{sustained_cnt} category{"" if sustained_cnt==1 else "ies"} rising for 3+ months')
    if share_cnt:
        headline_parts.append(f'{share_cnt} expense item{"s" if share_cnt>1 else ""} dominating location budgets')
    headline = ' · '.join(headline_parts) or f'{len(all_alerts)} alerts detected'

    pills = ''
    seen_heads = set()
    for loc, a in all_alerts[:6]:
        if a['head'] in seen_heads: continue
        seen_heads.add(a['head'])
        short = a['head'].split(' — ')[0][:32]
        pills += f'<span class="exp-alert-pill {a["badge_cls"]}">{short}</span>'

    return (
        f'<div class="exp-alert-banner">'
        f'<div class="exp-alert-banner-icon">⚠️</div>'
        f'<div class="exp-alert-banner-body">'
        f'<div class="exp-alert-banner-head">{headline}</div>'
        f'<div class="exp-alert-banner-items">{pills}</div>'
        f'</div>'
        f'<div class="exp-alert-cnt-badge">{len(all_alerts)} total</div>'
        f'</div>'
    )


# ═══════════════════════════════════════════════════════════════
#  KPI CARDS — location level  (PRESERVED)
# ═══════════════════════════════════════════════════════════════

def build_exp_kpis(df, loc, months):
    """Build KPI row for a location."""
    sub = df[df['Location'] == loc]
    if sub.empty or not months:
        return ''

    last_m  = months[-1]
    prev_m  = months[-2] if len(months) > 1 else None

    total_last  = sub[sub['Month Name'] == last_m]['Expenses Rs.'].sum()
    total_prev  = sub[sub['Month Name'] == prev_m]['Expenses Rs.'].sum() if prev_m else 0
    ytd_total   = sub['Expenses Rs.'].sum()
    num_exp     = sub['Expenses Name'].nunique()

    mom_pct = ((total_last - total_prev) / abs(total_prev) * 100) if total_prev else 0
    mom_cls = 'lo' if mom_pct > 10 else ('mid' if mom_pct > 0 else 'hi')
    mom_str = f'{mom_pct:+.1f}%'

    vec_data = _get_vectorized_exp_data(df, last_m)
    if loc in vec_data['top_exp_dict']:
        t_name, _ = vec_data['top_exp_dict'][loc]
        top_exp_name_short = t_name.split('&')[0].strip()[:20]
    else:
        top_exp_name_short = '—'

    cards = [
        (f'Total Exp · {last_m}', fmt_inr(total_last), 'neu', fmt_inr(total_prev) + ' prev'),
        ('MoM Change', mom_str, mom_cls, f'vs {prev_m}' if prev_m else ''),
        ('YTD Total', fmt_inr(ytd_total), 'neu', f'{len(months)} months'),
        ('Expense Items', str(num_exp), 'neu', 'tracked categories'),
        ('Largest Expense', top_exp_name_short, 'mid', f'{last_m}'),
    ]

    html = '<div class="exp-kpi-row-loc">'
    for lbl, val, cls, sub_text in cards:
        html += (f'<div class="exp-kpi">'
                 f'<div class="exp-kpi-lbl-sm">{lbl}</div>'
                 f'<div class="exp-kpi-val-sm {cls}">{val}</div>'
                 f'<div class="exp-kpi-sub-sm">{sub_text}</div></div>')
    html += '</div>'
    return html


# ═══════════════════════════════════════════════════════════════
#  MOM TABLE — location level  (UNCHANGED)
# ═══════════════════════════════════════════════════════════════

def build_mom_table(df, loc, months):
    """
    Collapsible MoM table: Group (collapsible) → Expense rows.
    Shows: Expense Name | Apr-25 | MoM% | May-25 | MoM% | … | YTD Total | Trend
    """
    sub = df[df['Location'] == loc]
    if sub.empty:
        return '<div style="padding:20px;color:var(--color-text-secondary);text-align:center">No expense data for this location</div>'

    th_html = '<th style="min-width:180px;text-align:left">Expense</th>'
    for i, m in enumerate(months):
        th_html += f'<th class="amt">{m}</th>'
        if i > 0:
            th_html += f'<th class="amt" style="color:var(--color-text-secondary);min-width:70px">MoM%</th>'
    th_html += '<th class="amt">YTD Total</th><th style="min-width:90px;text-align:center">Trend</th>'

    body_html = ''
    groups = [g for g in GROUP_ORDER if g in sub['Expenses Group'].values]
    if not groups:
        groups = sorted(sub['Expenses Group'].unique())

    uid_counter = [0]

    for grp in groups:
        grp_sub = sub[sub['Expenses Group'] == grp]
        if grp_sub.empty:
            continue

        grp_totals = {}
        for m in months:
            grp_totals[m] = grp_sub[grp_sub['Month Name'] == m]['Expenses Rs.'].sum()
        grp_ytd = sum(grp_totals.values())

        gid = f'g_{_loc_id(loc)}_{uid_counter[0]}'
        uid_counter[0] += 1

        grp_cells = ''
        for i, m in enumerate(months):
            amt = grp_totals[m]
            grp_cells += f'<td class="amt amt-total">{fmt_inr_full(amt)}</td>'
            if i > 0:
                prev_amt = grp_totals[months[i-1]]
                if prev_amt:
                    mom_v = (amt - prev_amt) / abs(prev_amt) * 100
                    grp_cells += mom_cell(mom_v)
                else:
                    grp_cells += '<td class="amt mom-blank">—</td>'

        grp_spark = _sparkline([grp_totals[m] for m in months])
        grp_cells += f'<td class="amt amt-total">{fmt_inr_full(grp_ytd)}</td>'
        grp_cells += f'<td style="text-align:center">{grp_spark}</td>'

        body_html += (f'<tr class="exp-grp-row" onclick="expTog(\'{gid}\')">'
                      f'<td><span class="arr" id="earr_{gid}">▶</span>'
                      f'<strong>{grp}</strong></td>{grp_cells}</tr>')

        for exp_name in sorted(grp_sub['Expenses Name'].unique()):
            exp_sub  = grp_sub[grp_sub['Expenses Name'] == exp_name]
            exp_amts = {}
            exp_moms = {}
            for m in months:
                row_m = exp_sub[exp_sub['Month Name'] == m]
                exp_amts[m] = row_m['Expenses Rs.'].sum() if not row_m.empty else 0
                if not row_m.empty and not row_m['MoM_Calc'].isna().all():
                    exp_moms[m] = row_m['MoM_Calc'].mean()
                else:
                    exp_moms[m] = np.nan

            ytd_val = sum(exp_amts.values())

            cells = ''
            for i, m in enumerate(months):
                amt = exp_amts[m]
                cell_style = ' style="color:var(--color-text-secondary)"' if amt == 0 else ''
                cells += f'<td class="amt"{cell_style}>{fmt_inr_full(amt) if amt != 0 else "—"}</td>'
                if i > 0:
                    cells += mom_cell(exp_moms[m])

            spark = _sparkline([exp_amts[m] for m in months])
            cells += f'<td class="amt">{fmt_inr_full(ytd_val)}</td>'
            cells += f'<td style="text-align:center">{spark}</td>'

            body_html += (f'<tr class="exp-name-row ep-{gid}" style="display:none">'
                          f'<td style="padding-left:24px">{exp_name}</td>{cells}</tr>')

    # Grand total row
    grand_totals = {}
    for m in months:
        grand_totals[m] = sub[sub['Month Name'] == m]['Expenses Rs.'].sum()
    grand_ytd = sum(grand_totals.values())

    tot_cells = ''
    for i, m in enumerate(months):
        tot_cells += f'<td class="amt amt-total">{fmt_inr_full(grand_totals[m])}</td>'
        if i > 0:
            prev_amt = grand_totals[months[i-1]]
            if prev_amt:
                mom_v = (grand_totals[m] - prev_amt) / abs(prev_amt) * 100
                tot_cells += mom_cell(mom_v)
            else:
                tot_cells += '<td class="amt mom-blank">—</td>'
    tot_spark = _sparkline([grand_totals[m] for m in months])
    tot_cells += f'<td class="amt amt-total">{fmt_inr_full(grand_ytd)}</td>'
    tot_cells += f'<td style="text-align:center">{tot_spark}</td>'

    body_html += f'<tr class="exp-tot-row"><td>GRAND TOTAL</td>{tot_cells}</tr>'

    legend_html = (
        '<div class="exp-legend">'
        '<span>Click group row to expand expenses</span>'
        '<span style="color:#991B1B">● Spike: MoM &gt;+30%</span>'
        '<span style="color:#BA7517">● Rising: MoM +10%–30%</span>'
        '<span style="color:#3B6D11">● Falling: MoM &lt;-10%</span>'
        '<span>Sparkline = last 8 months trend</span>'
        '</div>'
    )

    return (f'<div class="exp-sec-body">'
            f'<table style="width:100%;border-collapse:collapse;font-size:12px">'
            f'<thead><tr style="background:#F8F9FB">{th_html}</tr></thead>'
            f'<tbody>{body_html}</tbody>'
            f'</table></div>'
            + legend_html)


# ═══════════════════════════════════════════════════════════════
#  ALERT SECTION HTML  (PRESERVED)
# ═══════════════════════════════════════════════════════════════

def build_alert_section(df, loc):
    """Build the AI-alert panel for a location."""
    alerts = generate_alerts(df, loc)

    if not alerts:
        return (f'<div class="exp-alert-sec">'
                f'<div class="exp-alert-hdr">'
                f'<span class="exp-alert-title">AI Alerts</span>'
                f'<span class="exp-alert-ok">✓ No anomalies detected</span>'
                f'</div></div>')

    cards_html = ''
    for a in alerts:
        card_cls = 'warn' if a['type'] in ('sustained', 'zero', 'share') else (
                   'info' if a['type'] == 'drop' else '')
        cards_html += (f'<div class="exp-alert-card {card_cls}">'
                       f'<div class="exp-alert-icon">{a["icon"]}</div>'
                       f'<div class="exp-alert-body">'
                       f'<div class="exp-alert-head">{a["head"]}'
                       f'<span class="exp-alert-badge {a["badge_cls"]}">{a["badge_text"]}</span>'
                       f'</div>'
                       f'<div class="exp-alert-detail">{a["detail"]}</div>'
                       f'</div></div>')

    return (f'<div class="exp-alert-sec">'
            f'<div class="exp-alert-hdr">'
            f'<span class="exp-alert-title">'
            f'<span class="exp-alert-dot"></span>AI Expense Alerts</span>'
            f'<span class="exp-alert-cnt">{len(alerts)} alert{"s" if len(alerts)>1 else ""}</span>'
            f'</div>'
            f'<div class="exp-alert-list">{cards_html}</div>'
            f'</div>')


# ═══════════════════════════════════════════════════════════════
#  SUMMARY DASHBOARD TABLE  (PRESERVED)
# ═══════════════════════════════════════════════════════════════

def build_exp_dashboard(df, locations, loc_map, months):
    """Cross-location summary dashboard table."""
    if not months:
        return '<div style="padding:20px;color:var(--color-text-secondary)">No data</div>'

    last_m = months[-1]
    prev_m = months[-2] if len(months) > 1 else None
    max_total = 0

    # F2: Vectorized Precomputations for the Dashboard
    if last_m:
        vec_data = _get_vectorized_exp_data(df, last_m)
        loc_totals = vec_data['loc_totals']
        loc_ytd = vec_data['loc_ytd']
        top_exp_dict = vec_data['top_exp_dict']
    else:
        loc_totals = pd.DataFrame()
        loc_ytd = pd.Series()
        top_exp_dict = {}

    rows_data = []
    for loc in locations:
        total_last = loc_totals.loc[loc, last_m] if loc in loc_totals.index and last_m in loc_totals.columns else 0
        total_prev = loc_totals.loc[loc, prev_m] if prev_m and loc in loc_totals.index and prev_m in loc_totals.columns else 0
        ytd_total  = loc_ytd.loc[loc] if loc in loc_ytd.index else 0
        
        if loc in top_exp_dict:
            t_name, t_val = top_exp_dict[loc]
            top_name   = t_name.split('&')[0].strip()[:22]
            top_share  = t_val / total_last if total_last else 0
        else:
            top_name   = '—'
            top_share  = 0
            
        mom = ((total_last - total_prev) / abs(total_prev) * 100) if total_prev else 0
        num_alerts = len(generate_alerts(df, loc))

        rows_data.append({
            'loc': loc, 'total_last': total_last, 'total_prev': total_prev,
            'ytd': ytd_total, 'mom': mom, 'top_name': top_name,
            'top_share': top_share, 'num_alerts': num_alerts
        })
        max_total = max(max_total, total_last)

    rows_data.sort(key=lambda x: x['total_last'], reverse=True)

    rows_html = ''
    for rd in rows_data:
        loc   = rd['loc']
        lid   = _loc_id(loc)
        short = loc_map.get(loc, loc)
        mom   = rd['mom']
        mom_cls = 'lo' if mom > 10 else ('mid' if mom > 0 else 'hi')
        mom_str = f'{"▲" if mom>0 else "▼"} {abs(mom):.1f}%' if rd['total_prev'] else '—'

        bar_w = int((rd['total_last'] / max_total) * 100) if max_total else 0
        bar_cls = 'lo' if bar_w > 70 else ('mid' if bar_w > 40 else 'hi')

        alert_badge = ''
        if rd['num_alerts'] > 0:
            alert_badge = f'<span class="exp-alert-badge red">{rd["num_alerts"]} ⚠</span>'

        rows_html += (f'<tr onclick="expGoto(\'{lid}\')">'
                      f'<td><div class="dash-loc-name">{short} {alert_badge}</div>'
                      f'<div class="dash-loc-sub">{loc}</div></td>'
                      f'<td><div class="bar-cell">'
                      f'<div class="bar-track"><div class="bar-fill {bar_cls}" style="width:{bar_w}%"></div></div>'
                      f'<span class="bar-label {bar_cls}">{fmt_inr(rd["total_last"])}</span>'
                      f'</div></td>'
                      f'<td class="amt"><span style="color:{"#A32D2D" if mom_cls=="lo" else ("#BA7517" if mom_cls=="mid" else "#3B6D11")}">{mom_str}</span></td>'
                      f'<td class="amt">{fmt_inr(rd["ytd"])}</td>'
                      f'<td style="font-size:11px;color:var(--color-text-secondary)">{rd["top_name"]}</td>'
                      f'</tr>')

    grand_last = sum(r['total_last'] for r in rows_data)
    grand_ytd  = sum(r['ytd'] for r in rows_data)
    grand_prev = sum(r['total_prev'] for r in rows_data)
    grand_mom  = ((grand_last - grand_prev) / abs(grand_prev) * 100) if grand_prev else 0
    grand_mom_str = f'{"▲" if grand_mom>0 else "▼"} {abs(grand_mom):.1f}%'

    rows_html += (f'<tr class="dash-tot">'
                  f'<td>ALL {len(locations)} LOCATIONS</td>'
                  f'<td class="amt">{fmt_inr(grand_last)}</td>'
                  f'<td class="amt">{grand_mom_str}</td>'
                  f'<td class="amt">{fmt_inr(grand_ytd)}</td>'
                  f'<td></td></tr>')

    return (f'<div class="exp-dash-wrap"><table class="exp-dash-tbl">'
            f'<thead><tr>'
            f'<th style="text-align:left;min-width:180px">Location</th>'
            f'<th style="min-width:180px">Exp · {last_m}</th>'
            f'<th>MoM%</th>'
            f'<th>YTD Total</th>'
            f'<th style="text-align:left">Top Expense</th>'
            f'</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table></div>'
            f'<div class="exp-legend">'
            f'<span>Click any row to drill into that location</span>'
            f'<span style="color:#991B1B">⚠ = AI alerts found</span>'
            f'</div>')


# ═══════════════════════════════════════════════════════════════
#  LOCATION SECTION  (PRESERVED)
# ═══════════════════════════════════════════════════════════════

def build_loc_section(df, loc, loc_map):
    """Full collapsible section for one location."""
    lid   = _loc_id(loc)
    short = loc_map.get(loc, loc)
    sub   = df[df['Location'] == loc]
    months = get_available_months(sub)

    kpi_html    = build_exp_kpis(df, loc, months)
    mom_html    = build_mom_table(df, loc, months)
    alerts_html = build_alert_section(df, loc)

    num_alerts = len(generate_alerts(df, loc))
    alert_pill = (f'<span class="exp-alert-badge red" style="margin-left:8px">'
                  f'{num_alerts} ⚠</span>') if num_alerts else ''

    heading = (f'<div class="exp-loc-heading">'
               f'<div><div class="exp-loc-heading-name">{short}{alert_pill}</div>'
               f'<div class="exp-loc-heading-sub">{loc} · {len(months)} months of data</div></div>'
               f'</div>')

    tab_html = (
        f'<div class="exp-tab-row" id="etabs_{lid}">'
        f'<div class="exp-tab on" data-ep="mom" onclick="expShowPanel(\'mom\',\'{lid}\')">📊 MoM Trend</div>'
        f'<div class="exp-tab" data-ep="alerts" onclick="expShowPanel(\'alerts\',\'{lid}\')">🔔 AI Alerts</div>'
        f'</div>'
        f'<div class="exp-panel on" id="ep_{lid}_mom">'
        f'<div class="exp-sec"><div class="exp-sec-hdr">'
        f'<span>Month-over-Month Expense Analysis</span>'
        f'<span style="font-size:10px;color:var(--color-text-secondary)">Click group to expand · MoM% colour-coded</span>'
        f'</div>{mom_html}</div></div>'
        f'<div class="exp-panel" id="ep_{lid}_alerts">{alerts_html}</div>'
    )

    return (f'<div class="exp-loc-sec" id="els_{lid}">'
            f'{heading}{kpi_html}{tab_html}</div>')


# ═══════════════════════════════════════════════════════════════
#  MASTER REPORT BUILDER
# ═══════════════════════════════════════════════════════════════

def build_exp_report(df_raw, locations=None, loc_map=None, report_period=None):
    """
    Main entry point — call from app.py.

    Args:
        df_raw     : raw EXP CSV DataFrame (from Google Sheet / CSV upload)
        locations  : list of location strings to include (None = all)
        loc_map    : dict {loc_code: friendly_name} (None = use code as-is)
        report_period : string like 'Apr-25 to Apr-26'

    Returns:
        Complete HTML string ready for st.components.v1.html() or download.
    """
    df = prepare_exp_data(df_raw)

    all_locs = sorted([l for l in df['Location'].unique()
                       if l not in ['Gandh']])  # exclude incomplete
    if locations is None:
        locations = all_locs
    if loc_map is None:
        loc_map = {l: l for l in all_locs}

    months = get_available_months(df)
    period = report_period or (f'{months[0]} to {months[-1]}' if months else 'FY 25-26')
    gen_dt = datetime.now().strftime('%d-%b-%Y %H:%M')

    # ── Location selector options ──
    opts = '<option value="__ALL__">— All Locations —</option>'
    for loc in locations:
        lid = _loc_id(loc)
        opts += f'<option value="{lid}">{loc_map.get(loc, loc)} — {loc}</option>'

    loc_bar = (f'<div class="exp-loc-bar">'
               f'<label>Drill into Location</label>'
               f'<select id="exp-loc-sel" onchange="expSwitchLoc(this.value)">{opts}</select>'
               f'</div>')

    page_nav = (f'<div class="exp-page-nav">'
                f'<div class="epnav on" data-ep="mom" onclick="expShowPanel(\'mom\')">📊 MoM Trend</div>'
                f'<div class="epnav" data-ep="alerts" onclick="expShowPanel(\'alerts\')">🔔 AI Alerts</div>'
                f'</div>')

    # ── Executive Header ──
    hdr = (
        f'<div class="exp-exec-hdr">'
        f'<div class="exp-hdr-left">'
        f'<div class="exp-hdr-eyebrow">WSMIS Internal Audit Suite</div>'
        f'<div class="exp-hdr-title"><em>RKM</em> Motors — Expense Analysis</div>'
        f'<div class="exp-hdr-sub">Cost Control · {len(locations)} Locations · {len(months)} Months</div>'
        f'</div>'
        f'<div class="exp-hdr-right">'
        f'<div class="exp-hdr-period-pill">'
        f'<div class="exp-hdr-period-val">{period}</div>'
        f'<div class="exp-hdr-period-lbl">Generated {gen_dt}</div>'
        f'</div>'
        f'<div class="exp-live-badge"><span class="exp-live-dot"></span>Live</div>'
        f'<div class="exp-conf-badge">🔒 Confidential</div>'
        f'</div></div>'
    )

    # ── Summary dashboard block (shown when __ALL__ selected) ──
    dash_html = (
        f'<div class="exp-loc-sec" id="els___ALL__" style="display:none">'
        # 1. Alert Banner
        + build_alert_banner(df, locations, months)
        # 2. Executive KPIs
        + build_exec_kpis(df, locations, months)
        # 3. Expense Mix
        + build_expense_mix(df, locations, months)
        # 4. Two-col: Cost Centres + Donut
        + f'<div class="exp-section-label">Executive Dashboard</div>'
        + build_exec_dashboard_two_col(df, locations, loc_map, months)
        # 5. Monthly Trend
        + f'<div class="exp-section-label">Monthly Trend</div>'
        + build_monthly_trend(df, locations, months)
        # 6. Location Analysis
        + f'<div class="exp-section-label">Location Analysis</div>'
        + build_location_analysis(df, locations, loc_map, months)
        # 7. Transaction Drilldown
        + f'<div class="exp-section-label">Transaction Drilldown</div>'
        + build_transaction_drilldown(df, locations, months)
        # 8. Insights
        + f'<div class="exp-section-label">Executive Insights</div>'
        + build_exec_insights(df, locations, months)
        # 9. Action Panel
        + build_action_panel(df, locations, months)
        # 10. Summary table
        + f'<div class="exp-section-label">Full Location Summary</div>'
        + f'<div class="exp-sec"><div class="exp-sec-hdr">'
        + f'<span>All Locations — Expense Summary · {period}</span>'
        + f'<span style="font-size:10px;color:var(--color-text-secondary)">Click any row to drill in</span></div>'
        + build_exp_dashboard(df, locations, loc_map, months)
        + f'</div></div>'
    )

    # ── Per-location sections ──
    loc_sections = ''.join(build_loc_section(df, loc, loc_map) for loc in locations)

    body = hdr + loc_bar + page_nav + dash_html + loc_sections

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>RKM Expense Analysis — {period}</title>
  <style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px;
     background:#F0F2F5;color:#1C1C1E;-webkit-font-smoothing:antialiased}}
{EXP_CSS}
  </style>
</head>
<body>
<div class="exp-wrap">
{body}
  <div style="padding:14px;margin-top:8px;border-top:1px solid #E8ECF0;
              display:flex;justify-content:space-between;align-items:flex-start;
              flex-wrap:wrap;gap:8px;font-size:10px;color:var(--color-text-secondary);line-height:1.6">
    <div>
      <strong style="color:#374151;font-size:11px">CA Saurabh Jain &amp; Co.</strong> · Chartered Accountants · Internal Auditor, Rukmani Motors<br>
      RUKMANI Motors — Expense Analysis Report · {period} · Generated {gen_dt}<br>
      Data sourced from Google Sheet (EXP tab). MoM% computed from raw amounts.
      <div style="font-size:9px;font-weight:600;color:#991B1B;background:#FEE2E2;
                  border:1px solid #FECACA;padding:2px 8px;border-radius:4px;
                  letter-spacing:.06em;text-transform:uppercase;margin-top:4px;display:inline-block">
        ⚠ Strictly Confidential — For Authorised Personnel Only</div>
    </div>
    <div style="text-align:right">
      <strong style="color:#374151">Rukmani Motors</strong><br>
      Internal Audit Division<br>
      © CA Saurabh Jain &amp; Co. — All rights reserved.
    </div>
  </div>
</div>
<script>
{EXP_JS}
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
#  STREAMLIT INTEGRATION HELPER  (PRESERVED)
# ═══════════════════════════════════════════════════════════════

def render_in_streamlit(df_raw, locations=None, loc_map=None, report_period=None,
                        height=900, scrolling=True):
    """
    Convenience wrapper for use inside app.py.
    Call from the EXP tab section:

        import exp_report
        html = exp_report.render_in_streamlit(df_exp, loc_map=loc_map)

    Returns the HTML string (caller should pass to st.components.v1.html).
    """
    return build_exp_report(df_raw, locations=locations,
                            loc_map=loc_map, report_period=report_period)
