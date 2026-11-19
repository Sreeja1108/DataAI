import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
from cleaning.cleaning_rules import CleaningOperations
from config import Config

logger = logging.getLogger(__name__)

class CleaningEngine:
    """
    Coordinates safe, interactive data cleaning.
    Allows users to preview before-and-after values and approves individual fixes.
    Preserves original uploaded data and exports cleaned datasets.
    """

    @classmethod
    def get_suggested_value_desc(cls, df: pd.DataFrame, issue: Dict[str, Any]) -> str:
        """
        Derives an exact human-readable description of the proposed cleaning value or strategy.
        """
        rule = issue.get("cleaning_rule")
        params = issue.get("cleaning_params", {})
        col = params.get("column") or issue.get("column")

        if not rule:
            return "Manual Inspection"

        if rule in ("impute_median", "impute_mean", "impute_mode", "fill_constant"):
            strat = "median" if "median" in rule else ("mean" if "mean" in rule else ("mode" if "mode" in rule else "constant"))
            if col and col in df.columns:
                full_series = df[col]
                if strat == "median":
                    non_null_num = pd.to_numeric(full_series, errors="coerce").dropna()
                    val = round(float(non_null_num.median()), 2) if not non_null_num.empty else 0.0
                    return f"Replace missing with Median: {val}"
                elif strat == "mean":
                    non_null_num = pd.to_numeric(full_series, errors="coerce").dropna()
                    val = round(float(non_null_num.mean()), 2) if not non_null_num.empty else 0.0
                    return f"Replace missing with Mean: {val}"
                elif strat == "mode":
                    modes = full_series.dropna().mode()
                    val = str(modes.iloc[0]) if not modes.empty else "Unknown"
                    return f'Replace missing with Mode: "{val}"'
                else:
                    val = params.get("fill_value")
                    if val is None:
                        val = 0 if pd.api.types.is_numeric_dtype(full_series) else "Unknown"
                    return f'Replace missing with Constant: "{val}"'
            return f"Impute missing with {strat}"

        elif rule == "trim_whitespace":
            return "Trim leading & trailing whitespace"

        elif rule == "standardize_casing":
            c = str(params.get("case", "title")).capitalize()
            return f"Standardize casing to {c} Case"

        elif rule == "cap_outliers":
            lb = params.get("lower_bound", 0)
            ub = params.get("upper_bound", 100)
            return f"Winsorize/Cap values to [{lb}, {ub}]"

        elif rule == "absolute_or_zero_floor":
            return "Convert negative values to positive (Absolute Value)"

        elif rule == "nullify_invalid_emails":
            return "Clear/Nullify malformed email addresses"

        elif rule == "standardize_dates":
            return "Standardize date strings to YYYY-MM-DD"

        elif rule == "drop_duplicate_rows":
            return "Drop duplicate records (keep 1st occurrence)"

        elif rule == "deduplicate_by_key":
            return f"Deduplicate by key '{col}' (keep 1st)"

        elif rule == "cap_percentage":
            return "Cap percentage values to [0%, 100%]"

        elif rule == "coerce_numeric":
            return "Coerce invalid numeric text into numbers"

        elif rule == "swap_chronological_order":
            c1 = params.get("col_start")
            c2 = params.get("col_end")
            return f"Swap inverted dates between '{c1}' and '{c2}'"

        return f"Apply rule '{rule}'"

    @classmethod
    def generate_preview(cls, df: pd.DataFrame, issue: Dict[str, Any], max_samples: int = 5) -> List[Dict[str, Any]]:
        """
        Generates before-and-after previews for affected rows without altering original data.
        """
        rule = issue.get("cleaning_rule")
        params = issue.get("cleaning_params", {})
        col = params.get("column") or issue.get("column")
        affected_rows = issue.get("affected_rows", [])

        if not rule or not affected_rows:
            return []

        # Find rows in df by _row_number
        if "_row_number" in df.columns:
            target_df = df[df["_row_number"].isin(affected_rows[:max_samples])].copy()
        else:
            target_df = df.iloc[:max_samples].copy()

        if target_df.empty:
            return []

        preview_data = []

        # Simulate transformation on small sample
        if rule in ("impute_median", "impute_mean", "impute_mode", "fill_constant"):
            strat = "median" if "median" in rule else ("mean" if "mean" in rule else ("mode" if "mode" in rule else "constant"))
            # Precompute replacement from full dataset df
            full_series = df[col] if col in df.columns else target_df[col]
            if strat == "median":
                non_null_num = pd.to_numeric(full_series, errors="coerce").dropna()
                rep_val = round(float(non_null_num.median()), 2) if not non_null_num.empty else 0.0
            elif strat == "mean":
                non_null_num = pd.to_numeric(full_series, errors="coerce").dropna()
                rep_val = round(float(non_null_num.mean()), 2) if not non_null_num.empty else 0.0
            elif strat == "mode":
                modes = full_series.dropna().mode()
                rep_val = modes.iloc[0] if not modes.empty else "Unknown"
            else:
                rep_val = params.get("fill_value")
                if rep_val is None:
                    rep_val = 0 if pd.api.types.is_numeric_dtype(full_series) else "Unknown"

            simulated_df, _ = CleaningOperations.impute_missing(
                target_df, col, strategy="constant", fill_value=rep_val
            )
            for idx, row in target_df.iterrows():
                r_num = row.get("_row_number", idx)
                val_before = row.get(col)
                before_str = "<MISSING / NULL>" if (pd.isna(val_before) or str(val_before).strip() == "" or str(val_before).lower() == "nan") else str(val_before)
                preview_data.append({
                    "row": int(r_num),
                    "column": col,
                    "before": before_str,
                    "after": str(simulated_df.loc[idx, col])
                })

        elif rule == "trim_whitespace":
            simulated_df, _ = CleaningOperations.trim_whitespace(target_df, col)
            for idx, row in target_df.iterrows():
                r_num = row.get("_row_number", idx)
                preview_data.append({
                    "row": int(r_num),
                    "column": col,
                    "before": f"'{row.get(col)}'",
                    "after": f"'{simulated_df.loc[idx, col]}'"
                })

        elif rule == "standardize_casing":
            simulated_df, _ = CleaningOperations.standardize_casing(target_df, col, target_case=params.get("case", "title"))
            for idx, row in target_df.iterrows():
                r_num = row.get("_row_number", idx)
                preview_data.append({
                    "row": int(r_num),
                    "column": col,
                    "before": str(row.get(col)),
                    "after": str(simulated_df.loc[idx, col])
                })

        elif rule in ("drop_duplicate_rows", "deduplicate_by_key"):
            for idx, row in target_df.iterrows():
                r_num = row.get("_row_number", idx)
                preview_data.append({
                    "row": int(r_num),
                    "column": col or "Full Record",
                    "before": "Duplicate Record",
                    "after": "Removed (Pruned from dataset)"
                })

        elif rule == "cap_outliers":
            low = params.get("lower_bound", 0)
            high = params.get("upper_bound", 100)
            simulated_df, _ = CleaningOperations.cap_outliers(target_df, col, low, high)
            for idx, row in target_df.iterrows():
                r_num = row.get("_row_number", idx)
                preview_data.append({
                    "row": int(r_num),
                    "column": col,
                    "before": str(row.get(col)),
                    "after": str(simulated_df.loc[idx, col])
                })

        elif rule == "absolute_or_zero_floor":
            simulated_df, _ = CleaningOperations.fix_negatives(target_df, col, strategy=params.get("strategy", "absolute_value"))
            for idx, row in target_df.iterrows():
                r_num = row.get("_row_number", idx)
                preview_data.append({
                    "row": int(r_num),
                    "column": col,
                    "before": str(row.get(col)),
                    "after": str(simulated_df.loc[idx, col])
                })

        elif rule == "nullify_invalid_emails":
            simulated_df, _ = CleaningOperations.nullify_invalid_emails(target_df, col)
            for idx, row in target_df.iterrows():
                r_num = row.get("_row_number", idx)
                preview_data.append({
                    "row": int(r_num),
                    "column": col,
                    "before": str(row.get(col)),
                    "after": "NULL / Empty"
                })

        elif rule == "standardize_dates":
            simulated_df, _ = CleaningOperations.standardize_dates(target_df, col)
            for idx, row in target_df.iterrows():
                r_num = row.get("_row_number", idx)
                preview_data.append({
                    "row": int(r_num),
                    "column": col,
                    "before": str(row.get(col)),
                    "after": str(simulated_df.loc[idx, col])
                })

        return preview_data

    @classmethod
    def apply_cleaning(
        cls,
        df: pd.DataFrame,
        approved_issue_ids: List[str],
        all_issues: List[Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Applies only the user-approved operations onto a fresh copy of the DataFrame.
        Returns:
            (cleaned_df, audit_log)
        """
        cleaned_df = df.copy()
        audit_log = []

        # Map issues by ID
        issues_dict = {iss["id"]: iss for iss in all_issues}

        for issue_id in approved_issue_ids:
            if issue_id not in issues_dict:
                continue

            issue = issues_dict[issue_id]
            rule = issue.get("cleaning_rule")
            params = issue.get("cleaning_params", {})
            col = params.get("column") or issue.get("column")

            try:
                if rule in ("impute_median", "impute_mean", "impute_mode", "fill_constant"):
                    strat = "median" if "median" in rule else ("mean" if "mean" in rule else ("mode" if "mode" in rule else "constant"))
                    cleaned_df, meta = CleaningOperations.impute_missing(
                        cleaned_df, col, strategy=strat, fill_value=params.get("fill_value")
                    )
                    audit_log.append(meta)

                elif rule == "drop_duplicate_rows":
                    cleaned_df, meta = CleaningOperations.drop_duplicates(cleaned_df, subset=None, keep=params.get("keep", "first"))
                    audit_log.append(meta)

                elif rule == "deduplicate_by_key":
                    cleaned_df, meta = CleaningOperations.drop_duplicates(cleaned_df, subset=[col], keep=params.get("keep", "first"))
                    audit_log.append(meta)

                elif rule == "trim_whitespace":
                    cleaned_df, meta = CleaningOperations.trim_whitespace(cleaned_df, col)
                    audit_log.append(meta)

                elif rule == "standardize_casing":
                    cleaned_df, meta = CleaningOperations.standardize_casing(cleaned_df, col, target_case=params.get("case", "title"))
                    audit_log.append(meta)

                elif rule == "cap_outliers":
                    cleaned_df, meta = CleaningOperations.cap_outliers(
                        cleaned_df, col, params.get("lower_bound", 0), params.get("upper_bound", 100)
                    )
                    audit_log.append(meta)

                elif rule == "absolute_or_zero_floor":
                    cleaned_df, meta = CleaningOperations.fix_negatives(cleaned_df, col, strategy=params.get("strategy", "absolute_value"))
                    audit_log.append(meta)

                elif rule == "nullify_invalid_emails":
                    cleaned_df, meta = CleaningOperations.nullify_invalid_emails(cleaned_df, col)
                    audit_log.append(meta)

                elif rule == "standardize_dates":
                    cleaned_df, meta = CleaningOperations.standardize_dates(cleaned_df, col)
                    audit_log.append(meta)

            except Exception as e:
                logger.exception(f"Error applying rule {rule} on column {col}")
                audit_log.append({
                    "operation": f"Error applying {rule}",
                    "column": col,
                    "error": str(e)
                })

        return cleaned_df, audit_log

    @classmethod
    def export_cleaned_dataset(cls, cleaned_df: pd.DataFrame, session_id: str, file_format: str = "csv") -> Path:
        """
        Saves cleaned DataFrame to outputs directory without the internal _row_number column.
        """
        export_df = cleaned_df.drop(columns=["_row_number"], errors="ignore")
        output_dir = Config.OUTPUT_FOLDER
        output_dir.mkdir(parents=True, exist_ok=True)

        if file_format == "xlsx":
            output_path = output_dir / f"cleaned_{session_id}.xlsx"
            export_df.to_excel(output_path, index=False, engine="openpyxl")
        else:
            output_path = output_dir / f"cleaned_{session_id}.csv"
            export_df.to_csv(output_path, index=False, encoding="utf-8")

        return output_path
