"""
Base Validation Configuration Loader
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from utils.logger import logger


class BaseValidationConfig:
    """Encapsulates YAML validation settings and tolerances."""

    def __init__(self, config_path: Path | str):
        self.config_path = Path(config_path)
        self.raw_cfg = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            logger.warning(f"Validation config not found at {self.config_path}. Using empty config.")
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading validation config {self.config_path}: {e}")
            return {}

    @property
    def version(self) -> str:
        return self.raw_cfg.get("version", "1.0.0")

    @property
    def dataset_path(self) -> Path:
        return Path(self.raw_cfg.get("dataset_path", ""))

    @property
    def output_dir(self) -> Path:
        return Path(self.raw_cfg.get("output_dir", "data/validation"))

    def get_section(self, section_name: str) -> Dict[str, Any]:
        return self.raw_cfg.get(section_name, {})
