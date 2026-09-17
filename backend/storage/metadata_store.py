"""
Boreas-Nexus Metadata Store Module

Provides atomic reading, writing, updating, and querying of dataset metadata entries
stored in metadata.json and validation reports in data/metadata/.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil

from utils.logger import logger


class MetadataStore:
    """
    Handles atomic JSON metadata updates to prevent corruption during pipeline execution.
    """

    def __init__(self, metadata_path: Path | str = Path("data/metadata/metadata.json")):
        self.metadata_path = Path(metadata_path).resolve()
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.metadata_path.exists():
            self._write_raw({})

    def _read_raw(self) -> Dict[str, Any]:
        """Reads the underlying metadata JSON file."""
        if not self.metadata_path.exists():
            return {}
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read metadata file at {self.metadata_path}: {e}")
            return {}

    def _write_raw(self, data: Dict[str, Any]) -> None:
        """Atomic write using temporary file replacement."""
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.metadata_path.parent,
            delete=False,
            encoding="utf-8"
        )
        try:
            json.dump(data, temp_file, indent=2, ensure_ascii=False)
            temp_file.flush()
            temp_file.close()
            shutil.move(temp_file.name, self.metadata_path)
        except Exception as e:
            logger.error(f"Failed atomic write to metadata store: {e}")
            if Path(temp_file.name).exists():
                Path(temp_file.name).unlink()
            raise

    def add_dataset_metadata(self, dataset_name: str, record: Dict[str, Any]) -> None:
        """
        Adds or updates a metadata record for a dataset.
        """
        data = self._read_raw()
        data[dataset_name] = record
        self._write_raw(data)
        logger.info(f"Recorded metadata for dataset '{dataset_name}' in metadata.json")

    def get_dataset_metadata(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves metadata record for a dataset."""
        data = self._read_raw()
        return data.get(dataset_name)

    def get_all_metadata(self) -> Dict[str, Any]:
        """Returns all stored metadata records."""
        return self._read_raw()

    def save_validation_report(
        self,
        report_data: Dict[str, Any],
        report_path: Path | str = Path("data/metadata/validation_report.json")
    ) -> Path:
        """
        Saves a structured validation report to data/metadata/validation_report.json.
        """
        path = Path(report_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved validation report to {path}")
        return path
