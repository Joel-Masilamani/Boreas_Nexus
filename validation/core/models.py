"""
Unified Validation Data Models & Schemas

Standardizes validation results, check summaries, and dataset reports across all modules.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, Optional, List, Union
import json
import numpy as np


class ValidationStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class ValidationResult:
    """Represents a single validation check result."""
    validation_id: str
    validation_type: str
    metric: str
    expected: Any
    actual: Any
    status: ValidationStatus
    message: str
    point_id: Optional[str] = None
    block_id: Optional[Union[str, int]] = None
    error: Optional[float] = None
    threshold: Optional[Any] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        for k, v in d.items():
            if isinstance(v, (np.floating, float)) and (np.isnan(v) or np.isinf(v)):
                d[k] = str(v)
        return d


@dataclass
class CheckSummary:
    """Summary of a specific category of validation checks."""
    category: str
    total_checks: int
    pass_count: int
    warn_count: int
    fail_count: int
    status: ValidationStatus
    findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class DatasetValidationReport:
    """Dataset-level consolidated validation report."""
    dataset: str
    validation_run_id: str
    timestamp: str
    configuration_version: str
    total_checks: int
    pass_count: int
    warn_count: int
    fail_count: int
    overall_status: ValidationStatus
    configuration_gaps: List[Dict[str, Any]] = field(default_factory=list)
    critical_findings: List[Dict[str, Any]] = field(default_factory=list)
    manual_inspection_items: List[Dict[str, Any]] = field(default_factory=list)
    validation_summaries: Dict[str, Any] = field(default_factory=dict)
    validation_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["overall_status"] = self.overall_status.value
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)
