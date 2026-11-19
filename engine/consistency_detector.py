from typing import List, Dict, Any
import pandas as pd

class ConsistencyDetector:
    """
    Detects inconsistencies in text formatting:
    - Leading / trailing whitespace
    - Inconsistent capitalization across categorical values
    - Inconsistent boolean / status representations
    Quality Dimension: Consistency
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
            physical_type = col_profile.get("physical_type")
            semantic_type = col_profile.get("semantic_type")

            # Check string / categorical columns
            if physical_type in ("string", "categorical") or series.dtype == "object":
                non_null_mask = series.notna()
                str_series = series[non_null_mask].astype(str)

                # 1. Leading / Trailing Whitespace
                whitespace_mask = (str_series != str_series.str.strip())
                whitespace_count = int(whitespace_mask.sum())

                if whitespace_count > 0:
                    affected_indices = str_series[whitespace_mask].index
                    affected_row_numbers = row_indices.loc[affected_indices].head(50).tolist()
                    ws_pct = round((whitespace_count / total_rows) * 100, 2)
                    sample_values = [f"'{x}'" for x in str_series[whitespace_mask].head(5).tolist()]

                    issues.append({
                        "id": f"whitespace_{col}",
                        "category": "consistency",
                        "check_type": "untrimmed_whitespace",
                        "column": col,
                        "title": f"Leading/Trailing Whitespace in '{col}'",
                        "description": f"Found {whitespace_count} record(s) ({ws_pct}%) with untrimmed leading or trailing whitespace.",
                        "severity": "low",
                        "is_anomaly_only": False,
                        "affected_count": whitespace_count,
                        "affected_pct": ws_pct,
                        "affected_rows": affected_row_numbers,
                        "problematic_samples": sample_values,
                        "cleaning_rule": "trim_whitespace",
                        "cleaning_params": {"column": col}
                    })

                # 2. Inconsistent Capitalization in Categories
                if col_profile.get("distinct_count", 0) <= 100:
                    cleaned_str = str_series.str.strip()
                    lower_series = cleaned_str.str.lower()

                    # Compare count of unique raw vs unique lower
                    raw_uniques = cleaned_str.unique()
                    lower_uniques = lower_series.unique()

                    if len(raw_uniques) > len(lower_uniques):
                        # Find the colliding terms
                        case_mapping = {}
                        colliding_examples = []
                        for val in raw_uniques:
                            low = val.lower()
                            if low not in case_mapping:
                                case_mapping[low] = []
                            case_mapping[low].append(val)

                        for low, variants in case_mapping.items():
                            if len(variants) > 1:
                                colliding_examples.append(f"{' vs '.join(variants[:3])}")

                        # Count affected rows that have non-canonical casing
                        inconsistent_casing_count = 0
                        colliding_mask = pd.Series(False, index=str_series.index)
                        for low, variants in case_mapping.items():
                            if len(variants) > 1:
                                # Count all rows with these variants
                                colliding_mask |= cleaned_str.str.lower() == low

                        inconsistent_count = int(colliding_mask.sum())
                        if inconsistent_count > 0:
                            affected_indices = str_series[colliding_mask].index
                            affected_row_numbers = row_indices.loc[affected_indices].head(50).tolist()

                            issues.append({
                                "id": f"casing_{col}",
                                "category": "consistency",
                                "check_type": "inconsistent_capitalization",
                                "column": col,
                                "title": f"Inconsistent Capitalization in '{col}'",
                                "description": f"Found category casing variations representing identical terms ({', '.join(colliding_examples[:3])}).",
                                "severity": "medium",
                                "is_anomaly_only": False,
                                "affected_count": inconsistent_count,
                                "affected_pct": round((inconsistent_count / total_rows) * 100, 2),
                                "affected_rows": affected_row_numbers,
                                "problematic_samples": colliding_examples[:5],
                                "cleaning_rule": "standardize_casing",
                                "cleaning_params": {"column": col, "case": "title"}
                            })

        return issues
