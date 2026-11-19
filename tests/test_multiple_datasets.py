import pytest
from pathlib import Path
import pandas as pd
from agent.orchestrator import DataGuardAgent
from engine.ingestion import IngestionError, DataIngestion
from config import Config

@pytest.fixture
def agent():
    return DataGuardAgent()

def test_online_store_orders_pipeline(agent):
    dataset_path = Config.SAMPLE_DATASETS_FOLDER / "online_store_orders.csv"
    assert dataset_path.exists()
    session = agent.process_dataset(dataset_path)

    assert session.session_id is not None
    assert len(session.issues) > 0
    assert session.scores["overall_score"] < 100.0
    assert "Completeness" in session.scores["formula"]

    # Verify cleaning preview
    issue = session.issues[0]
    preview = agent.preview_cleaning(session.session_id, issue["id"])
    assert "preview_samples" in preview

    # Verify cleaning execution on confirmed issues
    confirmed_issue_ids = [i["id"] for i in session.issues if not i.get("is_anomaly_only")]
    clean_res = agent.execute_cleaning(session.session_id, confirmed_issue_ids)
    assert clean_res["actions_applied"] >= 1
    assert clean_res["remaining_issues_count"] < len(session.issues)
    assert clean_res["new_score"] > clean_res["initial_score"]

    # Verify report exports
    artifacts = agent.export_reports(session.session_id)
    assert Path(Config.OUTPUT_FOLDER / artifacts["pdf_report"]).exists()
    assert Path(Config.OUTPUT_FOLDER / artifacts["excel_summary"]).exists()
    assert Path(Config.OUTPUT_FOLDER / artifacts["cleaned_csv"]).exists()

def test_employees_hr_domain(agent):
    dataset_path = Config.SAMPLE_DATASETS_FOLDER / "employees.csv"
    session = agent.process_dataset(dataset_path)
    assert len(session.issues) > 0
    assert "overall_score" in session.scores

def test_financial_transactions_domain(agent):
    dataset_path = Config.SAMPLE_DATASETS_FOLDER / "financial_transactions.csv"
    session = agent.process_dataset(dataset_path)
    assert len(session.issues) > 0

def test_healthcare_patients_domain(agent):
    dataset_path = Config.SAMPLE_DATASETS_FOLDER / "healthcare_patients.csv"
    session = agent.process_dataset(dataset_path)
    assert len(session.issues) > 0

def test_inventory_stock_domain(agent):
    dataset_path = Config.SAMPLE_DATASETS_FOLDER / "inventory_stock.csv"
    session = agent.process_dataset(dataset_path)
    assert len(session.issues) > 0

def test_empty_file_handling():
    empty_file = Config.OUTPUT_FOLDER / "empty_test.csv"
    empty_file.write_text("")
    with pytest.raises(IngestionError):
        DataIngestion.load_dataset(empty_file)

def test_unsupported_format_handling():
    fake_file = Config.OUTPUT_FOLDER / "test.exe"
    fake_file.write_text("not a table")
    with pytest.raises(IngestionError):
        DataIngestion.load_dataset(fake_file)
