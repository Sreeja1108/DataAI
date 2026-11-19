import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from engine.ingestion import DataIngestion
from engine.profiler import DataProfiler
from engine.scoring_engine import ScoringEngine
from agent.dataset_context import DatasetSessionContext
from agent.rule_planner import DetectorRegistry
from agent.result_manager import ResultManager
from ai.gemini_service import GeminiService
from cleaning.cleaning_engine import CleaningEngine
from reports.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class DataGuardAgent:
    """
    Master Autonomous Agent Orchestrator for DataGuard AI.
    Executes connected multi-step analysis workflow from Ingestion to Reporting.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_service = GeminiService(api_key=gemini_api_key)
        self.detector_registry = DetectorRegistry()

    def process_dataset(
        self,
        file_path: Path,
        user_context: str = "",
        max_rows: Optional[int] = None
    ) -> DatasetSessionContext:
        """
        Executes Steps 1 through 7 for a newly uploaded dataset.
        """
        session_id = uuid.uuid4().hex[:12]
        logger.info(f"Starting DataGuard analysis session: {session_id} for file: {file_path.name}")

        # STEP 1: DATASET INGESTION
        original_df, metadata = DataIngestion.load_dataset(file_path, max_rows=max_rows)
        session = DatasetSessionContext.create_session(session_id, file_path.name, original_df, metadata)
        session.user_context = user_context

        # STEP 2: AUTOMATIC DATA PROFILING
        logger.info(f"Session {session_id}: Profiling {len(original_df)} rows and {len(original_df.columns)} columns.")
        profile = DataProfiler.profile(original_df)
        session.profile = profile

        # STEP 3: AI DATASET UNDERSTANDING (Gemini)
        logger.info(f"Session {session_id}: Sending compact profile to Gemini for domain understanding.")
        compact_summary = DataProfiler.get_compact_summary_for_llm(profile)
        ai_understanding = self.gemini_service.understand_dataset(compact_summary, user_context=user_context)
        session.ai_understanding = ai_understanding.model_dump()

        # STEP 4: ADAPTIVE VALIDATION PLANNING (Gemini)
        logger.info(f"Session {session_id}: Formulating adaptive validation plan.")
        domain = session.ai_understanding.get("probable_domain", "General Enterprise Data")
        ai_plan = self.gemini_service.plan_validation(domain, profile.get("columns", {}))
        session.ai_plan = ai_plan.model_dump()

        # STEP 5: ISSUE DETECTION (Python deterministic execution as ground truth)
        logger.info(f"Session {session_id}: Executing deterministic detector registry.")
        issues = self.detector_registry.execute_all(original_df, profile)
        session.issues = issues

        # STEP 6: QUALITY SCORING (Deterministic 25/20/30/25 formula)
        logger.info(f"Session {session_id}: Computing multi-dimensional quality scores.")
        scores = ScoringEngine.calculate_scores(original_df, profile, issues)
        session.scores = scores

        # STEP 7: GEMINI EXPLANATIONS (Ground-truth verified AI issue explanations)
        logger.info(f"Session {session_id}: Requesting Gemini business explanations and pandas code.")
        ai_explanations = self.gemini_service.explain_issues(
            domain=domain,
            verified_issues=issues,
            overall_score=scores.get("overall_score", 100.0)
        )
        session.ai_explanations = ai_explanations.model_dump()

        logger.info(f"Session {session_id} analysis complete. Overall score: {scores.get('overall_score')}%")
        return session

    def preview_cleaning(self, session_id: str, issue_id: str) -> Dict[str, Any]:
        """
        STEP 8 Part A: Generates before-and-after preview for an individual issue.
        """
        session = DatasetSessionContext.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        issue = next((i for i in session.issues if i["id"] == issue_id), None)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found in session {session_id}.")

        preview_rows = CleaningEngine.generate_preview(session.original_df, issue)
        return {
            "issue_id": issue_id,
            "title": issue["title"],
            "cleaning_rule": issue.get("cleaning_rule"),
            "preview_samples": preview_rows
        }

    def execute_cleaning(self, session_id: str, approved_issue_ids: list) -> Dict[str, Any]:
        """
        STEP 8 Part B: Applies approved operations onto a fresh copy of the dataset.
        """
        session = DatasetSessionContext.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        cleaned_df, audit_log = CleaningEngine.apply_cleaning(
            df=session.original_df,
            approved_issue_ids=approved_issue_ids,
            all_issues=session.issues
        )

        session.cleaned_df = cleaned_df
        session.cleaning_audit = audit_log

        # Re-score the cleaned DataFrame to show quality improvement!
        re_profile = DataProfiler.profile(cleaned_df)
        re_issues = self.detector_registry.execute_all(cleaned_df, re_profile)
        re_scores = ScoringEngine.calculate_scores(cleaned_df, re_profile, re_issues)

        return {
            "session_id": session_id,
            "actions_applied": len(audit_log),
            "audit_log": audit_log,
            "initial_score": session.scores.get("overall_score"),
            "new_score": re_scores.get("overall_score"),
            "remaining_issues_count": len(re_issues)
        }

    def export_reports(self, session_id: str) -> Dict[str, str]:
        """
        STEP 9: Generates downloadable PDF, Excel, and cleaned data artifacts.
        """
        session = DatasetSessionContext.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        pdf_path = ReportGenerator.generate_pdf_report(
            session_id=session.session_id,
            dataset_name=session.filename,
            overview=session.profile.get("overview", {}),
            scores=session.scores,
            issues=session.issues,
            ai_understanding=session.ai_understanding,
            ai_explanations=session.ai_explanations,
            cleaning_audit=session.cleaning_audit
        )

        excel_path = ReportGenerator.generate_excel_summary(
            session_id=session.session_id,
            dataset_name=session.filename,
            overview=session.profile.get("overview", {}),
            scores=session.scores,
            issues=session.issues,
            ai_understanding=session.ai_understanding,
            cleaning_audit=session.cleaning_audit
        )

        cleaned_csv_path = CleaningEngine.export_cleaned_dataset(session.cleaned_df, session.session_id, "csv")
        cleaned_xlsx_path = CleaningEngine.export_cleaned_dataset(session.cleaned_df, session.session_id, "xlsx")

        return {
            "pdf_report": pdf_path.name,
            "excel_summary": excel_path.name,
            "cleaned_csv": cleaned_csv_path.name,
            "cleaned_xlsx": cleaned_xlsx_path.name
        }
