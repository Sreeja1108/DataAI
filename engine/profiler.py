import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from engine.type_inference import TypeInferrer

logger = logging.getLogger(__name__)

class DataProfiler:
    """
    Performs comprehensive, domain-independent profiling of any structured dataset.
    Extracts statistical distributions, type inferences, nullness, uniqueness, and duplicate counts.
    Ensures all results are JSON-serializable.
    """

    @classmethod
    def profile(cls, df: pd.DataFrame, sample_size_for_stats: int = 100_000) -> Dict[str, Any]:
        """
        Profiles the dataset and returns a detailed structured summary.
        """
        clean_df = df.drop(columns=["_row_number"], errors="ignore")
        row_count = len(clean_df)
        col_count = len(clean_df.columns)

        # Check duplicate rows across all original columns
        duplicate_rows_count = int(clean_df.duplicated().sum())
        duplicate_rows_pct = round((duplicate_rows_count / row_count * 100) if row_count > 0 else 0, 2)

        columns_profile: Dict[str, Any] = {}
        total_cells = row_count * col_count if row_count > 0 and col_count > 0 else 1
        total_missing_cells = 0

        for col in clean_df.columns:
            series = clean_df[col]
            type_info = TypeInferrer.infer_column_type(series, col)

            # Null counts: None, NaN, and whitespace-only strings
            null_count = int(series.isna().sum())
            empty_string_count = 0
            if series.dtype == "object" or pd.api.types.is_string_dtype(series):
                # Count non-null strings that are empty or only whitespace
                empty_string_count = int(((~series.isna()) & (series.astype(str).str.strip() == "")).sum())

            total_col_missing = null_count + empty_string_count
            total_missing_cells += total_col_missing
            missing_pct = round((total_col_missing / row_count * 100) if row_count > 0 else 0, 2)

            # Distinct and unique values
            non_null_series = series.dropna()
            distinct_count = int(non_null_series.nunique())
            uniqueness_pct = round((distinct_count / row_count * 100) if row_count > 0 else 0, 2)

            col_summary: Dict[str, Any] = {
                "name": col,
                "physical_type": type_info["physical_type"],
                "semantic_type": type_info["semantic_type"],
                "is_mixed": type_info.get("is_mixed", False),
                "confidence": type_info.get("confidence", 0.9),
                "detected_formats": type_info.get("detected_formats", []),
                "total_count": row_count,
                "null_count": null_count,
                "empty_string_count": empty_string_count,
                "total_missing": total_col_missing,
                "missing_pct": missing_pct,
                "distinct_count": distinct_count,
                "uniqueness_pct": uniqueness_pct,
                "is_unique": (distinct_count == row_count and total_col_missing == 0),
                "statistics": {},
                "top_categories": [],
                "sample_values": [str(x) for x in non_null_series.head(5).tolist()]
            }

            # Numeric statistics
            if pd.api.types.is_numeric_dtype(series):
                numeric_series = pd.to_numeric(series, errors="coerce").dropna()
                if not numeric_series.empty:
                    mean_val = float(numeric_series.mean())
                    std_val = float(numeric_series.std()) if len(numeric_series) > 1 else 0.0
                    median_val = float(numeric_series.median())
                    min_val = float(numeric_series.min())
                    max_val = float(numeric_series.max())
                    q25 = float(numeric_series.quantile(0.25))
                    q75 = float(numeric_series.quantile(0.75))
                    iqr = q75 - q25

                    col_summary["statistics"] = {
                        "min": min_val,
                        "max": max_val,
                        "mean": round(mean_val, 4),
                        "median": round(median_val, 4),
                        "std": round(std_val, 4),
                        "q25": round(q25, 4),
                        "q75": round(q75, 4),
                        "iqr": round(iqr, 4),
                        "zeros_count": int((numeric_series == 0).sum()),
                        "negatives_count": int((numeric_series < 0).sum()),
                    }

                    # Create histogram bins for visual charts (10 bins)
                    try:
                        counts, bin_edges = np.histogram(numeric_series, bins=min(10, max(3, distinct_count)))
                        col_summary["distribution_chart"] = {
                            "type": "histogram",
                            "labels": [f"{round(bin_edges[i], 1)}-{round(bin_edges[i+1], 1)}" for i in range(len(counts))],
                            "values": [int(c) for c in counts]
                        }
                    except Exception:
                        pass

            # Categorical frequency
            if type_info["physical_type"] in ("categorical", "string", "boolean") or distinct_count <= 50:
                val_counts = non_null_series.astype(str).str.strip().value_counts().head(10)
                col_summary["top_categories"] = [
                    {"value": str(k), "count": int(v), "percentage": round(v / row_count * 100, 2)}
                    for k, v in val_counts.items()
                ]
                if "distribution_chart" not in col_summary and len(val_counts) > 0:
                    col_summary["distribution_chart"] = {
                        "type": "bar",
                        "labels": [str(k)[:15] for k in val_counts.keys()],
                        "values": [int(v) for v in val_counts.values]
                    }

            columns_profile[col] = col_summary

        total_missing_pct = round((total_missing_cells / total_cells * 100), 2)

        return {
            "overview": {
                "row_count": row_count,
                "column_count": col_count,
                "total_cells": total_cells,
                "total_missing_cells": total_missing_cells,
                "missing_cells_pct": total_missing_pct,
                "duplicate_rows_count": duplicate_rows_count,
                "duplicate_rows_pct": duplicate_rows_pct,
            },
            "columns": columns_profile
        }

    @classmethod
    def get_compact_summary_for_llm(cls, profile_dict: Dict[str, Any], max_columns: int = 50) -> Dict[str, Any]:
        """
        Creates a lightweight, privacy-conscious summary of the profile
        suitable for feeding to Gemini without sending sensitive raw data.
        """
        overview = profile_dict.get("overview", {})
        compact_cols = {}

        for col_name, col_data in list(profile_dict.get("columns", {}).items())[:max_columns]:
            c_info = {
                "physical_type": col_data.get("physical_type"),
                "semantic_type": col_data.get("semantic_type"),
                "missing_pct": col_data.get("missing_pct"),
                "distinct_count": col_data.get("distinct_count"),
                "is_unique": col_data.get("is_unique"),
            }
            if col_data.get("statistics"):
                s = col_data["statistics"]
                c_info["stats"] = {
                    "min": s.get("min"),
                    "max": s.get("max"),
                    "mean": s.get("mean"),
                    "median": s.get("median"),
                    "negatives": s.get("negatives_count", 0) > 0
                }
            if col_data.get("top_categories"):
                # Pass category labels without user identifiers
                c_info["sample_categories"] = [cat["value"] for cat in col_data["top_categories"][:5]]

            compact_cols[col_name] = c_info

        return {
            "total_rows": overview.get("row_count"),
            "total_columns": overview.get("column_count"),
            "duplicate_rows": overview.get("duplicate_rows_count"),
            "columns": compact_cols
        }
