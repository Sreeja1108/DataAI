from typing import List, Dict, Any
import pandas as pd

class IntegrityDetector:
    """
    Detects cross-column relational anomalies and temporal order inversions.
    Quality Dimension: Consistency / Validity
    """

    DATE_PAIR_PATTERNS = [
        ("start", "end"),
        ("order", "ship"),
        ("order", "deliver"),
        ("hire", "term"),
        ("hire", "fire"),
        ("birth", "hire"),
        ("open", "close"),
        ("created", "updated"),
        ("checkin", "checkout"),
        ("arrival", "departure")
    ]

    @classmethod
    def detect(cls, df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        total_rows = len(df)
        if total_rows == 0:
            return issues

        row_indices = df["_row_number"] if "_row_number" in df.columns else pd.Series(range(1, total_rows + 1))
        cols = list(df.columns)
        date_cols = [
            c for c, p in profile.get("columns", {}).items()
            if p.get("semantic_type") == "date_timestamp" and c in df.columns
        ]

        # 1. Temporal Relational Inversions (e.g., start_date > end_date)
        for c1 in date_cols:
            for c2 in date_cols:
                if c1 == c2:
                    continue

                c1_lower = c1.lower()
                c2_lower = c2.lower()

                matches_pattern = any(
                    (p1 in c1_lower and p2 in c2_lower) for p1, p2 in cls.DATE_PAIR_PATTERNS
                )

                if matches_pattern:
                    try:
                        d1 = pd.to_datetime(df[c1], errors="coerce")
                        d2 = pd.to_datetime(df[c2], errors="coerce")

                        valid_both = d1.notna() & d2.notna()
                        inverted_mask = valid_both & (d1 > d2)
                        inverted_count = int(inverted_mask.sum())

                        if inverted_count > 0:
                            affected_indices = df[inverted_mask].index
                            affected_row_numbers = row_indices.loc[affected_indices].head(50).tolist()
                            pct = round((inverted_count / total_rows) * 100, 2)

                            sample_pairs = []
                            for idx in affected_indices[:3]:
                                sample_pairs.append(f"{c1}: {df.loc[idx, c1]} > {c2}: {df.loc[idx, c2]}")

                            issues.append({
                                "id": f"temporal_inversion_{c1}_{c2}",
                                "category": "consistency",
                                "check_type": "temporal_order_violation",
                                "column": f"{c1} & {c2}",
                                "title": f"Chronological Order Inversion ({c1} > {c2})",
                                "description": f"Found {inverted_count} record(s) where start/prior timestamp '{c1}' is chronologically after end/later timestamp '{c2}'.",
                                "severity": "high",
                                "is_anomaly_only": False,
                                "affected_count": inverted_count,
                                "affected_pct": pct,
                                "affected_rows": affected_row_numbers,
                                "problematic_samples": sample_pairs,
                                "cleaning_rule": "swap_chronological_order",
                                "cleaning_params": {"col_start": c1, "col_end": c2}
                            })
                    except Exception:
                        pass

        return issues
