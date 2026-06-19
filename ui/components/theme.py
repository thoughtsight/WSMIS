EXECUTIVE_THEME_CSS = """
<style>
/* Executive Summary Layout Container */
.exec-heading { 
    font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; 
    color: #a1a1a6; margin: 24px 0 12px 0; 
}
.kpi-wrapper { 
    display: flex; gap: 16px; margin-bottom: 16px; 
}

/* Base KPI Card */
.kpi-box { 
    flex: 1; background: #232323; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
}
.kpi-title { 
    font-size: 12px; font-weight: 500; color: #a1a1a6; text-transform: uppercase; margin-bottom: 6px; 
}
.kpi-val { 
    font-size: 36px; font-weight: 700; color: #ffffff; line-height: 1.2; margin-bottom: 6px; 
}
.kpi-footer { 
    display: flex; align-items: baseline; gap: 8px; font-size: 14px; font-weight: 500; 
}

/* Indicators */
.g-pos { color: #34c759; font-weight: 600; }
.g-neg { color: #ff3b30; font-weight: 600; }
.pp-val { color: #a1a1a6; }

/* Service Panels (PMS/Bodyshop) */
.svc-panel { padding: 16px 20px; }
.svc-row { 
    display: flex; justify-content: space-between; align-items: center; 
    padding: 10px 0; border-bottom: 1px solid #333333; 
}
.svc-row:last-child { border-bottom: none; padding-bottom: 0; }
.svc-label { color: #a1a1a6; font-size: 13px; font-weight: 500; }
.svc-vals { display: flex; align-items: baseline; justify-content: flex-end; gap: 12px; }
.svc-cp { color: #ffffff; font-weight: 700; width: 80px; text-align: right; font-size: 16px; }
.svc-cp-tag { color: #34c759; font-size: 11px; font-weight: 600; margin-left: 2px; }
.svc-pp { color: #a1a1a6; font-weight: 500; width: 70px; text-align: right; font-size: 14px; }
</style>
"""
