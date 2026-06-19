import pandas as pd
from typing import Union, Dict

def _get_metric(df: pd.DataFrame, col_name: str, aggregate: bool = True) -> Union[float, pd.Series]:
    """Helper to safely extract and optionally sum a column."""
    if col_name not in df.columns:
        return 0.0 if aggregate else pd.Series(dtype=float, index=df.index if not df.empty else None)
    s = df[col_name]
    return float(s.sum()) if aggregate else s

def get_labour_sales(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Pre-GST Labour' - This is the canonical revenue column"""
    return _get_metric(df, "Pre-GST Labour", aggregate)

def get_parts_sales(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Pre-GST Parts' - This is the canonical revenue column"""
    return _get_metric(df, "Pre-GST Parts", aggregate)

def get_net_labour(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Pre-GST Labour' - Business rule: Pre-GST Labour = Net Labour (no discount subtraction)"""
    return _get_metric(df, "Pre-GST Labour", aggregate)

def get_net_parts(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Pre-GST Parts' - Business rule: Pre-GST Parts = Net Parts (no discount subtraction)"""
    return _get_metric(df, "Pre-GST Parts", aggregate)

def get_labour_discount(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Labour Discount'"""
    return _get_metric(df, "Labour Discount", aggregate)

def get_parts_discount(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Parts Discount'"""
    return _get_metric(df, "Parts Discount", aggregate)

def get_oil_sales(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Oil_Sale'"""
    return _get_metric(df, "Oil_Sale", aggregate)

def get_tyre_sales(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Tyre_Sale'"""
    return _get_metric(df, "Tyre_Sale", aggregate)

def get_battery_sales(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Battery_Sale'"""
    return _get_metric(df, "Battery_Sale", aggregate)

def get_accessory_sales(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Accessory_Sale'"""
    return _get_metric(df, "Accessory_Sale", aggregate)

def get_parts_profit(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Parts_Margin'"""
    return _get_metric(df, "Parts_Margin", aggregate)

def get_fsc_income(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'FSC Income'"""
    return _get_metric(df, "FSC Income", aggregate)

def get_otc_income(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'OTC Income'"""
    return _get_metric(df, "OTC Income", aggregate)

def get_msil_labour_claim(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'MSIL Labour Claim'"""
    return _get_metric(df, "MSIL Labour Claim", aggregate)

def get_internal_consumption(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Internal Consumption'"""
    return _get_metric(df, "Internal Consumption", aggregate)

def get_dealer_foc(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Dealer FOC'"""
    return _get_metric(df, "Dealer FOC", aggregate)

def get_vor_charges(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'VOR Charges'"""
    return _get_metric(df, "VOR Charges", aggregate)

def get_total_margin(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'Total Margin'"""
    return _get_metric(df, "Total Margin", aggregate)

def get_total_margin_column(df: pd.DataFrame) -> pd.Series:
    """Extracts 'Total Margin' as a Series"""
    return _get_metric(df, "Total Margin", aggregate=False)

def get_jobcard_count(df: pd.DataFrame, aggregate: bool = True) -> Union[float, pd.Series]:
    """Extracts 'JC_Nos.'"""
    return _get_metric(df, "JC_Nos.", aggregate)

def get_revenue_components(df: pd.DataFrame, aggregate: bool = True) -> Dict[str, Union[float, pd.Series]]:
    """Returns a dictionary of all revenue-related base components."""
    return {
        "Pre-GST Labour": get_labour_sales(df, aggregate),
        "Pre-GST Parts": get_parts_sales(df, aggregate),
        "Net_Labour": get_net_labour(df, aggregate),
        "Net_Parts": get_net_parts(df, aggregate),
        "Labour Discount": get_labour_discount(df, aggregate),
        "Parts Discount": get_parts_discount(df, aggregate),
    }

def get_margin_components(df: pd.DataFrame, aggregate: bool = True) -> Dict[str, Union[float, pd.Series]]:
    """Returns a dictionary of all margin-related base components."""
    return {
        "Parts_Margin": get_parts_profit(df, aggregate),
        "Oil_Margin": _get_metric(df, "Oil_Margin", aggregate),
        "Battery_Margin": _get_metric(df, "Battery_Margin", aggregate),
        "Tyre_Margin": _get_metric(df, "Tyre_Margin", aggregate),
        "Accessory_Margin": _get_metric(df, "Accessory_Margin", aggregate),
        "Other_Margin": _get_metric(df, "Other_Margin", aggregate),
        "FSC Income": get_fsc_income(df, aggregate),
        "OTC Income": get_otc_income(df, aggregate),
        "MSIL Labour Claim": get_msil_labour_claim(df, aggregate),
        "Internal Consumption": get_internal_consumption(df, aggregate),
        "Dealer FOC": get_dealer_foc(df, aggregate),
        "VOR Charges": get_vor_charges(df, aggregate),
        "Total Margin": get_total_margin(df, aggregate)
    }
