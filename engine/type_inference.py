import re
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Semantic regex patterns
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^(\+?\d{1,4}[-.\s]?)?(\(?\d{1,4}\)?[-.\s]?)?[\d\s.-]{6,15}$")
URL_REGEX = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
DATE_PATTERN_HINTS = re.compile(r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})")
ID_COL_REGEX = re.compile(r"(^id$|_id$|id_|^uuid$|guid|^code$|ref(erence)?|num(ber)?|ssn|ein|sku|serial)", re.IGNORECASE)

class TypeInferrer:
    """
    Infers physical and semantic data types for columns in a tabular dataset
    without hardcoding specific domain column names.
    """

    @classmethod
    def infer_column_type(cls, series: pd.Series, col_name: str) -> Dict[str, Any]:
        """
        Analyzes a single Series to determine its physical type, semantic type,
        mixed-type presence, and candidate patterns.
        """
        # Exclude internal tracking columns
        if col_name == "_row_number":
            return {"physical_type": "integer", "semantic_type": "row_index", "is_mixed": False}

        non_null_series = series.dropna()
        total_non_null = len(non_null_series)

        if total_non_null == 0:
            return {
                "physical_type": "empty",
                "semantic_type": "unknown",
                "is_mixed": False,
                "confidence": 1.0,
                "detected_formats": []
            }

        sample_size = min(total_non_null, 1000)
        sample = non_null_series.sample(n=sample_size, random_state=42) if total_non_null > 1000 else non_null_series

        # Check Python native types inside the sample to detect mixed types
        native_types = {type(v).__name__ for v in sample}
        is_mixed = len(native_types) > 1

        # Check if already recognized as datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return {
                "physical_type": "datetime",
                "semantic_type": "date_timestamp",
                "is_mixed": is_mixed,
                "confidence": 0.98,
                "detected_formats": ["iso8601"]
            }

        # Check boolean
        if pd.api.types.is_bool_dtype(series):
            return {
                "physical_type": "boolean",
                "semantic_type": "boolean_flag",
                "is_mixed": False,
                "confidence": 1.0,
                "detected_formats": ["boolean"]
            }

        # String representations of values
        str_sample = [str(x).strip() for x in sample]

        # Check if boolean represented as string (e.g. true/false, yes/no, 0/1)
        bool_strings = {"true", "false", "yes", "no", "y", "n", "0", "1", "t", "f"}
        if all(s.lower() in bool_strings for s in str_sample if s):
            return {
                "physical_type": "boolean",
                "semantic_type": "boolean_flag",
                "is_mixed": is_mixed,
                "confidence": 0.90,
                "detected_formats": ["boolean_string"]
            }

        # Numeric check
        if pd.api.types.is_numeric_dtype(series):
            is_int = pd.api.types.is_integer_dtype(series) or (series.dropna() % 1 == 0).all()
            unique_ratio = series.nunique() / total_non_null if total_non_null > 0 else 0

            # Could it be an ID / identifier?
            if is_int and (unique_ratio > 0.85 or ID_COL_REGEX.search(col_name)):
                semantic = "identifier"
            elif series.min() >= 0 and series.max() <= 1 and not is_int:
                semantic = "ratio_or_probability"
            elif series.min() >= 0 and series.max() <= 100 and "pct" in col_name.lower():
                semantic = "percentage"
            else:
                semantic = "numeric_measure"

            return {
                "physical_type": "integer" if is_int else "float",
                "semantic_type": semantic,
                "is_mixed": is_mixed,
                "confidence": 0.95,
                "detected_formats": ["numeric"]
            }

        # String / Object types: Try parsing as datetime
        date_matches = 0
        email_matches = 0
        phone_matches = 0
        url_matches = 0
        uuid_matches = 0
        numeric_convertible = 0

        for val in str_sample:
            if not val:
                continue
            if EMAIL_REGEX.match(val):
                email_matches += 1
            if PHONE_REGEX.match(val):
                phone_matches += 1
            if URL_REGEX.match(val):
                url_matches += 1
            if UUID_REGEX.match(val):
                uuid_matches += 1
            try:
                float(val.replace(",", "").replace("$", "").replace("€", "").replace("£", ""))
                numeric_convertible += 1
            except ValueError:
                pass
            if DATE_PATTERN_HINTS.search(val):
                date_matches += 1

        sample_len = len(str_sample) or 1
        # Date parsing attempt (check dates BEFORE phone numbers to avoid phone regex false positives)
        if date_matches / sample_len > 0.5:
            try:
                pd.to_datetime(sample, errors="coerce", format="mixed")
                return {
                    "physical_type": "datetime",
                    "semantic_type": "date_timestamp",
                    "is_mixed": is_mixed,
                    "confidence": 0.90,
                    "detected_formats": ["datetime_string"]
                }
            except Exception:
                pass

        if email_matches / sample_len > 0.6:
            return {
                "physical_type": "string",
                "semantic_type": "email",
                "is_mixed": is_mixed,
                "confidence": round(email_matches / sample_len, 2),
                "detected_formats": ["email"]
            }

        if url_matches / sample_len > 0.6:
            return {
                "physical_type": "string",
                "semantic_type": "url",
                "is_mixed": is_mixed,
                "confidence": round(url_matches / sample_len, 2),
                "detected_formats": ["url"]
            }

        if uuid_matches / sample_len > 0.6:
            return {
                "physical_type": "string",
                "semantic_type": "identifier",
                "is_mixed": is_mixed,
                "confidence": 0.99,
                "detected_formats": ["uuid"]
            }

        if phone_matches / sample_len > 0.6 and not (numeric_convertible / sample_len > 0.9):
            return {
                "physical_type": "string",
                "semantic_type": "phone_number",
                "is_mixed": is_mixed,
                "confidence": round(phone_matches / sample_len, 2),
                "detected_formats": ["phone"]
            }

        # Check if numeric values stored as strings (e.g. currency "$12.50" or numbers with commas)
        if numeric_convertible / sample_len > 0.8:
            return {
                "physical_type": "string_numeric",
                "semantic_type": "numeric_measure",
                "is_mixed": True,
                "confidence": 0.85,
                "detected_formats": ["numeric_string"]
            }

        # Categorical vs General Text
        unique_count = series.nunique()
        unique_ratio = unique_count / total_non_null if total_non_null > 0 else 0

        # Identifier check for string codes / IDs
        if ID_COL_REGEX.search(col_name) and unique_ratio > 0.7:
            return {
                "physical_type": "string",
                "semantic_type": "identifier",
                "is_mixed": is_mixed,
                "confidence": 0.85,
                "detected_formats": ["identifier_code"]
            }

        if unique_count <= 50 or unique_ratio < 0.05:
            return {
                "physical_type": "categorical",
                "semantic_type": "category",
                "is_mixed": is_mixed,
                "confidence": 0.88,
                "detected_formats": ["category"]
            }

        return {
            "physical_type": "string",
            "semantic_type": "general_text",
            "is_mixed": is_mixed,
            "confidence": 0.80,
            "detected_formats": ["text"]
        }
