import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ai.report_generator import generate_report

def main():
    load_dotenv()
    
    print("Testing WSMIS Gemini AI Integration...")
    print("-" * 50)
    
    # Mock minimal context to avoid needing full dataframes
    mock_context = {
        "meta": {"client": "Rukmani Motors (Pilot)", "period": "Jun-26", "comparison": "YoY"},
        "current_period": {"total_revenue": 15000000, "total_margin": 3000000, "job_cards": 2500, "labour_discount_pct": 18.5},
        "prior_period": {"total_revenue": 14000000, "total_margin": 2800000, "job_cards": 2400, "labour_discount_pct": 16.0},
        "growth": {"revenue_pct": 7.1, "margin_pct": 7.1, "jc_pct": 4.1},
        "business_health": {"score": 78, "label": "Stable"},
        "benchmarks": {"labour_discount_pct": 15.0},
        "leakage": [{"entity": "Global", "scope": "Labour", "level": "Total", "discount_pct": 18.5, "benchmark_pct": 15.0, "recoverable": 50000}],
        "opportunities": [{"title": "Cross-sell Accessories", "entity": "Global", "impact": "Increase Revenue", "estimated_value": 150000, "owner": "Branch Manager"}],
        "top_locations": [],
        "top_advisors": [],
        "risks": [{"title": "High Labour Discount", "entity": "Global", "impact": "Margin Drain", "detail": "18.5% > 15%", "recommended_action": "Enforce strict approval for >15% discounts"}]
    }

    try:
        report = generate_report(context=mock_context, provider="gemini")
        print(f"Provider Used: {report.provider}")
        print(f"Model Used: {report.model}")
        print("-" * 50)
        print("GENERATED REPORT PREVIEW (First 500 chars):")
        print(report.markdown[:500].encode('ascii', errors='replace').decode('ascii') + "\n...\n")
        print("-" * 50)
        if report.provider == "offline (fallback)":
            print("[OK] Fallback to offline rendered successfully (Expected if API key missing/invalid).")
        else:
            print("[OK] Gemini AI returned successfully.")
    except Exception as e:
        print(f"[X] Unhandled Exception occurred: {e}")

if __name__ == "__main__":
    main()
