from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ColumnUnderstanding(BaseModel):
    column_name: str
    inferred_meaning: str
    semantic_role: str = Field(description="e.g. primary_identifier, foreign_key, demographic, financial_metric, temporal, categorical_feature")
    is_sensitive_or_pii: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)

class DatasetUnderstandingResponse(BaseModel):
    probable_domain: str = Field(description="e.g. E-Commerce, Healthcare, Human Resources, Financial Banking, Logistics/Supply Chain")
    domain_description: str
    business_context_summary: str
    columns_understanding: List[ColumnUnderstanding] = []
    inferred_relationships: List[str] = []
    assumptions_made: List[str] = []
    suggested_validation_rules: List[str] = []
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.85)

class RecommendedCheck(BaseModel):
    category: str = Field(description="completeness, uniqueness, validity, consistency, anomaly, integrity")
    column: Optional[str] = None
    check_name: str
    rationale: str
    priority: str = Field(default="medium", description="high, medium, low")

class AdaptiveValidationPlanResponse(BaseModel):
    domain_tailored_summary: str
    recommended_checks: List[RecommendedCheck] = []
    skipped_checks_explanation: str = ""

class IssueExplanation(BaseModel):
    issue_id: str
    issue_title: str
    simple_explanation: str
    affected_column: Optional[str] = None
    affected_count: int
    business_impact: str
    severity: str = Field(description="high, medium, low, info")
    recommended_solution: str
    suggested_pandas_code: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)
    assumptions: str = ""

class IssuesExplanationResponse(BaseModel):
    overall_summary: str
    explanations: List[IssueExplanation] = []
    immediate_action_items: List[str] = []
