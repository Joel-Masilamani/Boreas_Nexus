"""
Boreas-Nexus File Manager Module

Manages directory structures, resolves dataset output file paths, prevents duplicate downloads,
computes file checksums, and manages versioning across raw and metadata storage.
"""

from pathlib import Path
from typing import Dict, Optional
import shutil

from utils.logger import logger
from utils.constants import (
    DIR_BOUNDARY,
    DIR_SATELLITE,
    DIR_VECTOR,
    DIR_WEATHER,
    DIR_ELEVATION,
    DIR_METADATA,
    RAW_SUBDIRECTORIES,
)
from utils.helpers import calculate_sha256, get_file_size_bytes


class FileManager:
    """
    Handles directory setup, path resolution, checksum verification,
    and storage organization for the Boreas-Nexus pipeline.
    """

    def __init__(self, base_raw_dir: Path | str = Path("data/raw")):
        self.base_raw_dir = Path(base_raw_dir).resolve()
        self.data_root = self.base_raw_dir.parent
        self.metadata_dir = self.data_root / DIR_METADATA
        self._ensure_directory_structure()

    def _ensure_directory_structure(self) -> None:
        """
        Creates necessary raw and metadata subdirectories if they do not exist.
        """
        self.base_raw_dir.mkdir(parents=True, exist_ok=True)
        for subdir in RAW_SUBDIRECTORIES:
            (self.base_raw_dir / subdir).mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured raw subdirectories exist at {self.base_raw_dir}")

    @property
    def boundary_dir(self) -> Path:
        return self.base_raw_dir / DIR_BOUNDARY

    @property
    def satellite_dir(self) -> Path:
        return self.base_raw_dir / DIR_SATELLITE

    @property
    def vector_dir(self) -> Path:
        return self.base_raw_dir / DIR_VECTOR

    @property
    def weather_dir(self) -> Path:
        return self.base_raw_dir / DIR_WEATHER

    @property
    def elevation_dir(self) -> Path:
        return self.base_raw_dir / DIR_ELEVATION


    def get_boundary_path(self, filename: str) -> Path:
        return self.base_raw_dir / DIR_BOUNDARY / filename

    def get_vector_path(self, filename: str) -> Path:
        return self.base_raw_dir / DIR_VECTOR / filename

    def get_weather_path(self, filename: str) -> Path:
        return self.base_raw_dir / DIR_WEATHER / filename

    def get_elevation_path(self, filename: str) -> Path:
        return self.base_raw_dir / DIR_ELEVATION / filename

    def get_satellite_path(self, provider: str, year: int, month: int, filename: str) -> Path:
        month_str = f"{month:02d}"
        sat_dir = self.base_raw_dir / DIR_SATELLITE / provider / str(year) / month_str
        sat_dir.mkdir(parents=True, exist_ok=True)
        return sat_dir / filename

    def get_metadata_path(self, filename: str = "metadata.json") -> Path:
        return self.metadata_dir / filename

    def file_exists_and_valid(self, file_path: Path, expected_min_size: int = 10) -> bool:
        """
        Checks if a file exists and exceeds a minimum byte size threshold.
        """
        if not file_path.exists():
            return False
        file_size = get_file_size_bytes(file_path)
        if file_size < expected_min_size:
            logger.warning(f"File {file_path} exists but is suspiciously small ({file_size} bytes).")
            return False
        return True

    def get_file_info(self, file_path: Path) -> Dict[str, str | int]:
        """
        Retrieves file size and checksum.
        """
        return {
            "file_size_bytes": get_file_size_bytes(file_path),
            "checksum": calculate_sha256(file_path),
            "storage_path": str(file_path.resolve())
        }
