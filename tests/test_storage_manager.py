"""
Unit tests for centralized StorageManager.
"""

from pathlib import Path
import pytest
from storage.storage_manager import StorageManager


def test_storage_manager_paths(tmp_path):
    """Tests directory resolution and creation in StorageManager."""
    storage_cfg = tmp_path / "storage.yaml"
    debug_cfg = tmp_path / "debug.yaml"

    storage_cfg.write_text(f"""
storage:
  processed_root: "{tmp_path / 'processed'}"
  exports_root: "{tmp_path / 'exports'}"
  debug_root: "{tmp_path / 'debug'}"
  primary_spatial_format: "geoparquet"
""")

    debug_cfg.write_text("""
debug:
  enabled: false
  save_intermediate_outputs: false
""")

    sm = StorageManager(storage_config_path=storage_cfg, debug_config_path=debug_cfg)

    # Processed directories
    fe_dir = sm.get_processed_dir("feature_engineering")
    m1_dir = sm.get_processed_dir("module_1")
    assert fe_dir.exists() and fe_dir.name == "feature_engineering"
    assert m1_dir.exists() and m1_dir.name == "module_1"

    # Export directories
    geojson_dir = sm.get_export_dir("geojson")
    gpkg_dir = sm.get_export_dir("gpkg")
    reports_dir = sm.get_export_dir("reports")
    assert geojson_dir.exists() and geojson_dir.name == "geojson"
    assert gpkg_dir.exists() and gpkg_dir.name == "gpkg"
    assert reports_dir.exists() and reports_dir.name == "reports"

    # Debug directory & flag
    debug_m1 = sm.get_debug_dir("module_1")
    assert debug_m1.exists() and debug_m1.name == "module_1"
    assert not sm.should_save_intermediate()


def test_storage_manager_debug_toggle(tmp_path):
    """Tests debug flag enabling intermediate output saving."""
    storage_cfg = tmp_path / "storage.yaml"
    debug_cfg = tmp_path / "debug.yaml"

    storage_cfg.write_text(f"""
storage:
  processed_root: "{tmp_path / 'processed'}"
  exports_root: "{tmp_path / 'exports'}"
  debug_root: "{tmp_path / 'debug'}"
""")

    debug_cfg.write_text("""
debug:
  enabled: true
  save_intermediate_outputs: true
""")

    sm = StorageManager(storage_config_path=storage_cfg, debug_config_path=debug_cfg)
    assert sm.should_save_intermediate()
