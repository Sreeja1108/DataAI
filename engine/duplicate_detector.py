from typing import List, Dict, Any
import pandas as pd

class DuplicateDetector:
    """
    Detects full duplicate records and duplicate key identifiers.
    Quality Dimension: Uniqueness
    """

    @classmethod
    def detect(cls, df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        total_rows = len(df)
        if total_rows == 0:
            return issues

        row_indices = df["_row_number"] if "_row_number" in df.columns else pd.Series(range(1, total_rows + 1))
        data_cols = [c for c in df.columns if c != "_row_number"]

        # 1. Full duplicate records
        dup_mask = df.duplicated(subset=data_cols, keep="first")
        dup_count = int(dup_mask.sum())

        if dup_count > 0:
            affected_row_numbers = row_indices[dup_mask].head(100).tolist()
            dup_pct = round((dup_count / total_rows) * 100, 2)

            issues.append({
                "id": "dup_full_rows",
                "category": "uniqueness",
                "check_type": "duplicate_rows",
                "column": None,
                "title": "Exact Duplicate Rows Found",
                "description": f"Found {dup_count} duplicate row(s) ({dup_pct}%) that have identical values across all columns.",
                "severity": "high" if dup_pct > 5 else "medium",
                "is_anomaly_only": False,
                "affected_count": dup_count,
                "affected_pct": dup_pct,
                "affected_rows": affected_row_numbers,
                "problematic_samples": ["Duplicate full records"],
                "cleaning_rule": "drop_duplicate_rows",
                "cleaning_params": {"subset": None, "keep": "first"}
            })

        # 2. Duplicate Key Identifiers (where uniqueness is expected)
        for col, col_profile in profile.get("columns", {}).items():
            if col not in df.columns or col == "_row_number":
                continue

            # Only check if semantic type is identifier or name strongly indicates ID
            is_identifier = col_profile.get("semantic_type") == "identifier"
            uniqueness_pct = col_profile.get("uniqueness_pct", 0)

            # If it's expected to be an identifier and has duplicates
            if is_identifier and uniqueness_pct < 100 and col_profile.get("distinct_count", 0) > 0:
                id_dup_mask = df[col].duplicated(keep="first") & df[col].notna()
                id_dup_count = int(id_dup_mask.sum())

                if id_dup_count > 0:
                    affected_row_numbers = row_indices[id_dup_mask].head(100).tolist()
                    id_dup_pct = round((id_dup_count / total_rows) * 100, 2)

                    # Get sample duplicate values
                    dup_values = df[col][id_dup_mask].astype(str).unique()[:5].tolist()

                    issues.append({
                        "id": f"dup_id_{col}",
                        "category": "uniqueness",
                        "check_type": "duplicate_identifier",
                        "column": col,
                        "title": f"Duplicate Identifier in '{col}'",
                        "description": f"Column '{col}' was identified as a primary key/identifier, but contains {id_dup_count} duplicate values.",
                        "severity": "high",
                        "is_anomaly_only": False,
                        "affected_count": id_dup_count,
                        "affected_pct": id_dup_pct,
                        "affected_rows": affected_row_numbers,
                        "problematic_samples": dup_values,
                        "cleaning_rule": "deduplicate_by_key",
                        "cleaning_params": {"column": col, "keep": "first"}
                    })

        return issues
