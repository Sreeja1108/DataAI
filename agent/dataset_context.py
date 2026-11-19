import time
from typing import Dict, Any, Optional, List
import pandas as pd

class DatasetSessionContext:
    """
    In-memory state management for active dataset analysis sessions.
    Stores original DataFrame, cleaned DataFrame, profile, issues, scores,
    and AI insight outputs.
    """
    _sessions: Dict[str, "DatasetSessionContext"] = {}

    def __init__(self, session_id: str, filename: str, original_df: pd.DataFrame, metadata: Dict[str, Any]):
        self.session_id = session_id
        self.filename = filename
        self.created_at = time.time()
        self.original_df = original_df # Preserved, NEVER modified
        self.cleaned_df = original_df.copy() # Transformed only upon user approval
        self.metadata = metadata
        self.user_context: str = ""
        self.profile: Dict[str, Any] = {}
        self.ai_understanding: Optional[Dict[str, Any]] = None
        self.ai_plan: Optional[Dict[str, Any]] = None
        self.issues: List[Dict[str, Any]] = []
        self.scores: Dict[str, Any] = {}
        self.ai_explanations: Optional[Dict[str, Any]] = None
        self.cleaning_audit: List[Dict[str, Any]] = []

    @classmethod
    def create_session(cls, session_id: str, filename: str, df: pd.DataFrame, metadata: Dict[str, Any]) -> "DatasetSessionContext":
        session = cls(session_id, filename, df, metadata)
        cls._sessions[session_id] = session
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional["DatasetSessionContext"]:
        return cls._sessions.get(session_id)

    @classmethod
    def list_recent_sessions(cls, limit: int = 5) -> List[Dict[str, Any]]:
        sorted_sessions = sorted(cls._sessions.values(), key=lambda s: s.created_at, reverse=True)
        return [
            {
                "session_id": s.session_id,
                "filename": s.filename,
                "created_at": s.created_at,
                "row_count": len(s.original_df),
                "column_count": len([c for c in s.original_df.columns if c != "_row_number"]),
                "overall_score": s.scores.get("overall_score"),
                "health": s.scores.get("health", "Analyzed")
            }
            for s in sorted_sessions[:limit]
        ]
