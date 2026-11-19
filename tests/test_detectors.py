import pytest
import pandas as pd
import numpy as np
from engine.profiler import DataProfiler
from engine.missing_detector import MissingValueDetector
from engine.duplicate_detector import DuplicateDetector
from engine.outlier_detector import OutlierDetector
from engine.validity_detector import ValidityDetector
from engine.consistency_detector import ConsistencyDetector
from engine.integrity_detector import IntegrityDetector

def test_missing_detector():
    df = pd.DataFrame({
        "name": ["Alice", "Bob", None, "   "],
        "_row_number": [1, 2, 3, 4]
    })
    prof = DataProfiler.profile(df)
    issues = MissingValueDetector.detect(df, prof)
    assert len(issues) == 1
    assert issues[0]["category"] == "completeness"
    assert issues[0]["affected_count"] == 2

def test_duplicate_detector():
    df = pd.DataFrame({
        "user_id": ["USR-1", "USR-2", "USR-1"],
        "score": [10, 20, 10],
        "_row_number": [1, 2, 3]
    })
    prof = DataProfiler.profile(df)
    issues = DuplicateDetector.detect(df, prof)
    check_types = [i["check_type"] for i in issues]
    assert "duplicate_rows" in check_types or "duplicate_identifier" in check_types

def test_outlier_detector():
    # 20 standard values and 1 extreme outlier
    values = [10.0] * 19 + [10000.0]
    df = pd.DataFrame({
        "transaction_amount": values,
        "_row_number": list(range(1, 21))
    })
    prof = DataProfiler.profile(df)
    issues = OutlierDetector.detect(df, prof)
    assert len(issues) == 1
    assert issues[0]["category"] == "anomaly"
    assert issues[0]["is_anomaly_only"] is True

def test_validity_detector_invalid_email_and_negatives():
    df = pd.DataFrame({
        "contact_email": ["good@test.com", "bad-email-without-at", "another@domain.org"],
        "unit_price": [25.0, -10.0, 50.0],
        "_row_number": [1, 2, 3]
    })
    prof = DataProfiler.profile(df)
    issues = ValidityDetector.detect(df, prof)
    check_types = [i["check_type"] for i in issues]
    assert "invalid_email_format" in check_types
    assert "invalid_range" in check_types

def test_consistency_detector_whitespace_and_casing():
    df = pd.DataFrame({
        "status": ["Active", "active", "ACTIVE", "Pending"],
        "city": ["New York", " Chicago ", "Dallas", "Miami"],
        "_row_number": [1, 2, 3, 4]
    })
    prof = DataProfiler.profile(df)
    issues = ConsistencyDetector.detect(df, prof)
    check_types = [i["check_type"] for i in issues]
    assert "inconsistent_capitalization" in check_types
    assert "untrimmed_whitespace" in check_types

def test_integrity_detector_date_inversion():
    df = pd.DataFrame({
        "start_date": ["2026-01-01", "2026-01-10"],
        "end_date": ["2026-01-05", "2026-01-02"], # Second row has end_date < start_date
        "_row_number": [1, 2]
    })
    prof = DataProfiler.profile(df)
    issues = IntegrityDetector.detect(df, prof)
    assert len(issues) == 1
    assert issues[0]["check_type"] == "temporal_order_violation"
    assert 2 in issues[0]["affected_rows"]
