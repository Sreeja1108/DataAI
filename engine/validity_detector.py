import re
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from engine.type_inference import EMAIL_REGEX

class ValidityDetector:
    """
    Detects invalid formats, impossible values, out-of-range metrics,
    and category discrepancies.
    Quality Dimension: Validity
    """

    NON_NEGATIVE_TERMS = ("age", "price", "cost", "salary", "amount", "quantity", "count", "fee", "revenue", "rate", "distance", "weight", "height")

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
            semantic_type = col_profile.get("semantic_type")
            physical_type = col_profile.get("physical_type")
            col_lower = col.lower()

            # 1. Invalid Email Detection
            if semantic_type == "email":
                non_null_mask = series.notna() & (series.astype(str).str.strip() != "")
                non_null_series = series[non_null_mask].astype(str).str.strip()

                invalid_mask = ~non_null_series.str.match(EMAIL_REGEX.pattern)
                invalid_count = int(invalid_mask.sum())

                if invalid_count > 0:
                    affected_indices = non_null_series[invalid_mask].index
                    affected_row_numbers = row_indices.loc[affected_indices].head(50).tolist()
                    invalid_pct = round((invalid_count / total_rows) * 100, 2)
                    sample_invalids = non_null_series[invalid_mask].head(5).tolist()

                    issues.append({
                        "id": f"invalid_email_{col}",
                        "category": "validity",
                        "check_type": "invalid_email_format",
                        "column": col,
                        "title": f"Invalid Email Format in '{col}'",
                        "description": f"Found {invalid_count} email value(s) ({invalid_pct}%) that do not follow standard email syntax.",
                        "severity": "medium",
                        "is_anomaly_only": False,
                        "affected_count": invalid_count,
                        "affected_pct": invalid_pct,
                        "affected_rows": affected_row_numbers,
                        "problematic_samples": sample_invalids,
                        "cleaning_rule": "nullify_invalid_emails",
                        "cleaning_params": {"column": col}
                    })

            # 2. Date Format & Unparseable Dates
            if semantic_type == "date_timestamp" and physical_type != "datetime":
                non_null_mask = series.notna() & (series.astype(str).str.strip() != "")
                non_null_series = series[non_null_mask].astype(str).str.strip()

                parsed = pd.to_datetime(non_null_series, errors="coerce", format="mixed")
                invalid_date_mask = parsed.isna()
                invalid_date_count = int(invalid_date_mask.sum())

                if invalid_date_count > 0:
                    affected_indices = non_null_series[invalid_date_mask].index
                    affected_row_numbers = row_indices.loc[affected_indices].head(50).tolist()
                    invalid_pct = round((invalid_date_count / total_rows) * 100, 2)
                    sample_invalids = non_null_series[invalid_date_mask].head(5).tolist()

                    issues.append({
                        "id": f"invalid_date_{col}",
                        "category": "validity",
                        "check_type": "invalid_date_format",
                        "column": col,
                        "title": f"Unparseable Dates in '{col}'",
                        "description": f"Found {invalid_date_count} date string(s) ({invalid_pct}%) that cannot be converted to valid timestamps.",
                        "severity": "medium",
                        "is_anomaly_only": False,
                        "affected_count": invalid_date_count,
                        "affected_pct": invalid_pct,
                        "affected_rows": affected_row_numbers,
                        "problematic_samples": sample_invalids,
                        "cleaning_rule": "standardize_dates",
                        "cleaning_params": {"column": col}
                    })

            # 3. Impossible or Negative Values in Non-Negative Measures
            if pd.api.types.is_numeric_dtype(series) or physical_type in ("integer", "float"):
                num_series = pd.to_numeric(series, errors="coerce")
                is_non_negative_expected = any(term in col_lower for term in cls.NON_NEGATIVE_TERMS)

                if is_non_negative_expected:
                    negative_mask = (num_series < 0)
                    neg_count = int(negative_mask.sum())

                    if neg_count > 0:
                        affected_indices = num_series[negative_mask].index
                        affected_row_numbers = row_indices.loc[affected_indices].head(50).tolist()
                        neg_pct = round((neg_count / total_rows) * 100, 2)
                        sample_negs = [str(x) for x in num_series[negative_mask].head(5).tolist()]

                        issues.append({
                            "id": f"invalid_negative_{col}",
                            "category": "validity",
                            "check_type": "invalid_range",
                            "column": col,
                            "title": f"Negative Values in Non-Negative Column '{col}'",
                            "description": f"Found {neg_count} negative value(s) ({neg_pct}%) in '{col}', where values are expected to be >= 0.",
                            "severity": "high",
                            "is_anomaly_only": False,
                            "affected_count": neg_count,
                            "affected_pct": neg_pct,
                            "affected_rows": affected_row_numbers,
                            "problematic_samples": sample_negs,
                            "cleaning_rule": "absolute_or_zero_floor",
                            "cleaning_params": {"column": col, "strategy": "absolute_value"}
                        })

                # Percentage out of bounds (> 100 or < 0)
                if "pct" in col_lower or "percentage" in col_lower or semantic_type == "percentage":
                    pct_invalid_mask = (num_series < 0) | (num_series > 100)
                    pct_invalid_count = int(pct_invalid_mask.sum())
                    if pct_invalid_count > 0:
                        affected_indices = num_series[pct_invalid_mask].index
                        affected_row_numbers = row_indices.loc[affected_indices].head(50).tolist()
                        issues.append({
                            "id": f"invalid_pct_{col}",
                            "category": "validity",
                            "check_type": "out_of_range_percentage",
                            "column": col,
                            "title": f"Out-of-Range Percentage in '{col}'",
                            "description": f"Found {pct_invalid_count} values outside the valid 0-100% range.",
                            "severity": "medium",
                            "is_anomaly_only": False,
                            "affected_count": pct_invalid_count,
                            "affected_pct": round((pct_invalid_count / total_rows) * 100, 2),
                            "affected_rows": affected_row_numbers,
                            "problematic_samples": [str(x) for x in num_series[pct_invalid_mask].head(5).tolist()],
                            "cleaning_rule": "cap_percentage",
                            "cleaning_params": {"column": col, "min": 0, "max": 100}
                        })

            # 4. Mixed Types in Object Columns (Numbers mixed with text error codes)
            if col_profile.get("is_mixed") and physical_type in ("string_numeric", "string", "object"):
                non_null_series = series.dropna().astype(str).str.strip()
                numeric_count = 0
                text_error_count = 0
                error_samples = []

                for v in non_null_series:
                    try:
                        float(v.replace(",", ""))
                        numeric_count += 1
                    except ValueError:
                        text_error_count += 1
                        if len(error_samples) < 5 and v not in error_samples:
                            error_samples.append(v)

                total_non_null = len(non_null_series)
                if total_non_null > 0 and 0.05 < (text_error_count / total_non_null) < 0.95:
                    affected_row_numbers = row_indices[series.astype(str).isin(error_samples)].head(50).tolist()
                    issues.append({
                        "id": f"mixed_type_{col}",
                        "category": "validity",
                        "check_type": "mixed_data_types",
                        "column": col,
                        "title": f"Mixed Data Types in '{col}'",
                        "description": f"Column contains mixed numeric values and text strings ({text_error_count} non-numeric instances).",
                        "severity": "medium",
                        "is_anomaly_only": False,
                        "affected_count": text_error_count,
                        "affected_pct": round((text_error_count / total_rows) * 100, 2),
                        "affected_rows": affected_row_numbers,
                        "problematic_samples": error_samples,
                        "cleaning_rule": "coerce_numeric",
                        "cleaning_params": {"column": col}
                    })

        return issues
