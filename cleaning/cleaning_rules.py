import re
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from engine.type_inference import EMAIL_REGEX

class CleaningOperations:
    """
    Pure transformation functions that take a DataFrame and parameters,
    and return (transformed_df, changes_summary).
    Never modifies the original DataFrame in-place.
    """

    @classmethod
    def impute_missing(cls, df: pd.DataFrame, column: str, strategy: str = "median", fill_value: Any = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_copy = df.copy()
        if column not in df_copy.columns:
            return df_copy, {"modified_rows": 0}

        series = df_copy[column]
        mask = series.isna() | (series.astype(str).str.strip() == "")
        count = int(mask.sum())

        if count == 0:
            return df_copy, {"modified_rows": 0}

        if strategy == "median":
            num_series = pd.to_numeric(series, errors="coerce")
            replacement = round(float(num_series.median()), 2) if not num_series.dropna().empty else 0.0
        elif strategy == "mean":
            num_series = pd.to_numeric(series, errors="coerce")
            replacement = round(float(num_series.mean()), 2) if not num_series.dropna().empty else 0.0
        elif strategy == "mode":
            mode_vals = series.dropna().mode()
            replacement = mode_vals.iloc[0] if not mode_vals.empty else "Unknown"
        else:
            replacement = fill_value if fill_value is not None else ("Unknown" if not pd.api.types.is_numeric_dtype(series) else 0)

        # Cast to object if trying to put a string into a numeric column
        if pd.api.types.is_numeric_dtype(df_copy[column]) and isinstance(replacement, str):
            df_copy[column] = df_copy[column].astype(object)

        df_copy.loc[mask, column] = replacement
        return df_copy, {
            "operation": f"Imputed missing with {strategy} ({replacement})",
            "column": column,
            "modified_rows": count
        }

    @classmethod
    def drop_duplicates(cls, df: pd.DataFrame, subset=None, keep: str = "first") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_copy = df.copy()
        cols_to_check = subset if subset else [c for c in df_copy.columns if c != "_row_number"]
        initial_len = len(df_copy)
        df_copy = df_copy.drop_duplicates(subset=cols_to_check, keep=keep)
        removed_count = initial_len - len(df_copy)
        return df_copy, {
            "operation": f"Dropped duplicates (keep='{keep}')",
            "column": str(subset) if subset else "All columns",
            "modified_rows": removed_count
        }

    @classmethod
    def trim_whitespace(cls, df: pd.DataFrame, column: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_copy = df.copy()
        if column not in df_copy.columns:
            return df_copy, {"modified_rows": 0}

        series = df_copy[column]
        str_series = series.astype(str)
        trimmed = str_series.str.strip()
        mask = (str_series != trimmed) & series.notna()
        count = int(mask.sum())

        df_copy.loc[series.notna(), column] = trimmed[series.notna()]
        return df_copy, {
            "operation": "Trimmed leading and trailing whitespace",
            "column": column,
            "modified_rows": count
        }

    @classmethod
    def standardize_casing(cls, df: pd.DataFrame, column: str, target_case: str = "title") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_copy = df.copy()
        if column not in df_copy.columns:
            return df_copy, {"modified_rows": 0}

        series = df_copy[column]
        valid_mask = series.notna()

        if target_case == "upper":
            transformed = series[valid_mask].astype(str).str.strip().str.upper()
        elif target_case == "lower":
            transformed = series[valid_mask].astype(str).str.strip().str.lower()
        else:
            transformed = series[valid_mask].astype(str).str.strip().str.title()

        changed_mask = (series[valid_mask].astype(str) != transformed)
        count = int(changed_mask.sum())

        df_copy.loc[valid_mask, column] = transformed
        return df_copy, {
            "operation": f"Standardized casing to {target_case}",
            "column": column,
            "modified_rows": count
        }

    @classmethod
    def cap_outliers(cls, df: pd.DataFrame, column: str, lower_bound: float, upper_bound: float) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_copy = df.copy()
        if column not in df_copy.columns:
            return df_copy, {"modified_rows": 0}

        series = pd.to_numeric(df_copy[column], errors="coerce")
        outlier_mask = (series < lower_bound) | (series > upper_bound)
        count = int(outlier_mask.sum())

        df_copy[column] = series.clip(lower=lower_bound, upper=upper_bound)
        return df_copy, {
            "operation": f"Winsorized/capped values to [{lower_bound}, {upper_bound}]",
            "column": column,
            "modified_rows": count
        }

    @classmethod
    def fix_negatives(cls, df: pd.DataFrame, column: str, strategy: str = "absolute_value") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_copy = df.copy()
        if column not in df_copy.columns:
            return df_copy, {"modified_rows": 0}

        series = pd.to_numeric(df_copy[column], errors="coerce")
        negative_mask = series < 0
        count = int(negative_mask.sum())

        if strategy == "zero":
            df_copy.loc[negative_mask, column] = 0
        else:
            df_copy.loc[negative_mask, column] = series[negative_mask].abs()

        return df_copy, {
            "operation": f"Corrected negative values ({strategy})",
            "column": column,
            "modified_rows": count
        }

    @classmethod
    def nullify_invalid_emails(cls, df: pd.DataFrame, column: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_copy = df.copy()
        if column not in df_copy.columns:
            return df_copy, {"modified_rows": 0}

        series = df_copy[column]
        non_null_mask = series.notna() & (series.astype(str).str.strip() != "")
        str_series = series[non_null_mask].astype(str).str.strip()

        invalid_mask = ~str_series.str.match(EMAIL_REGEX.pattern)
        invalid_indices = str_series[invalid_mask].index
        count = len(invalid_indices)

        df_copy.loc[invalid_indices, column] = np.nan
        return df_copy, {
            "operation": "Nullified invalid email formats",
            "column": column,
            "modified_rows": count
        }

    @classmethod
    def standardize_dates(cls, df: pd.DataFrame, column: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_copy = df.copy()
        if column not in df_copy.columns:
            return df_copy, {"modified_rows": 0}

        series = df_copy[column]
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")
        formatted = parsed.dt.strftime("%Y-%m-%d")
        count = int((series.astype(str) != formatted.astype(str)).sum())

        df_copy[column] = formatted
        return df_copy, {
            "operation": "Standardized dates to YYYY-MM-DD",
            "column": column,
            "modified_rows": count
        }
