from typing import Dict, Any, List
from agent.dataset_context import DatasetSessionContext

class ResultManager:
    """
    Formats, serializes, and aggregates analysis results for web UI consumption.
    """

    @classmethod
    def format_dashboard_payload(cls, session: DatasetSessionContext) -> Dict[str, Any]:
        """
        Builds a comprehensive JSON-safe payload for the dashboard.
        """
        return {
            "session_id": session.session_id,
            "filename": session.filename,
            "created_at": session.created_at,
            "metadata": session.metadata,
            "user_context": session.user_context,
            "overview": session.profile.get("overview", {}),
            "columns": session.profile.get("columns", {}),
            "scores": session.scores,
            "issues": session.issues,
            "ai_understanding": session.ai_understanding,
            "ai_plan": session.ai_plan,
            "ai_explanations": session.ai_explanations,
            "cleaning_audit": session.cleaning_audit,
            "has_cleaned_data": len(session.cleaning_audit) > 0
        }
