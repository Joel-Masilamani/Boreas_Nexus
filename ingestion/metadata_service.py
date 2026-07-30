"""
Boreas-Nexus Metadata Service Module

Constructs, validates, and stores standardized metadata entries for all
ingested datasets in compliance with step 6 requirements.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from storage.file_manager import FileManager
from storage.metadata_store import MetadataStore
from utils.logger import logger
from utils.constants import REQUIRED_METADATA_KEYS


class MetadataService:
    """
    Service responsible for building metadata records and persisting them into MetadataStore.
    """

    def __init__(self, file_manager: FileManager, metadata_store: MetadataStore):
        self.file_manager = file_manager
        self.metadata_store = metadata_store

    def create_and_store_metadata(
        self,
        dataset_name: str,
        source: str,
        provider: str,
        storage_path: Path,
        projection: str = "EPSG:4326",
        bounding_box: Optional[Dict[str, float]] = None,
        resolution: str = "N/A",
        license_info: str = "Open Data",
        version: str = "1.0",
        status: str = "SUCCESS"
    ) -> Dict[str, Any]:
        """
        Gathers dataset file attributes (checksum, size) and records standard metadata.

        Returns:
            Dict containing the recorded metadata entry.
        """
        file_info = self.file_manager.get_file_info(storage_path)

        metadata_record = {
            "dataset_name": dataset_name,
            "source": source,
            "provider": provider,
            "download_time": datetime.now(timezone.utc).isoformat(),
            "projection": projection,
            "bounding_box": bounding_box or {"minx": 0.0, "miny": 0.0, "maxx": 0.0, "maxy": 0.0},
            "resolution": resolution,
            "file_size_bytes": file_info["file_size_bytes"],
            "license": license_info,
            "version": version,
            "checksum": file_info["checksum"],
            "storage_path": str(storage_path.resolve()),
            "status": status,
        }

        # Verify all required keys are present
        for key in REQUIRED_METADATA_KEYS:
            if key not in metadata_record:
                logger.warning(f"Metadata field '{key}' missing for dataset '{dataset_name}'. Setting default.")
                metadata_record[key] = "N/A"

        self.metadata_store.add_dataset_metadata(dataset_name, metadata_record)
        return metadata_record
