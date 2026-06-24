import re
import unicodedata
import pandas as pd
from dataclasses import dataclass
from typing import Optional
from services.error_handler import LoaderError


@dataclass
class TargetResult:
    """Structured result from a target lookup."""
    found: bool
    value: Optional[float]
    message: Optional[str]


REQUIRED_TARGET_COLS = [
    "Month Name", "Location Name",
    "WS_Labour_Target", "BS_Labour_Target",
    "WS_Parts_Target", "BS_Parts_Target",
]


def _normalize_key(value: object) -> str:
    """
    Unify a lookup key: NFKC-normalize, replace NBSP with space, strip,
    remove zero-width characters, collapse multiple spaces.

    Every lookup path (months, locations) calls this as the first step.
    Type-specific normalization (lowercasing, date parsing) is applied on
    top by the caller.
    """
    s = str(value)
    s = unicodedata.normalize('NFKC', s)
    s = s.replace('\u00a0', ' ')
    s = s.strip()
    s = re.sub(r'[\u200b\u200c\u200d\ufeff\u2060]', '', s)
    s = re.sub(r' {2,}', ' ', s)
    return s


class TargetProvider:
    """
    Encapsulates all logic related to fetching, formatting, and aggregating target 
    and benchmark thresholds. 
    Provides a canonical single source of truth across all modules.

    This layer returns structured TargetResult objects. It never imports streamlit,
    never writes to the UI, and never raises exceptions for missing targets.
    """

    def __init__(self, targets_df: pd.DataFrame):
        self._raw_df = targets_df.copy()

        # ── Schema validation ──────────────────────────────────────────────
        missing = [c for c in REQUIRED_TARGET_COLS if c not in self._raw_df.columns]
        if missing:
            raise LoaderError(
                f"TargetProvider: missing required columns: {', '.join(missing)}. "
                f"Expected: {', '.join(REQUIRED_TARGET_COLS)}"
            )

        if self._raw_df.empty:
            return

        # ── Normalize Month Name ───────────────────────────────────────────
        raw_months = self._raw_df["Month Name"].apply(_normalize_key)
        parsed = pd.to_datetime(raw_months, format="%b-%y", errors="coerce")
        self._raw_df["Month Name"] = parsed.dt.strftime("%b-%Y").fillna(raw_months)

        # ── Normalize Location Name ────────────────────────────────────────
        self._raw_df["Location Name"] = (
            self._raw_df["Location Name"]
            .apply(_normalize_key)
            .str.lower()
        )

        # ── Precomputed lookup keys ────────────────────────────────────────
        # One normalization pass — every lookup uses these columns.
        self._raw_df["_month_key"] = self._raw_df["Month Name"]
        self._raw_df["_location_key"] = self._raw_df["Location Name"]

    @staticmethod
    def _normalize_locations(locations: list) -> list:
        """Prepare location keys for matching: normalize key then lowercase."""
        return [_normalize_key(loc).lower() for loc in locations]

    @staticmethod
    def _normalize_months(months: list) -> list:
        """Normalize months to %b-%Y format regardless of input format (Mar-26 or Mar-2026)."""
        result = []
        for m in months:
            key = _normalize_key(m)
            if key:
                key = key[0].upper() + key[1:]
            parsed = pd.to_datetime(key, format="%b-%y", errors="coerce")
            if pd.isna(parsed):
                parsed = pd.to_datetime(key, format="%b-%Y", errors="coerce")
            if pd.notna(parsed):
                result.append(parsed.strftime("%b-%Y"))
            else:
                result.append(key)
        return result

    def _filter(self, locations: list, months: list) -> pd.DataFrame:
        """
        Perform normalised matching on both locations and months.
        Uses precomputed _month_key / _location_key columns — no repeated .apply().
        Returns the filtered DataFrame (may be empty).
        """
        if self._raw_df.empty:
            return pd.DataFrame()

        locs_norm = self._normalize_locations(locations)
        months_norm = self._normalize_months(months)

        mask = (
            self._raw_df["_location_key"].isin(locs_norm)
            & self._raw_df["_month_key"].isin(months_norm)
        )
        return self._raw_df[mask].drop(columns=["_month_key", "_location_key"])

    def get_location_targets(self, locations: list, months: list) -> pd.DataFrame:
        """
        Returns the raw target dataframe filtered for the requested locations and months.
        Useful for detailed breakdown pages like Targets or Discounts that merge row-by-row.
        """
        return self._filter(locations, months)

    def get_revenue_target(self, locations: list, months: list) -> TargetResult:
        """
        Returns the scalar sum of all WS/BS Labour and Parts targets for the specified scope.
        Used by Executive Command Center and summary KPIs.
        """
        tgt = self._filter(locations, months)
        if tgt.empty:
            return TargetResult(found=False, value=None, message="Target Not Configured")

        cols = ["WS_Labour_Target", "BS_Labour_Target", "WS_Parts_Target", "BS_Parts_Target"]
        valid_cols = [c for c in cols if c in tgt.columns]
        if not valid_cols:
            return TargetResult(found=False, value=None, message="Target Not Configured")

        result = float(tgt[valid_cols].apply(pd.to_numeric, errors='coerce').sum().sum())
        return TargetResult(found=True, value=result, message=None)

    def get_parts_target(self, locations: list, months: list) -> TargetResult:
        """
        Returns the scalar sum of all WS/BS Parts targets for the specified scope.
        Used by Parts Executive.
        """
        tgt = self._filter(locations, months)
        if tgt.empty:
            return TargetResult(found=False, value=None, message="No Target")

        cols = ["WS_Parts_Target", "BS_Parts_Target"]
        valid_cols = [c for c in cols if c in tgt.columns]
        if not valid_cols:
            return TargetResult(found=False, value=None, message="No Target")

        result = float(tgt[valid_cols].apply(pd.to_numeric, errors='coerce').sum().sum())
        return TargetResult(found=True, value=result, message=None)

    def get_discount_target(
        self,
        locations: list,
        months: list,
        revenue_df: Optional[pd.DataFrame] = None,
    ) -> TargetResult:
        """
        Calculates the average approved discount for the specified scope.
        If revenue_df is provided (DataFrame with Location Name and Net_Labour columns),
        computes a revenue-weighted average using Net_Labour as the canonical weighting metric.
        Otherwise, a simple average.

        When no target data is found, returns the configured default benchmark
        with found=False so the UI can display a fallback message.
        """
        from config.settings import LABOUR_DISC_BENCH

        tgt = self._filter(locations, months)

        if tgt.empty or "Appr_Lab_Disc" not in tgt.columns:
            return TargetResult(
                found=False,
                value=float(LABOUR_DISC_BENCH),
                message="Using Default Benchmark",
            )

        if revenue_df is not None and not revenue_df.empty:
            # Compute revenue weights using canonical Net_Labour metric
            # Normalize revenue_df Location Name to match target keys
            rev_df = revenue_df.copy()
            rev_df["Location Name"] = rev_df["Location Name"].apply(_normalize_key).str.lower()
            revenue_weights = rev_df.groupby("Location Name")["Net_Labour"].sum().to_dict()

            total_weight = 0.0
            weighted_sum = 0.0

            loc_tgt = tgt.groupby("Location Name")["Appr_Lab_Disc"].apply(
                lambda x: pd.to_numeric(x, errors="coerce").mean()
            ).reset_index()

            for _, row in loc_tgt.iterrows():
                loc = row["Location Name"]
                val = row["Appr_Lab_Disc"]
                if pd.isna(val):
                    continue
                weight = revenue_weights.get(loc, 0.0)
                weighted_sum += val * weight
                total_weight += weight

            if total_weight > 0:
                return TargetResult(found=True, value=float(weighted_sum / total_weight), message=None)

        # Simple average fallback
        result = float(pd.to_numeric(tgt["Appr_Lab_Disc"], errors="coerce").mean())
        return TargetResult(found=True, value=result, message=None)
