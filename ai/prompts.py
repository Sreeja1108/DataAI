import json
from typing import Dict, Any, List

def build_dataset_understanding_prompt(
    compact_profile: Dict[str, Any],
    user_context: str = ""
) -> str:
    """
    Constructs the prompt for initial dataset understanding and domain inference.
    """
    context_part = f"\nUser-Provided Context / Business Description:\n'{user_context}'\n" if user_context else ""

    return f"""You are DataGuard AI, an elite autonomous data architect and quality consultant.
Analyze this compact tabular dataset profiling summary to understand its business domain and column roles.
{context_part}
Dataset Profile Summary:
{json.dumps(compact_profile, indent=2)}

TASK:
1. Infer the probable dataset domain (e.g., E-Commerce, Human Resources, Healthcare, Finance, Logistics, Education, SaaS, Inventory, etc.).
2. For each column, explain its likely real-world meaning and semantic role (identifier, measure, category, date, etc.).
3. Identify potential relationships between columns (e.g. order_date vs delivery_date, price vs total, etc.).
4. Clearly distinguish verified facts from assumptions made.
5. Suggest relevant data validation rules.

OUTPUT FORMAT:
Return a valid JSON object matching this schema:
{{
  "probable_domain": "string",
  "domain_description": "string",
  "business_context_summary": "string",
  "columns_understanding": [
    {{
      "column_name": "string",
      "inferred_meaning": "string",
      "semantic_role": "string",
      "is_sensitive_or_pii": false,
      "confidence": 0.9
    }}
  ],
  "inferred_relationships": ["string"],
  "assumptions_made": ["string"],
  "suggested_validation_rules": ["string"],
  "confidence_level": 0.88
}}
Return ONLY valid JSON. Do not include markdown code block syntax or extra text.
"""

def build_validation_planning_prompt(
    domain: str,
    columns_summary: Dict[str, Any]
) -> str:
    """
    Constructs the prompt to recommend adaptive validation checks.
    """
    return f"""You are DataGuard AI. Given the inferred domain '{domain}' and column profiles:
Columns Profile:
{json.dumps(columns_summary, indent=2)}

TASK:
Recommend applicable validation rules.
Do NOT assume every numeric column is a measurement or every text column is a category.
Do NOT assume all columns must be unique.
Recommend rules across: Completeness, Uniqueness, Validity, Consistency, Statistical Anomaly, Structural Integrity.

OUTPUT FORMAT:
Return a valid JSON object matching this schema:
{{
  "domain_tailored_summary": "string",
  "recommended_checks": [
    {{
      "category": "completeness" | "uniqueness" | "validity" | "consistency" | "anomaly" | "integrity",
      "column": "column_name or null",
      "check_name": "string",
      "rationale": "string",
      "priority": "high" | "medium" | "low"
    }}
  ],
  "skipped_checks_explanation": "string"
}}
Return ONLY valid JSON.
"""

def build_issue_explanation_prompt(
    domain: str,
    verified_issues: List[Dict[str, Any]],
    overall_score: float
) -> str:
    """
    Constructs prompt to explain verified deterministic issues in plain language.
    CRITICAL: Gemini must NEVER invent counts or modify verified counts.
    """
    # Prepare minimal representation of verified issues
    issues_for_llm = []
    for iss in verified_issues:
        issues_for_llm.append({
            "id": iss.get("id"),
            "title": iss.get("title"),
            "category": iss.get("category"),
            "column": iss.get("column"),
            "affected_count": iss.get("affected_count"),
            "affected_pct": iss.get("affected_pct"),
            "severity": iss.get("severity"),
            "problematic_samples": iss.get("problematic_samples", [])[:3]
        })

    return f"""You are DataGuard AI, explaining verified data quality findings for a '{domain}' dataset.
Overall Dataset Quality Score: {overall_score}/100.

Verified Issues List:
{json.dumps(issues_for_llm, indent=2)}

TASK:
For each verified issue:
1. Provide a clear, non-technical explanation suitable for business stakeholders.
2. Explain the potential business or operational impact if this issue is not fixed.
3. Recommend the best remediation strategy.
4. Provide standard, safe pandas cleaning code (as documentation only; this code will not be executed directly).
IMPORTANT:
- NEVER invent or alter the issue counts or severity. Use the exact affected_count and severity provided.
- Return ONLY valid JSON.

OUTPUT FORMAT:
{{
  "overall_summary": "Executive summary of dataset health",
  "explanations": [
    {{
      "issue_id": "matching issue id",
      "issue_title": "string",
      "simple_explanation": "string",
      "affected_column": "column name or null",
      "affected_count": integer,
      "business_impact": "string",
      "severity": "high" | "medium" | "low" | "info",
      "recommended_solution": "string",
      "suggested_pandas_code": "df['col'] = ...",
      "confidence": 0.95,
      "assumptions": "string"
    }}
  ],
  "immediate_action_items": ["string"]
}}
"""
