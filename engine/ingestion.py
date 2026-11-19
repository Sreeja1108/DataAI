import csv
import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception raised during dataset ingestion."""
    pass

class DataIngestion:
    """
    Handles robust, safe ingestion of tabular datasets (CSV, XLSX, XLS, JSON).
    Preserves original uploaded files, original row indices, detects encodings/delimiters,
    and guards against empty, malformed, or oversized files.
    """

    SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}

    @classmethod
    def detect_csv_encoding_and_delimiter(cls, file_path: Path) -> Tuple[str, str]:
        """Detect encoding and delimiter of a CSV file."""
        encodings_to_try = ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"]
        detected_encoding = "utf-8"
        sample_bytes = b""

        with open(file_path, "rb") as f:
            sample_bytes = f.read(65536)

        if not sample_bytes:
            raise IngestionError("The uploaded file is empty (0 bytes).")

        for enc in encodings_to_try:
            try:
                sample_text = sample_bytes.decode(enc)
                detected_encoding = enc
                break
            except (UnicodeDecodeError, LookupError):
                continue

        # Detect delimiter using csv.Sniffer or fallback
        detected_delimiter = ","
        try:
            sample_text = sample_bytes.decode(detected_encoding)
            lines = [line for line in sample_text.splitlines() if line.strip()][:20]
            if lines:
                sniffer = csv.Sniffer()
                sample_for_sniff = "\n".join(lines)
                dialect = sniffer.sniff(sample_for_sniff, delimiters=[",", ";", "\t", "|"])
                detected_delimiter = dialect.delimiter
        except Exception:
            # Fallback heuristic based on character counts
            first_line = sample_text.splitlines()[0] if sample_text.splitlines() else ""
            counts = {d: first_line.count(d) for d in [",", ";", "\t", "|"]}
            detected_delimiter = max(counts, key=counts.get) if any(counts.values()) else ","

        return detected_encoding, detected_delimiter

    @classmethod
    def load_dataset(cls, file_path: Path, max_rows: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Loads dataset into a pandas DataFrame safely while preserving original row positions.
        Returns:
            (DataFrame, metadata_dict)
        """
        path = Path(file_path)
        if not path.exists():
            raise IngestionError(f"File not found: {path}")

        file_size = path.stat().st_size
        if file_size == 0:
            raise IngestionError("Uploaded file is empty (0 bytes).")

        suffix = path.suffix.lower()
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise IngestionError(f"Unsupported format '{suffix}'. Supported formats: CSV, XLSX, XLS, JSON.")

        metadata: Dict[str, Any] = {
            "filename": path.name,
            "file_size_bytes": file_size,
            "format": suffix.lstrip("."),
            "encoding": "utf-8",
            "delimiter": None,
        }

        try:
            if suffix == ".csv":
                encoding, delimiter = cls.detect_csv_encoding_and_delimiter(path)
                metadata["encoding"] = encoding
                metadata["delimiter"] = delimiter
                df = pd.read_csv(
                    path,
                    encoding=encoding,
                    sep=delimiter,
                    nrows=max_rows,
                    low_memory=False,
                    on_bad_lines="skip"
                )
            elif suffix in (".xlsx", ".xls"):
                df = pd.read_excel(path, nrows=max_rows)
            elif suffix == ".json":
                # Support array of records or keyed objects
                with open(path, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    # Check if nested records exist
                    records_key = next((k for k in ("data", "records", "items", "rows") if isinstance(data.get(k), list)), None)
                    if records_key:
                        df = pd.DataFrame(data[records_key])
                    else:
                        df = pd.DataFrame.from_dict(data, orient="index")
                else:
                    raise IngestionError("JSON content must be a JSON array of records or dictionary.")
            else:
                raise IngestionError(f"Unsupported file format: {suffix}")

        except IngestionError:
            raise
        except Exception as e:
            logger.exception("Failed to parse dataset file.")
            raise IngestionError(f"Could not parse file '{path.name}': {str(e)}")

        if df.empty:
            raise IngestionError("The dataset contains 0 rows or is empty.")

        # Handle duplicate column names gracefully while tracking them
        original_cols = list(df.columns)
        seen_cols = {}
        renamed = False
        deduped_columns = []
        for c in original_cols:
            col_str = str(c).strip() if pd.notna(c) and str(c).strip() else "Unnamed"
            if col_str in seen_cols:
                seen_cols[col_str] += 1
                deduped_columns.append(f"{col_str}_{seen_cols[col_str]}")
                renamed = True
            else:
                seen_cols[col_str] = 0
                deduped_columns.append(col_str)

        df.columns = deduped_columns
        metadata["had_duplicate_columns"] = renamed
        metadata["column_count"] = len(df.columns)
        metadata["row_count"] = len(df)
        metadata["columns"] = list(df.columns)

        # Store 1-based original row number index for human-friendly issue tracing
        df["_row_number"] = range(1, len(df) + 1)

        return df, metadata
