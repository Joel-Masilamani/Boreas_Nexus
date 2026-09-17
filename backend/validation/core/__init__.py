"""
Unified Validation Core Framework

Provides standardized data models, status enumerations (PASS / WARN / FAIL),
configuration loaders, and reporting schemas for all Boreas-Nexus validation engines.
"""

from validation.core.models import (
    ValidationStatus,
    ValidationResult,
    CheckSummary,
    DatasetValidationReport
)
from validation.core.config import BaseValidationConfig

__all__ = [
    "ValidationStatus",
    "ValidationResult",
    "CheckSummary",
    "DatasetValidationReport",
    "BaseValidationConfig"
]
