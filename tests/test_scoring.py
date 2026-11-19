import pytest
import pandas as pd
from engine.profiler import DataProfiler
from engine.scoring_engine import ScoringEngine

def test_perfect_score_dataset():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "price": [10.0, 20.0, 30.0, 40.0, 50.0],
        "_row_number": [1, 2, 3, 4, 5]
    })
    prof = DataProfiler.profile(df)
    scores = ScoringEngine.calculate_scores(df, prof, issues=[])
    assert scores["overall_score"] == 100.0
    assert scores["dimensions"]["completeness"] == 100.0
    assert scores["dimensions"]["uniqueness"] == 100.0
    assert scores["dimensions"]["validity"] == 100.0
    assert scores["dimensions"]["consistency"] == 100.0

def test_formula_weights():
    # Verify exact weights match 0.25, 0.20, 0.30, 0.25
    assert ScoringEngine.DIMENSION_WEIGHTS["completeness"] == 0.25
    assert ScoringEngine.DIMENSION_WEIGHTS["uniqueness"] == 0.20
    assert ScoringEngine.DIMENSION_WEIGHTS["validity"] == 0.30
    assert ScoringEngine.DIMENSION_WEIGHTS["consistency"] == 0.25

def test_anomaly_not_penalized_in_score():
    df = pd.DataFrame({
        "value": [10, 10, 10, 10, 1000],
        "_row_number": [1, 2, 3, 4, 5]
    })
    prof = DataProfiler.profile(df)
    anomaly_issue = {
        "id": "outlier_val",
        "category": "anomaly",
        "check_type": "statistical_outlier",
        "column": "value",
        "is_anomaly_only": True,
        "affected_count": 1,
        "affected_rows": [5]
    }
    scores = ScoringEngine.calculate_scores(df, prof, issues=[anomaly_issue])
    # Anomaly issue should NOT drag down score
    assert scores["overall_score"] == 100.0
    assert scores["total_anomalies"] == 1
