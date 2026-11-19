import pytest
import pandas as pd
import numpy as np
from engine.profiler import DataProfiler
from engine.type_inference import TypeInferrer

def test_type_inferrer_numeric_and_identifier():
    series_id = pd.Series([101, 102, 103, 104, 105])
    info_id = TypeInferrer.infer_column_type(series_id, "customer_id")
    assert info_id["physical_type"] == "integer"
    assert info_id["semantic_type"] == "identifier"

    series_float = pd.Series([12.5, 45.0, 99.9, 10.2, 5.0])
    info_float = TypeInferrer.infer_column_type(series_float, "item_price")
    assert info_float["physical_type"] == "float"
    assert info_float["semantic_type"] == "numeric_measure"

def test_type_inferrer_email():
    emails = pd.Series(["user1@test.com", "user2@domain.org", "alice@wonder.net"])
    info = TypeInferrer.infer_column_type(emails, "email_address")
    assert info["semantic_type"] == "email"

def test_type_inferrer_dates():
    dates = pd.Series(["2026-01-01", "2026-01-02", "2026-01-03"])
    info = TypeInferrer.infer_column_type(dates, "created_at")
    assert info["semantic_type"] == "date_timestamp"

def test_profiler_statistics_and_missing():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "category": ["A", "B", "A", " ", None],
        "revenue": [100.0, 200.0, 300.0, None, 500.0],
        "_row_number": [1, 2, 3, 4, 5]
    })
    profile = DataProfiler.profile(df)
    overview = profile["overview"]
    assert overview["row_count"] == 5
    assert overview["column_count"] == 3

    cols = profile["columns"]
    assert "revenue" in cols
    rev_stats = cols["revenue"]["statistics"]
    assert rev_stats["min"] == 100.0
    assert rev_stats["max"] == 500.0
    assert cols["category"]["total_missing"] == 2 # 1 None + 1 whitespace
