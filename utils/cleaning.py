import pandas as pd
import numpy as np
from typing import List, Dict

def normalize_advisor_name(name_series: pd.Series) -> pd.Series:
    """
    Normalizes advisor names by stripping anything after and including the hyphen.
    Preserves original capitalization and trims leading/trailing spaces.
    Converts repeated spaces to a single space.
    """
    return name_series.astype(str).str.split('-').str[0].str.strip().str.replace(r'\s+', ' ', regex=True)

def clean_dataframe(df: pd.DataFrame, adv_col: str, month_sort_order: Dict[str, int], pb_service_types: List[str]) -> pd.DataFrame:
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
            
    # Clean advisor names (canonical normalization)
    if adv_col in df.columns:
        df["Advisor_Raw"] = df[adv_col]
        # Only normalize names containing the suffix pattern
        df["Advisor_Clean"] = np.where(
            df[adv_col].astype(str).str.contains('-'),
            normalize_advisor_name(df[adv_col]),
            df[adv_col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
        )
        df[adv_col] = df["Advisor_Clean"]
        
        invalid_mask = df[adv_col].isin(['', '@', 'nan', 'N/A', 'None', 'nan']) | df[adv_col].isna()
        df.loc[invalid_mask, adv_col] = "Unassigned"
        df.loc[invalid_mask, "Advisor_Clean"] = "Unassigned"
            
    # Computed helper columns
    df['Location Name'] = df.get('Location Name', df.get('Location', 'Unknown'))
    
    # Business rule: Pre-GST Labour = Net Labour (no discount subtraction)
    # Business rule: Pre-GST Parts = Net Parts (no discount subtraction)
    if 'Pre-GST Labour' in df.columns:
        df['Net_Labour']     = df['Pre-GST Labour']
        if 'Labour Discount' in df.columns:
            df['Labour_Disc_Pct']= df['Labour Discount'] / df['Pre-GST Labour'].replace(0,np.nan) * 100
        
    if 'Pre-GST Parts' in df.columns:
        df['Net_Parts']      = df['Pre-GST Parts']
        if 'Parts Discount' in df.columns:
            df['Parts_Disc_Pct'] = df['Parts Discount']  / df['Pre-GST Parts'].replace(0,np.nan) * 100
        
    # Business rule: Avg Labour = Pre-GST Labour / Job Cards
    if 'Pre-GST Labour' in df.columns and 'JC_Nos.' in df.columns:
        df['Avg_Lab_per_JC'] = df['Pre-GST Labour'] / df['JC_Nos.'].replace(0,np.nan)
        
    if 'Pre-GST Parts' in df.columns and 'JC_Nos.' in df.columns:
        df['Avg_Parts_per_JC']= df['Pre-GST Parts'] / df['JC_Nos.'].replace(0,np.nan)
        
    if 'Net_Labour' in df.columns and 'Net_Parts' in df.columns:
        df['Lab_per_100_Parts']= df['Net_Labour'] / df['Net_Parts'].replace(0,np.nan) * 100
        
    if 'Month Name' in df.columns:
        df['Month Name'] = df['Month Name'].apply(lambda x: __import__('datetime').datetime.strptime(x, "%b-%y").strftime("%b-%Y") if isinstance(x, str) and '-' in x else x)

        sorted_months = sorted(month_sort_order.keys(), key=lambda k: month_sort_order[k])
        df['Month Name'] = pd.Categorical(df['Month Name'], categories=sorted_months, ordered=True)
        df['Month_Sort'] = df['Month Name'].map(month_sort_order).fillna(99).astype(int)
        
    if 'Service Type' in df.columns:
        df['Service_Type_Group'] = df['Service Type'].apply(lambda x: 'BS' if x in pb_service_types else 'WS')
        
    if 'Location Name' in df.columns:
        from utils.constants import PB_LOCATIONS
        df['Location_Group'] = df['Location Name'].apply(lambda x: 'PB' if x in PB_LOCATIONS else 'MP')

    return df
