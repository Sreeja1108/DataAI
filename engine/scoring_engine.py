from typing import List, Dict, Any, Set
import pandas as pd

class ScoringEngine:
    """
    Calculates overall and column-level quality scores based on the formula:
        Overall Quality Score = 25% Completeness + 20% Uniqueness + 30% Validity + 25% Consistency

    Rules:
    - Each dimension calculated strictly from applicable checks.
    - Non-applicable checks are not penalized.
    - Avoids double-counting affected records within any quality dimension.
    - Keeps anomaly observations separate from confirmed errors.
    """

    DIMENSION_WEIGHTS = {
        "completeness": 0.25,
        "uniqueness": 0.20,
        "validity": 0.30,
        "consistency": 0.25
    }

    COLUMN_DIMENSION_WEIGHTS = {
        "completeness": 0.35,
        "uniqueness": 0.25,
        "validity": 0.25,
        "consistency": 0.15
    }

    @classmethod
    def calculate_scores(
        cls,
        df: pd.DataFrame,
        profile: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        total_rows = len(df)
        if total_rows == 0:
            return {
                "overall_score": 100.0,
                "dimensions": {
                    "completeness": 100.0,
                    "uniqueness": 100.0,
                    "validity": 100.0,
                    "consistency": 100.0
                },
                "column_scores": {},
                "formula": "25% Completeness + 20% Uniqueness + 30% Validity + 25% Consistency",
                "total_confirmed_issues": 0,
                "total_anomalies": 0
            }

        # Separate confirmed quality errors from potential anomalies
        confirmed_issues = [iss for iss in issues if not iss.get("is_anomaly_only", False)]
        anomaly_issues = [iss for iss in issues if iss.get("is_anomaly_only", False)]

        # Collect unique affected row numbers per dimension to prevent double-counting
        dimension_affected_rows: Dict[str, Set[int]] = {
            "completeness": set(),
            "uniqueness": set(),
            "validity": set(),
            "consistency": set()
        }

        # Track applicable dimensions
        applicable_dimensions = {"completeness": True, "uniqueness": True, "validity": True, "consistency": True}

        # For completeness: Use total missing cells ratio across all cells as precise metric
        overview = profile.get("overview", {})
        total_cells = overview.get("total_cells", total_rows * max(1, len(profile.get("columns", {}))))
        total_missing_cells = overview.get("total_missing_cells", 0)
        completeness_ratio = max(0.0, 1.0 - (total_missing_cells / total_cells)) if total_cells > 0 else 1.0
        completeness_score = round(completeness_ratio * 100, 2)

        # For uniqueness: Deduplicate affected rows across all uniqueness issues
        for iss in confirmed_issues:
            cat = iss.get("category")
            if cat in dimension_affected_rows:
                # Add row indices from affected rows
                for r in iss.get("affected_rows", []):
                    dimension_affected_rows[cat].add(r)

        # Calculate uniqueness score
        uniqueness_affected_pct = min(100.0, (len(dimension_affected_rows["uniqueness"]) / total_rows) * 100)
        uniqueness_score = round(max(0.0, 100.0 - uniqueness_affected_pct), 2)

        # Calculate validity score (deduplicated affected rows in validity)
        validity_affected_pct = min(100.0, (len(dimension_affected_rows["validity"]) / total_rows) * 100)
        validity_score = round(max(0.0, 100.0 - validity_affected_pct), 2)

        # Calculate consistency score (deduplicated affected rows in consistency)
        consistency_affected_pct = min(100.0, (len(dimension_affected_rows["consistency"]) / total_rows) * 100)
        consistency_score = round(max(0.0, 100.0 - consistency_affected_pct), 2)

        # Calculate overall weighted score
        dimensions = {
            "completeness": completeness_score,
            "uniqueness": uniqueness_score,
            "validity": validity_score,
            "consistency": consistency_score
        }

        overall_score = (
            cls.DIMENSION_WEIGHTS["completeness"] * completeness_score +
            cls.DIMENSION_WEIGHTS["uniqueness"] * uniqueness_score +
            cls.DIMENSION_WEIGHTS["validity"] * validity_score +
            cls.DIMENSION_WEIGHTS["consistency"] * consistency_score
        )
        overall_score = round(min(100.0, max(0.0, overall_score)), 2)

        # Calculate Column-Level Quality Scores
        column_scores = {}
        for col, col_prof in profile.get("columns", {}).items():
            if col == "_row_number":
                continue

            # Column Completeness
            col_missing_pct = col_prof.get("missing_pct", 0.0)
            col_comp_score = max(0.0, 100.0 - col_missing_pct)

            # Column Uniqueness
            # Only penalize if duplicate identifiers exist for this column
            col_dup_issues = [
                iss for iss in confirmed_issues
                if iss.get("category") == "uniqueness" and iss.get("column") == col
            ]
            col_uniq_dedup_rows = set()
            for iss in col_dup_issues:
                col_uniq_dedup_rows.update(iss.get("affected_rows", []))
            col_uniq_score = max(0.0, 100.0 - (len(col_uniq_dedup_rows) / total_rows * 100))

            # Column Validity
            col_val_issues = [
                iss for iss in confirmed_issues
                if iss.get("category") == "validity" and iss.get("column") == col
            ]
            col_val_dedup_rows = set()
            for iss in col_val_issues:
                col_val_dedup_rows.update(iss.get("affected_rows", []))
            col_val_score = max(0.0, 100.0 - (len(col_val_dedup_rows) / total_rows * 100))

            # Column Consistency
            col_cons_issues = [
                iss for iss in confirmed_issues
                if iss.get("category") == "consistency" and (iss.get("column") == col or col in str(iss.get("column")))
            ]
            col_cons_dedup_rows = set()
            for iss in col_cons_issues:
                col_cons_dedup_rows.update(iss.get("affected_rows", []))
            col_cons_score = max(0.0, 100.0 - (len(col_cons_dedup_rows) / total_rows * 100))

            col_total_score = (
                cls.COLUMN_DIMENSION_WEIGHTS["completeness"] * col_comp_score +
                cls.COLUMN_DIMENSION_WEIGHTS["uniqueness"] * col_uniq_score +
                cls.COLUMN_DIMENSION_WEIGHTS["validity"] * col_val_score +
                cls.COLUMN_DIMENSION_WEIGHTS["consistency"] * col_cons_score
            )
            col_total_score = round(min(100.0, max(0.0, col_total_score)), 2)

            # Assign qualitative health rating
            if col_total_score >= 90:
                health = "Excellent"
                badge_class = "success"
            elif col_total_score >= 75:
                health = "Good"
                badge_class = "primary"
            elif col_total_score >= 50:
                health = "Fair"
                badge_class = "warning"
            else:
                health = "Poor"
                badge_class = "danger"

            column_scores[col] = {
                "score": col_total_score,
                "completeness": round(col_comp_score, 1),
                "uniqueness": round(col_uniq_score, 1),
                "validity": round(col_val_score, 1),
                "consistency": round(col_cons_score, 1),
                "health": health,
                "badge_class": badge_class,
                "issues_count": len(col_dup_issues) + len(col_val_issues) + len(col_cons_issues) + (1 if col_missing_pct > 0 else 0)
            }

        # Overall health rating
        if overall_score >= 90:
            overall_health = "Excellent"
            health_color = "#198754"
        elif overall_score >= 75:
            overall_health = "Good"
            health_color = "#0d6efd"
        elif overall_score >= 50:
            overall_health = "Fair"
            health_color = "#ffc107"
        else:
            overall_health = "Needs Attention"
            health_color = "#dc3545"

        return {
            "overall_score": overall_score,
            "health": overall_health,
            "health_color": health_color,
            "dimensions": dimensions,
            "column_scores": column_scores,
            "formula": "Overall Quality = 25% Completeness + 20% Uniqueness + 30% Validity + 25% Consistency",
            "weights": cls.DIMENSION_WEIGHTS,
            "total_confirmed_issues": len(confirmed_issues),
            "total_anomalies": len(anomaly_issues)
        }
