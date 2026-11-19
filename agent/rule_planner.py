import logging
from typing import List, Dict, Any, Type
import pandas as pd
from engine.missing_detector import MissingValueDetector
from engine.duplicate_detector import DuplicateDetector
from engine.outlier_detector import OutlierDetector
from engine.validity_detector import ValidityDetector
from engine.consistency_detector import ConsistencyDetector
from engine.integrity_detector import IntegrityDetector

logger = logging.getLogger(__name__)

class DetectorRegistry:
    """
    Reusable registry of deterministic Python detector modules.
    Executes applicable detectors against the dataset based on type profiling
    and AI adaptive recommendations.
    """

    def __init__(self):
        self._detectors: List[Any] = [
            MissingValueDetector,
            DuplicateDetector,
            ValidityDetector,
            ConsistencyDetector,
            IntegrityDetector,
            OutlierDetector
        ]

    def register_detector(self, detector_cls):
        """Allows registering custom or domain-specific detectors."""
        if detector_cls not in self._detectors:
            self._detectors.append(detector_cls)

    def execute_all(self, df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Runs all registered detectors against the DataFrame and profile.
        Aggregates detected issues into a clean unified list.
        """
        all_issues = []
        for detector in self._detectors:
            try:
                detector_issues = detector.detect(df, profile)
                all_issues.extend(detector_issues)
            except Exception as e:
                logger.exception(f"Detector {detector.__name__} failed execution: {e}")

        # Assign unique sequence IDs if needed
        for idx, iss in enumerate(all_issues, 1):
            if "id" not in iss or not iss["id"]:
                iss["id"] = f"iss_{idx}"

        return all_issues
