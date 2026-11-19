from typing import List, Dict, Any
import numpy as np
import pandas as pd
from scipy import stats

class OutlierDetector:
    """
    Detects statistical anomalies and extreme values in numeric measurement columns.
    IMPORTANT: As per requirements, statistical outliers are flagged as 'anomaly'
    and are NOT automatically penalized as confirmed quality errors (is_anomaly_only = True).
    """

    @classmethod
    def detect(cls, df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        total_rows = len(df)
        if total_rows < 5:
            return issues

        row_indices = df["_row_number"] if "_row_number" in df.columns else pd.Series(range(1, total_rows + 1))

        for col, col_profile in profile.get("columns", {}).items():
            if col not in df.columns or col == "_row_number":
                continue

            # Only check numeric columns that represent measurements, NOT identifiers or categorical codes
            if col_profile.get("semantic_type") not in ("numeric_measure", "ratio_or_probability", "percentage"):
                continue

            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(series) < 5 or series.nunique() < 2:
                continue

            # If binary flag (e.g. only 0 and 1), skip
            unique_vals = set(series.unique())
            if unique_vals.issubset({0, 1}) or unique_vals.issubset({-1, 1}):
                continue

            q25 = float(series.quantile(0.25))
            q75 = float(series.quantile(0.75))
            iqr = q75 - q25

            if iqr <= 0:
                # Fallback to Z-score if IQR is 0 (constant or near-constant)
                std = float(series.std())
                if std > 0:
                    mean = float(series.mean())
                    z_scores = np.abs((series - mean) / std)
                    outlier_mask = z_scores > 3.0
                    lower_bound = mean - 3 * std
                    upper_bound = mean + 3 * std
                else:
                    continue
            else:
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                outlier_mask = (series < lower_bound) | (series > upper_bound)

            outlier_count = int(outlier_mask.sum())
            if outlier_count > 0:
                outlier_indices = series[outlier_mask].index
                affected_row_numbers = row_indices.loc[outlier_indices].head(50).tolist()
                outlier_pct = round((outlier_count / total_rows) * 100, 2)

                # Get sample extreme values
                sample_outliers = series[outlier_mask].sort_values()
                samples = []
                if not sample_outliers.empty:
                    samples.append(f"Min anomaly: {sample_outliers.iloc[0]}")
                    if len(sample_outliers) > 1:
                        samples.append(f"Max anomaly: {sample_outliers.iloc[-1]}")

                # Determine severity: anomalies with extreme values
                extreme_count = int(((series < (q25 - 3 * iqr)) | (series > (q75 + 3 * iqr))).sum()) if iqr > 0 else 0
                severity = "medium" if extreme_count > 0 else "low"

                issues.append({
                    "id": f"outlier_{col}",
                    "category": "anomaly",
                    "check_type": "statistical_outlier",
                    "column": col,
                    "title": f"Statistical Outliers in '{col}'",
                    "description": f"Detected {outlier_count} potential outlier(s) ({outlier_pct}%) outside IQR bounds [{round(lower_bound, 2)}, {round(upper_bound, 2)}].",
                    "severity": severity,
                    "is_anomaly_only": True, # Kept separate from confirmed quality errors
                    "affected_count": outlier_count,
                    "affected_pct": outlier_pct,
                    "affected_rows": affected_row_numbers,
                    "problematic_samples": samples,
                    "cleaning_rule": "cap_outliers",
                    "cleaning_params": {
                        "column": col,
                        "lower_bound": round(lower_bound, 4),
                        "upper_bound": round(upper_bound, 4)
                    }
                })

        return issues
