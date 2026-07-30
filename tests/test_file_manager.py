"""
Unit tests for storage file manager and metadata store.
"""

from pathlib import Path
from storage.file_manager import FileManager
from storage.metadata_store import MetadataStore
from utils.helpers import calculate_sha256


def test_file_manager_directory_creation(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    fm = FileManager(base_raw_dir=raw_dir)

    assert (raw_dir / "boundary").exists()
    assert (raw_dir / "satellite").exists()
    assert (raw_dir / "vector").exists()
    assert (raw_dir / "weather").exists()
    assert (raw_dir / "elevation").exists()


def test_checksum_calculation(tmp_path: Path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Boreas Nexus Geospatial Pipeline")

    checksum = calculate_sha256(test_file)
    assert len(checksum) == 64  # SHA256 length hex


def test_metadata_store(tmp_path: Path):
    meta_file = tmp_path / "metadata.json"
    store = MetadataStore(metadata_path=meta_file)

    sample_meta = {
        "dataset_name": "boundary",
        "status": "SUCCESS"
    }
    store.add_dataset_metadata("boundary", sample_meta)

    retrieved = store.get_dataset_metadata("boundary")
    assert retrieved is not None
    assert retrieved["status"] == "SUCCESS"
