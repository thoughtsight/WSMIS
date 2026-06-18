import numpy as np
import pandas as pd
from typing import List, Dict, Any

from utils.calculations.common import calc_ratio, calc_growth_pct
from utils.calculations.fact_metrics import get_vor_charges
from utils.aggregations import location_summary, advisor_summary
from services.benchmark_provider import BenchmarkProvider
from ui.formatters import fmt_inr, fmt_pct
from utils.constants import ADV_COL

class ExecutiveAlertEngine:
    def __init__(self, provider: BenchmarkProvider):
        self.provider = provider
        
    def evaluate(self, df_cp: pd.DataFrame, df_pp: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
        critical = []
        warning = []
        opportunities = []
        
        # Benchmarks
        high_disc_bench = self.provider.get_benchmark("high_discount_alert")
        labour_disc_target = self.provider.get_benchmark("labour_discount_target")
        yoy_decline_bench = self.provider.get_benchmark("yoy_decline_alert")
        vor_alert_bench = self.provider.get_benchmark("vor_alert_threshold")

        # 1. High Labour Discount Alert (Critical)
        if not df_cp.empty:
            loc_disc = location_summary(df_cp, as_index=True).agg(
                L=('Pre-GST Labour', 'sum'), D=('Labour Discount', 'sum')
            )
            loc_disc['D%'] = calc_ratio(loc_disc['D'], loc_disc['L'], multiplier=100, fill_value=np.nan)
            high_disc_df = loc_disc[loc_disc['D%'] > high_disc_bench]
            
            if not high_disc_df.empty:
                locations = high_disc_df.index.tolist()
                avg_val = high_disc_df['D%'].mean()
                variance = avg_val - high_disc_bench
                leakage = sum([(row['D%'] - labour_disc_target) / 100 * row['L'] for _, row in high_disc_df.iterrows()])
                
                critical.append({
                    "rule": "High Labour Discount",
                    "current": f"{avg_val:.2f}%",
                    "benchmark": f"{high_disc_bench}%",
                    "variance": f"+{variance:.2f}%",
                    "impact": fmt_inr(leakage),
                    "reason": f"{len(locations)} locations exceeded configured labour discount benchmark.",
                    "locations": ", ".join(locations),
                    "advisors": "Multiple",
                    "action": "Review advisor approvals and discount matrices.",
                    "owner": "Workshop Manager",
                    "why": {
                        "rule": "High Labour Discount",
                        "threshold": f">{high_disc_bench}%",
                        "current": f"{avg_val:.2f}%",
                        "calculation": "Sum(Labour Discount) / Sum(Pre-GST Labour)",
                        "rows": len(df_cp[df_cp['Location Name'].isin(locations)]),
                        "locations": locations,
                        "impact_rationale": f"Estimated leakage vs target ({labour_disc_target}%)"
                    }
                })
                
        # 2. YoY Decline (Critical)
        if not df_cp.empty and not df_pp.empty:
            loc_cp = location_summary(df_cp, as_index=True)['Net_Labour'].sum()
            loc_pp = location_summary(df_pp, as_index=True)['Net_Labour'].sum()
            declining_locs = []
            total_lost = 0
            worst_yoy = 0
            
            for loc in loc_cp.index:
                if loc in loc_pp.index and loc_pp[loc] > 50000:
                    yoy = calc_growth_pct(loc_cp[loc], loc_pp[loc], fill_value=np.nan)
                    if not np.isnan(yoy) and yoy < -yoy_decline_bench:
                        declining_locs.append(loc)
                        total_lost += (loc_pp[loc] - loc_cp[loc])
                        worst_yoy = min(worst_yoy, yoy)
                        
            if declining_locs:
                critical.append({
                    "rule": "Severe Revenue Decline",
                    "current": f"{worst_yoy:.2f}% (worst)",
                    "benchmark": f"-{yoy_decline_bench}%",
                    "variance": f"{worst_yoy + yoy_decline_bench:.2f}%",
                    "impact": fmt_inr(total_lost),
                    "reason": f"{len(declining_locs)} locations showed massive YoY revenue drop.",
                    "locations": ", ".join(declining_locs),
                    "advisors": "N/A",
                    "action": "Investigate underlying drop in volume or ticket size.",
                    "owner": "General Manager",
                    "why": {
                        "rule": "YoY Revenue Decline",
                        "threshold": f"<-{yoy_decline_bench}%",
                        "current": f"{worst_yoy:.2f}%",
                        "calculation": "(CP Net Labour - PP Net Labour) / PP Net Labour",
                        "rows": len(df_cp[df_cp['Location Name'].isin(declining_locs)]),
                        "locations": declining_locs,
                        "impact_rationale": "Lost revenue compared to prior period"
                    }
                })

        # 3. VOR Charges (Warning)
        if not df_cp.empty:
            vor = get_vor_charges(df_cp)
            if vor < -vor_alert_bench:
                warning.append({
                    "rule": "Elevated VOR Charges",
                    "current": fmt_inr(abs(vor)),
                    "benchmark": fmt_inr(vor_alert_bench),
                    "variance": fmt_inr(abs(vor) - vor_alert_bench),
                    "impact": fmt_inr(abs(vor)),
                    "reason": "Excessive ordering costs detected in parts inventory.",
                    "locations": "Group Wide",
                    "advisors": "Parts Manager",
                    "action": "Review inventory management and fast-moving stock availability.",
                    "owner": "Parts Manager",
                    "why": {
                        "rule": "Elevated VOR Charges",
                        "threshold": f">{fmt_inr(vor_alert_bench)}",
                        "current": fmt_inr(abs(vor)),
                        "calculation": "Sum of VOR related charge codes",
                        "rows": len(df_cp[df_cp['Service Type'] == 'VOR']),
                        "locations": "All",
                        "impact_rationale": "Direct bottom line hit due to emergency stock orders"
                    }
                })

        # 4. Opportunity: Recoverable Discount
        if not df_cp.empty:
            adv_disc = advisor_summary(df_cp, adv_col=ADV_COL, as_index=True).agg(
                L=('Pre-GST Labour', 'sum'), D=('Labour Discount', 'sum')
            )
            adv_disc['D%'] = calc_ratio(adv_disc['D'], adv_disc['L'], multiplier=100, fill_value=np.nan)
            recoverable_df = adv_disc[adv_disc['D%'] > labour_disc_target].copy()
            if not recoverable_df.empty:
                potential_gain = sum([(row['D%'] - labour_disc_target) / 100 * row['L'] for _, row in recoverable_df.iterrows()])
                if potential_gain > 5000:
                    opportunities.append({
                        "opportunity": "Discount Optimization",
                        "situation": f"{len(recoverable_df)} advisors above target {labour_disc_target}% discount.",
                        "gain": fmt_inr(potential_gain),
                        "basis": f"Reducing discount to benchmark {labour_disc_target}%",
                        "benefit": "Direct margin improvement without volume increase.",
                        "action": "Implement strict approval workflow for discounts above benchmark.",
                        "owner": "Service Head",
                        "priority": "High" if potential_gain > 50000 else "Medium"
                    })

        return {
            "critical": critical,
            "warning": warning,
            "opportunities": opportunities
        }
