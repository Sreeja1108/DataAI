import json
import logging
import os
import re
import time
from typing import Dict, Any, List, Optional
from config import Config
from ai.response_validator import (
    DatasetUnderstandingResponse,
    AdaptiveValidationPlanResponse,
    IssuesExplanationResponse,
    ColumnUnderstanding,
    RecommendedCheck,
    IssueExplanation
)
from ai.prompts import (
    build_dataset_understanding_prompt,
    build_validation_planning_prompt,
    build_issue_explanation_prompt
)

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Manages interaction with the Google Gemini API using the official google-genai SDK.
    Includes connection validation, retries, Pydantic response validation,
    and reliable heuristic fallbacks when offline or unconfigured.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model_name = model_name or Config.GEMINI_MODEL
        self.fallback_model = Config.GEMINI_FALLBACK_MODEL
        self._client = None
        self.is_connected = False
        self._initialize_client()

    def _initialize_client(self):
        """Initializes the google-genai Client if an API key is present."""
        if not self.api_key or self.api_key.startswith("your_"):
            logger.warning("No valid Gemini API key configured. Fallback heuristic AI engine will be used.")
            self.is_connected = False
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key, http_options={"timeout": 15000})
            self.is_connected = True
            logger.info("Gemini API client initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini Client: {e}. Fallback AI will be used.")
            self.is_connected = False

    def _extract_json_text(self, raw_text: str) -> str:
        """Strips markdown code blocks and returns cleanly formatted JSON string."""
        cleaned = raw_text.strip()
        # Remove ```json and ```
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def _call_gemini_with_fallback(self, prompt: str) -> Optional[str]:
        """Calls Gemini API with retries and fallback model."""
        if not self.is_connected or not self._client:
            return None

        models_to_try = [self.model_name, self.fallback_model]
        for model in models_to_try:
            for attempt in range(2):
                try:
                    response = self._client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    if response and response.text:
                        return response.text
                except Exception as e:
                    err_str = str(e)
                    logger.warning(f"Gemini call to model '{model}' attempt {attempt+1} failed: {err_str}")
                    # If network is completely offline/unreachable, avoid stalling further attempts
                    if "getaddrinfo failed" in err_str or "11001" in err_str or "Network is unreachable" in err_str:
                        logger.info("Network is unavailable. Switching to heuristic AI mode.")
                        self.is_connected = False
                        return None
                    time.sleep(1)
        return None

    def understand_dataset(
        self,
        compact_profile: Dict[str, Any],
        user_context: str = ""
    ) -> DatasetUnderstandingResponse:
        """
        Understands the dataset domain and column roles using Gemini.
        Falls back to rule-based inference if API is unavailable.
        """
        prompt = build_dataset_understanding_prompt(compact_profile, user_context)
        raw_output = self._call_gemini_with_fallback(prompt)

        if raw_output:
            try:
                json_str = self._extract_json_text(raw_output)
                parsed_data = json.loads(json_str)
                return DatasetUnderstandingResponse.model_validate(parsed_data)
            except Exception as e:
                logger.error(f"Failed to validate Gemini understanding response with Pydantic: {e}")

        # Intelligent Fallback Heuristic
        return self._fallback_understand_dataset(compact_profile, user_context)

    def plan_validation(
        self,
        domain: str,
        columns_profile: Dict[str, Any]
    ) -> AdaptiveValidationPlanResponse:
        """
        Generates an adaptive validation plan.
        """
        prompt = build_validation_planning_prompt(domain, columns_profile)
        raw_output = self._call_gemini_with_fallback(prompt)

        if raw_output:
            try:
                json_str = self._extract_json_text(raw_output)
                parsed_data = json.loads(json_str)
                return AdaptiveValidationPlanResponse.model_validate(parsed_data)
            except Exception as e:
                logger.error(f"Failed to validate Gemini validation plan response with Pydantic: {e}")

        return self._fallback_plan_validation(domain, columns_profile)

    def explain_issues(
        self,
        domain: str,
        verified_issues: List[Dict[str, Any]],
        overall_score: float
    ) -> IssuesExplanationResponse:
        """
        Generates business-friendly explanations and recommendations for verified issues.
        """
        if not verified_issues:
            return IssuesExplanationResponse(
                overall_summary=f"Dataset is in pristine health with a quality score of {overall_score}/100. No critical anomalies or defects detected.",
                explanations=[],
                immediate_action_items=["Maintain current data ingestion pipelines and ongoing validation monitors."]
            )

        prompt = build_issue_explanation_prompt(domain, verified_issues, overall_score)
        raw_output = self._call_gemini_with_fallback(prompt)

        if raw_output:
            try:
                json_str = self._extract_json_text(raw_output)
                parsed_data = json.loads(json_str)
                validated = IssuesExplanationResponse.model_validate(parsed_data)
                # Ensure verified counts were not altered by LLM
                verified_counts_map = {iss["id"]: iss["affected_count"] for iss in verified_issues}
                for exp in validated.explanations:
                    if exp.issue_id in verified_counts_map:
                        exp.affected_count = verified_counts_map[exp.issue_id]
                return validated
            except Exception as e:
                logger.error(f"Failed to validate Gemini issue explanations with Pydantic: {e}")

        return self._fallback_explain_issues(domain, verified_issues, overall_score)

    # ------------------- Robust Fallback Heuristics -------------------

    def _fallback_understand_dataset(
        self,
        compact_profile: Dict[str, Any],
        user_context: str
    ) -> DatasetUnderstandingResponse:
        """Rule-based domain inference and column role mapping."""
        cols = compact_profile.get("columns", {})
        col_names = [c.lower() for c in cols.keys()]
        all_cols_str = " ".join(col_names)

        # Domain inference heuristic
        if any(w in all_cols_str for w in ["order", "cart", "product", "sku", "shipping", "customer", "discount"]):
            domain = "E-Commerce & Retail"
            desc = "Commercial transactional data capturing consumer purchases, product fulfillment, and orders."
        elif any(w in all_cols_str for w in ["salary", "department", "employee", "hire", "termination", "job"]):
            domain = "Human Resources & Workforce"
            desc = "Workforce operational dataset capturing employee attributes, organizational hierarchy, and compensation."
        elif any(w in all_cols_str for w in ["patient", "diagnosis", "doctor", "blood", "prescription", "symptom"]):
            domain = "Healthcare & Clinical Records"
            desc = "Clinical dataset tracking patient records, diagnostic vitals, and treatment history."
        elif any(w in all_cols_str for w in ["transaction", "account", "balance", "credit", "debit", "interest"]):
            domain = "Banking & Financial Services"
            desc = "Financial ledger tracking accounts, monetary movements, and balance statements."
        elif any(w in all_cols_str for w in ["inventory", "warehouse", "stock", "supplier", "reorder"]):
            domain = "Supply Chain & Inventory Management"
            desc = "Logistical dataset recording inventory stock levels, supply depots, and replenishment cycles."
        else:
            domain = "General Enterprise Tabular Data"
            desc = "Structured business dataset containing multidimensional organizational measurements and entities."

        columns_understanding = []
        for col_name, col_meta in cols.items():
            sem = col_meta.get("semantic_type", "general_text")
            role = "primary_identifier" if sem == "identifier" else (
                "metric_measure" if sem == "numeric_measure" else (
                    "temporal_dimension" if sem == "date_timestamp" else "categorical_attribute"
                )
            )
            is_pii = any(term in col_name.lower() for term in ["name", "email", "phone", "ssn", "address"])
            columns_understanding.append(ColumnUnderstanding(
                column_name=col_name,
                inferred_meaning=f"Stores {sem.replace('_', ' ')} data representing {col_name.replace('_', ' ')}.",
                semantic_role=role,
                is_sensitive_or_pii=is_pii,
                confidence=0.88
            ))

        return DatasetUnderstandingResponse(
            probable_domain=domain,
            domain_description=desc,
            business_context_summary=user_context or f"Automated structural analysis for {domain} operations.",
            columns_understanding=columns_understanding,
            inferred_relationships=[
                "Identifiers uniquely anchor individual rows for transactional integrity.",
                "Temporal fields define event sequencing and lifecycle milestones."
            ],
            assumptions_made=[
                "Columns with unique ratios above 80% are treated as prospective entity keys.",
                "Statistical distributions reflect standard operational business conditions."
            ],
            suggested_validation_rules=[
                "Enforce mandatory presence on primary keys and essential categorical attributes.",
                "Verify non-negative numerical values across revenue, quantities, and pricing metrics.",
                "Standardize casing on category names and trim accidental whitespace."
            ],
            confidence_level=0.85
        )

    def _fallback_plan_validation(
        self,
        domain: str,
        columns_profile: Dict[str, Any]
    ) -> AdaptiveValidationPlanResponse:
        checks = []
        for col, meta in columns_profile.items():
            sem = meta.get("semantic_type")
            if sem == "identifier":
                checks.append(RecommendedCheck(
                    category="uniqueness",
                    column=col,
                    check_name="Primary Key Uniqueness",
                    rationale=f"'{col}' is identified as an entity key and must not have duplicate records.",
                    priority="high"
                ))
                checks.append(RecommendedCheck(
                    category="completeness",
                    column=col,
                    check_name="Key Completeness",
                    rationale=f"'{col}' cannot contain null or empty values.",
                    priority="high"
                ))
            elif sem == "email":
                checks.append(RecommendedCheck(
                    category="validity",
                    column=col,
                    check_name="RFC Email Format Validation",
                    rationale=f"Validates syntax of '{col}' email entries.",
                    priority="medium"
                ))
            elif sem == "date_timestamp":
                checks.append(RecommendedCheck(
                    category="validity",
                    column=col,
                    check_name="Timestamp Parsing & Format Standard",
                    rationale=f"Ensures '{col}' adheres to parseable date-time standards.",
                    priority="medium"
                ))
            elif sem == "numeric_measure":
                checks.append(RecommendedCheck(
                    category="anomaly",
                    column=col,
                    check_name="Statistical Outlier Boundary",
                    rationale=f"Monitors statistical dispersion (IQR & Z-score) in '{col}'.",
                    priority="low"
                ))
            elif sem == "category":
                checks.append(RecommendedCheck(
                    category="consistency",
                    column=col,
                    check_name="Category Casing Uniformity",
                    rationale=f"Prevents casing divergence in categorical field '{col}'.",
                    priority="medium"
                ))

        return AdaptiveValidationPlanResponse(
            domain_tailored_summary=f"Validation plan dynamically structured for {domain} datasets, prioritizing entity uniqueness and format precision.",
            recommended_checks=checks,
            skipped_checks_explanation="Skipped cross-table foreign key constraints as only single-table file was provided."
        )

    def _fallback_explain_issues(
        self,
        domain: str,
        verified_issues: List[Dict[str, Any]],
        overall_score: float
    ) -> IssuesExplanationResponse:
        explanations = []
        for iss in verified_issues:
            col = iss.get("column") or "Dataset"
            count = iss.get("affected_count", 0)
            rule = iss.get("cleaning_rule", "investigate")
            sev = iss.get("severity", "medium")

            if iss.get("category") == "completeness":
                exp = f"Missing data in '{col}' leaves records incomplete, which can distort analytics aggregates and disrupt downstream workflows."
                impact = "Leads to biased reporting, metric undercounting, and processing exceptions in reporting pipelines."
                sol = f"Impute missing values with statistical central tendency (median/mode) or populate with a known default flag."
                code = f"df['{col}'] = df['{col}'].fillna(df['{col}'].median())"
            elif iss.get("category") == "uniqueness":
                exp = f"Duplicate entries in '{col}' indicate redundant record ingestion or accidental multiple submissions."
                impact = "Inflates transaction counts, causes duplicate billing/processing, and skews cohort metrics."
                sol = "Deduplicate records by retaining the first occurrence and pruning subsequent duplicates."
                code = f"df = df.drop_duplicates(subset=['{col}'], keep='first')"
            elif iss.get("category") == "anomaly":
                exp = f"Values in '{col}' fall outside the expected statistical distribution boundaries."
                impact = "May represent extreme genuine events or typographical data entry errors."
                sol = "Inspect high-leverage records and apply outlier bounding (winsorization) if entry error is verified."
                code = f"df['{col}'] = df['{col}'].clip(lower=lower_bound, upper=upper_bound)"
            elif iss.get("category") == "consistency":
                exp = f"Formatting differences such as untrimmed whitespace or casing inconsistencies in '{col}'."
                impact = "Causes identical categories to group separately in SQL and BI dashboards."
                sol = f"Standardize text casing and strip whitespace."
                code = f"df['{col}'] = df['{col}'].astype(str).str.strip().str.title()"
            else:
                exp = f"Identified invalid format or value constraint violation in '{col}'."
                impact = "Breaks schema contracts and causes ingestion failures in relational databases."
                sol = "Filter or transform invalid entries to adhere to format specifications."
                code = f"df['{col}'] = df['{col}'].apply(validate_format)"

            explanations.append(IssueExplanation(
                issue_id=iss.get("id", "iss"),
                issue_title=iss.get("title", "Data Quality Issue"),
                simple_explanation=exp,
                affected_column=col,
                affected_count=count,
                business_impact=impact,
                severity=sev,
                recommended_solution=sol,
                suggested_pandas_code=code,
                confidence=0.92,
                assumptions="Assumes target column follows standard operational usage."
            ))

        return IssuesExplanationResponse(
            overall_summary=f"Automated audit revealed {len(verified_issues)} issue pattern(s) across {domain}. Overall dataset health rating is {overall_score}/100.",
            explanations=explanations,
            immediate_action_items=[
                "Review high-severity uniqueness and validity issues before executing automated transformations.",
                "Approve recommended cleaning rules in the DataGuard Cleaning console.",
                "Export sanitized dataset alongside the verification compliance report."
            ]
        )
