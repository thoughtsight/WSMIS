import pandas as pd

class TargetProvider:
    """
    Encapsulates all logic related to fetching, formatting, and aggregating target 
    and benchmark thresholds. 
    Provides a canonical single source of truth across all modules.
    """
    
    def __init__(self, targets_df: pd.DataFrame):
        self._raw_df = targets_df.copy()
        
        # 1. Normalize the month format to ensure matching
        if not self._raw_df.empty and "Month Name" in self._raw_df.columns:
            # Map Apr-26 -> Apr-2026 safely
            normalized = pd.to_datetime(
                self._raw_df["Month Name"], format="%b-%y", errors="coerce"
            ).dt.strftime("%b-%Y")
            
            # Fill any NaN resulting from parsing errors with the original string
            self._raw_df["Month Name"] = normalized.fillna(self._raw_df["Month Name"])
            
    def get_location_targets(self, locations: list, months: list) -> pd.DataFrame:
        """
        Returns the raw target dataframe filtered for the requested locations and months.
        Useful for detailed breakdown pages like Targets or Discounts that merge row-by-row.
        """
        if self._raw_df.empty:
            return pd.DataFrame()
            
        mask = (self._raw_df["Month Name"].isin(months)) & (self._raw_df["Location Name"].isin(locations))
        return self._raw_df[mask]

    def get_revenue_target(self, locations: list, months: list) -> float:
        """
        Returns the scalar sum of all WS/BS Labour and Parts targets for the specified scope.
        Used by Executive Command Center and summary KPIs.
        """
        tgt = self.get_location_targets(locations, months)
        if tgt.empty:
            return 0.0
            
        cols = ["WS_Labour_Target", "BS_Labour_Target", "WS_Parts_Target", "BS_Parts_Target"]
        # Ensure columns exist before summing
        valid_cols = [c for c in cols if c in tgt.columns]
        if not valid_cols:
            return 0.0
            
        return float(tgt[valid_cols].apply(pd.to_numeric, errors='coerce').sum().sum())

    def get_parts_target(self, locations: list, months: list) -> float:
        """
        Returns the scalar sum of all WS/BS Parts targets for the specified scope.
        Used by Parts Executive.
        """
        tgt = self.get_location_targets(locations, months)
        if tgt.empty:
            return 0.0
            
        cols = ["WS_Parts_Target", "BS_Parts_Target"]
        valid_cols = [c for c in cols if c in tgt.columns]
        if not valid_cols:
            return 0.0
            
        return float(tgt[valid_cols].apply(pd.to_numeric, errors='coerce').sum().sum())
        
    def get_discount_target(self, locations: list, months: list, revenue_df: pd.DataFrame = None) -> float:
        """
        Calculates the average approved discount for the specified scope.
        If revenue_df is provided (DataFrame with Location Name and Net_Labour columns),
        computes a revenue-weighted average using Net_Labour as the canonical weighting metric.
        Otherwise, a simple average.
        """
        tgt = self.get_location_targets(locations, months)
        if tgt.empty or "Appr_Lab_Disc" not in tgt.columns:
            return 15.0 # Fallback safety default
            
        if revenue_df is not None and not revenue_df.empty:
            # Compute revenue weights using canonical Net_Labour metric
            revenue_weights = revenue_df.groupby("Location Name")["Net_Labour"].sum().to_dict()
            
            total_weight = 0.0
            weighted_sum = 0.0
            
            # Since multiple months could be passed, group by location and average the target
            loc_tgt = tgt.groupby("Location Name")["Appr_Lab_Disc"].apply(
                lambda x: pd.to_numeric(x, errors="coerce").mean()
            ).reset_index()
            
            for _, row in loc_tgt.iterrows():
                loc = row["Location Name"]
                val = row["Appr_Lab_Disc"]
                if pd.isna(val): continue
                
                weight = revenue_weights.get(loc, 0.0)
                weighted_sum += val * weight
                total_weight += weight
                
            if total_weight > 0:
                return float(weighted_sum / total_weight)
                
        # Simple average fallback if no revenue_df provided or total weight is zero
        return float(pd.to_numeric(tgt["Appr_Lab_Disc"], errors="coerce").mean())
