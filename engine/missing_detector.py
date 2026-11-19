from typing import List, Dict, Any
import pandas as pd

class MissingValueDetector:
    """
    Detects missing values (null, NaN, None) and whitespace-only/empty strings.
    Quality Dimension: Completeness
    """

    @classmethod
    def detect(cls, df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        total_rows = len(df)
        if total_rows == 0:
            return issues

        row_indices = df["_row_number"] if "_row_number" in df.columns else pd.Series(range(1, total_rows + 1))

        for col, col_profile in profile.get("columns", {}).items():
            if col not in df.columns or col == "_row_number":
                continue

            series = df[col]
            # Null/NaN mask
            null_mask = series.isna()

            # Empty string mask for text columns
            empty_str_mask = pd.Series(False, index=df.index)
            if series.dtype == "object" or pd.api.types.is_string_dtype(series):
                empty_str_mask = (~null_mask) & (series.astype(str).str.strip() == "")

            combined_missing = null_mask | empty_str_mask
            missing_count = int(combined_missing.sum())

            if missing_count > 0:
                affected_row_numbers = row_indices[combined_missing].head(100).tolist()
                missing_pct = round((missing_count / total_rows) * 100, 2)

                # Determine severity based on percentage and whether column is an identifier
                is_id = col_profile.get("semantic_type") == "identifier"
                if is_id or missing_pct > 30:
                    severity = "high"
                elif missing_pct > 5:
                    severity = "medium"
                else:
                    severity = "low"

                # Suggest cleaning rule based on column type
                if col_profile.get("physical_type") in ("integer", "float"):
                    suggested_action = "impute_median" if col_profile.get("semantic_type") == "numeric_measure" else "fill_constant"
                elif col_profile.get("physical_type") == "categorical":
                    suggested_action = "impute_mode"
                elif is_id:
                    suggested_action = "drop_rows"
                else:
                    suggested_action = "fill_constant"

                issues.append({
                    "id": f"miss_{col}",
                    "category": "completeness",
                    "check_type": "missing_values",
                    "column": col,
                    "title": f"Missing Values in '{col}'",
                    "description": f"Found {missing_count} missing value(s) ({missing_pct}%) including nulls and blank strings.",
                    "severity": severity,
                    "is_anomaly_only": False,
                    "affected_count": missing_count,
                    "affected_pct": missing_pct,
                    "affected_rows": affected_row_numbers,
                    "problematic_samples": ["<NULL/BLANK>"],
                    "cleaning_rule": suggested_action,
                    "cleaning_params": {
                        "column": col,
                        "fill_value": "Unknown" if suggested_action == "fill_constant" else None
                    }
                })

        return issues
