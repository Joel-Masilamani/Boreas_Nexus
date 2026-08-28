"""
Module 2 Validation Configuration Loader
"""

from pathlib import Path
from typing import Dict, Any, Optional
from validation.core.config import BaseValidationConfig


class ValidationConfig(BaseValidationConfig):
    """Configuration loader for Module 2 validation suite."""

    def __init__(self, config_path: Path | str = Path("config/module2_validation_config.yaml")):
        super().__init__(config_path=config_path)
