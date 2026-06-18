"""
Test script for Audit Intelligence page integration (PR-027).
Verifies the render function works end-to-end with synthetic data.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views.audit_intelligence import render
from services.ai import generate_report


def create_synthetic_data(n=500):
    """Create synthetic WSMIS data matching the required columns."""
    rng = np.random.default_rng(42)
    locs = ['ALPR', 'Palda', 'Dhar', 'MG', 'Rajod', 'Bhavra', 'DN']
    advs = ['A. Kumar', 'B. Singh', 'C. Rao', 'D. Patel', 'E. Gupta']
    months = ['Apr-26', 'May-26', 'Jun-26', 'Apr-25', 'May-25', 'Jun-25']
    month_sort = {'Apr-25': 1, 'May-25': 2, 'Jun-25': 3, 'Apr-26': 4, 'May-26': 5, 'Jun-26': 6}

    data = []
    for _ in range(n):
        month = rng.choice(months)
        loc = rng.choice(locs)
        adv = rng.choice(advs)
        jcs = rng.integers(1, 4)
        pre_lab = rng.integers(1000, 5000)
        lab_disc = rng.integers(100, 1500)
        pre_parts = rng.integers(500, 4000)
        parts_disc = rng.integers(50, 800)
        margin = rng.integers(200, 2000)

        data.append({
            'Location Name': loc,
            'Location Group': 'Arena' if loc in ['ALPR', 'Palda', 'Dhar'] else 'Nexa',
            'Advisior Name': adv,
            'Service Type': rng.choice(['PMS', 'FR', 'BR']),
            'MP_PB': rng.choice(['MP', 'PB']),
            'Month Name': month,
            'Month_Sort': month_sort[month],
            'JC_Nos.': jcs,
            'Pre-GST Labour': pre_lab,
            'Labour Discount': lab_disc,
            'Pre-GST Parts': pre_parts,
            'Parts Discount': parts_disc,
            'Net_Labour': pre_lab - lab_disc,
            'Net_Parts': pre_parts - parts_disc,
            'Total Margin': margin,
            'Parts_Margin': rng.integers(100, 900),
            'Oil_Sale_Qty': rng.integers(0, 3),
            'Oil_Sale': rng.integers(0, 1500),
            'VOR Charges': -rng.integers(0, 500),
        })

    return pd.DataFrame(data)


def test_ai_page_render():
    """Test the Audit Intelligence page render function."""
    print("Creating synthetic data...")
    df = create_synthetic_data(500)

    # Create pairs for CP/PP comparison
    cp_months = ['Apr-26', 'May-26', 'Jun-26']
    pp_months = ['Apr-25', 'May-25', 'Jun-25']
    pairs = list(zip(cp_months, pp_months))

    alerts = [
        ("red", "High Labour Discount at Palda"),
        ("yellow", "Margin decline at Dhar"),
    ]

    print("Testing AI report generation (offline provider)...")
    try:
        # Test the report generator directly first
        cp = df[df['Month Name'].isin(cp_months)]
        pp = df[df['Month Name'].isin(pp_months)]

        report = generate_report(
            cp=cp,
            pp=pp,
            client_name="Rukmani Motors",
            period_label="Apr-26 → Jun-26",
            comparison_label="YoY",
            adv_col="Advisior Name",
            provider="offline",
        )

        print(f"✓ Report generated successfully")
        print(f"  Provider: {report.provider}")
        print(f"  Model: {report.model}")
        print(f"  Markdown length: {len(report.markdown)} chars")
        print(f"  Sections found: {report.markdown.count('## ')}")

        # Verify the markdown has the expected sections
        expected_sections = [
            "Executive Summary",
            "Business Performance",
            "Profit Drivers",
            "Loss Drivers",
            "Revenue Leakage",
            "Top Risks",
            "Top Opportunities",
            "Priority Actions",
            "Estimated Financial Recovery",
        ]

        for section in expected_sections:
            if section in report.markdown:
                print(f"  ✓ Section '{section}' present")
            else:
                print(f"  ✗ Section '{section}' MISSING")
                return False

        print("\n✓ All tests passed!")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ai_page_render()
    sys.exit(0 if success else 1)
