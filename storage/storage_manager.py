"""
Boreas-Nexus Centralized Storage Manager Module

Provides production-grade path resolution, module output ownership, separation
of internal GeoParquet/Parquet formats from exports (GeoJSON/GPKG), and configurable
debug-mode intermediate file management.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from utils.logger import logger


class StorageManager:
    """
    Centralized path manager enforcing module output ownership, export routing,
    and debug intermediate output control.
    """

    def __init__(
        self,
        storage_config_path: Path | str = Path("config/storage.yaml"),
        debug_config_path: Path | str = Path("config/debug.yaml")
    ):
        self.storage_config_path = Path(storage_config_path)
        self.debug_config_path = Path(debug_config_path)
        self.storage_cfg = self._load_yaml(self.storage_config_path).get("storage", {})
        self.debug_cfg = self._load_yaml(self.debug_config_path).get("debug", {})

        self.processed_root = Path(self.storage_cfg.get("processed_root", "data/processed")).resolve()
        self.exports_root = Path(self.storage_cfg.get("exports_root", "data/exports")).resolve()
        self.debug_root = Path(self.storage_cfg.get("debug_root", "data/debug")).resolve()

        self._ensure_base_directories()

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Safely loads YAML configuration file."""
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Error reading YAML from {path}: {e}")
                return {}
        return {}

    def _ensure_base_directories(self) -> None:
        """Ensures base root directories exist."""
        self.processed_root.mkdir(parents=True, exist_ok=True)
        self.exports_root.mkdir(parents=True, exist_ok=True)
        self.debug_root.mkdir(parents=True, exist_ok=True)

    def is_debug_enabled(self) -> bool:
        """Returns True if global debug mode is enabled."""
        return bool(self.debug_cfg.get("enabled", False))

    def should_save_intermediate(self) -> bool:
        """Returns True if intermediate stage outputs should be saved."""
        enabled = self.is_debug_enabled()
        save_int = bool(self.debug_cfg.get("save_intermediate_outputs", False))
        return enabled or save_int

    def get_processed_dir(self, module_name: str) -> Path:
        """
        Returns module-owned processed directory path (e.g. data/processed/module_1).
        Creates directory if missing.
        """
        module_dir = self.processed_root / module_name
        module_dir.mkdir(parents=True, exist_ok=True)
        return module_dir

    def get_processed_filepath(self, module_name: str, filename: str) -> Path:
        """Returns full filepath for a processed module dataset."""
        return self.get_processed_dir(module_name) / filename

    def get_export_dir(self, export_type: str) -> Path:
        """
        Returns target export directory path (e.g. data/exports/geojson, data/exports/gpkg, data/exports/reports).
        Creates directory if missing.
        """
        export_dir = self.exports_root / export_type
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir

    def get_export_filepath(self, export_type: str, filename: str) -> Path:
        """Returns full filepath for an export product."""
        return self.get_export_dir(export_type) / filename

    def get_debug_dir(self, module_name: str) -> Path:
        """
        Returns debug output directory path (e.g. data/debug/module_1).
        Creates directory if missing.
        """
        debug_dir = self.debug_root / module_name
        debug_dir.mkdir(parents=True, exist_ok=True)
        return debug_dir

    def get_debug_filepath(self, module_name: str, filename: str) -> Path:
        """Returns full filepath for a debug output."""
        return self.get_debug_dir(module_name) / filename
