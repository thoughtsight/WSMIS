import pandas as pd
import numpy as np
from typing import List, Dict

def clean_dataframe(df: pd.DataFrame, adv_col: str, month_sort_order: Dict[str, int], bs_service_types: List[str]) -> pd.DataFrame:
    """
    Applies deterministic structural cleaning to the raw DataFrame.
    """
    if df is None or df.empty:
        return df

    # Column trimming and Strip %
    for col in ["Labour Dis.(%)", "Parts Dis(%)"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("%", "", regex=False)
            
    # Numeric conversion
    nums = [
        "JC_Nos.", "Pre-GST Labour", "Labour Discount", "Pre-GST Parts",
        "Parts Discount", "Parts_Sale", "Accessory_Sale", "Oil_Sale",
        "Oil_Sale_Qty", "Tyre_Sale", "Tyre_Sale_Qty", "Battery_Sale",
        "Battery_Sale_Qty", "Other_Sale", "Parts_Margin", "Accessory_Margin",
        "Oil_Margin", "Tyre_Margin", "Battery_Margin", "Other_Margin",
        "Labour Dis.(%)", "Parts Dis(%)", "Total Margin", "VOR Charges",
        "OTC Income", "MSIL Labour Claim", "FSC Income", "Dealer FOC", "Internal Consumption"
    ]
    for c in nums:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce", downcast="float").fillna(0)
            
    # Clean advisor names
    if adv_col in df.columns:
        mask = df[adv_col].notna() & ~df[adv_col].astype(str).str.strip().isin(['', '@', 'nan', 'N/A'])
        df = df[mask]
        df.loc[:, adv_col] = df[adv_col].astype(str).str.strip()
            
    # Computed helper columns
    df['Location Name'] = df.get('Location Name', df.get('Location', 'Unknown'))
    
    if 'Pre-GST Labour' in df.columns and 'Labour Discount' in df.columns:
        df['Net_Labour']     = df['Pre-GST Labour'] - df['Labour Discount']
        df['Labour_Disc_Pct']= df['Labour Discount'] / df['Pre-GST Labour'].replace(0,np.nan) * 100
        
    if 'Pre-GST Parts' in df.columns and 'Parts Discount' in df.columns:
        df['Net_Parts']      = df['Pre-GST Parts']  - df['Parts Discount']
        df['Parts_Disc_Pct'] = df['Parts Discount']  / df['Pre-GST Parts'].replace(0,np.nan) * 100
        
    if 'Net_Labour' in df.columns and 'JC_Nos.' in df.columns:
        df['Avg_Lab_per_JC'] = df['Net_Labour'] / df['JC_Nos.'].replace(0,np.nan)
        
    if 'Net_Parts' in df.columns and 'JC_Nos.' in df.columns:
        df['Avg_Parts_per_JC']= df['Net_Parts'] / df['JC_Nos.'].replace(0,np.nan)
        
    if 'Net_Labour' in df.columns and 'Net_Parts' in df.columns:
        df['Lab_per_100_Parts']= df['Net_Labour'] / df['Net_Parts'].replace(0,np.nan) * 100
        
    if 'Month Name' in df.columns:
        sorted_months = sorted(month_sort_order.keys(), key=lambda k: month_sort_order[k])
        df['Month Name'] = pd.Categorical(df['Month Name'], categories=sorted_months, ordered=True)
        df['Month_Sort'] = df['Month Name'].map(month_sort_order).fillna(99).astype(int)
        
    if 'Service Type' in df.columns:
        df['WS_BS']          = df['Service Type'].apply(lambda x: 'BS' if x in bs_service_types else 'WS')

    return df
