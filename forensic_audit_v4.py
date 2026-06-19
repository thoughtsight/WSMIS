"""
Forensic Audit Script V4 - Check advisor filtering
"""
import pandas as pd
import numpy as np
from utils.loaders import load_raw_worksheet
from utils.constants import ADV_COL, MONTH_SORT_ORDER, PB_SERVICE_TYPES, CLIENTS

def main():
    print("FORENSIC AUDIT V4: Check advisor filtering")
    print("="*80)
    
    # Get client config
    client_config = list(CLIENTS.values())[0]
    sheet_id = client_config["sheet_id"]
    sheet_tab = client_config["sheet_tab"]
    
    print(f"\nSheet ID: {sheet_id}")
    print(f"Sheet Tab: {sheet_tab}")
    
    # Load raw data
    df_raw = load_raw_worksheet(sheet_id, sheet_tab)
    
    print(f"\nTotal rows in raw worksheet: {len(df_raw)}")
    
    # Check advisor column
    if ADV_COL in df_raw.columns:
        print(f"\nAdvisor column: {ADV_COL}")
        
        # Check Feb-25 and Mar-25 advisor values
        feb_25_df = df_raw[df_raw['Month Name'] == 'Feb-25']
        mar_25_df = df_raw[df_raw['Month Name'] == 'Mar-25']
        
        print(f"\nFeb-25 rows: {len(feb_25_df)}")
        print(f"Advisor values in Feb-25:")
        print(feb_25_df[ADV_COL].value_counts().head(20).to_string())
        
        print(f"\nMar-25 rows: {len(mar_25_df)}")
        print(f"Advisor values in Mar-25:")
        print(mar_25_df[ADV_COL].value_counts().head(20).to_string())
        
        # Check which advisors would be filtered out
        print(f"\nApplying advisor filter from clean_dataframe line 33-34:")
        mask = df_raw[ADV_COL].notna() & ~df_raw[ADV_COL].astype(str).str.strip().isin(['', '@', 'nan', 'N/A'])
        print(f"Rows before advisor filter: {len(df_raw)}")
        print(f"Rows after advisor filter: {len(df_raw[mask])}")
        print(f"Rows removed: {len(df_raw) - len(df_raw[mask])}")
        
        # Check Feb-25 and Mar-25 after advisor filter
        feb_25_after = df_raw[mask & (df_raw['Month Name'] == 'Feb-25')]
        mar_25_after = df_raw[mask & (df_raw['Month Name'] == 'Mar-25')]
        
        print(f"\nFeb-25 after advisor filter: {len(feb_25_after)}")
        print(f"Mar-25 after advisor filter: {len(mar_25_after)}")
        
        # Check which advisors are being removed from Feb-25
        feb_25_removed = feb_25_df[~feb_25_df.index.isin(feb_25_after.index)]
        print(f"\nFeb-25 advisors being removed:")
        if not feb_25_removed.empty:
            print(feb_25_removed[ADV_COL].value_counts().to_string())
        else:
            print("None")
        
        # Check which advisors are being removed from Mar-25
        mar_25_removed = mar_25_df[~mar_25_df.index.isin(mar_25_after.index)]
        print(f"\nMar-25 advisors being removed:")
        if not mar_25_removed.empty:
            print(mar_25_removed[ADV_COL].value_counts().to_string())
        else:
            print("None")

if __name__ == "__main__":
    main()
