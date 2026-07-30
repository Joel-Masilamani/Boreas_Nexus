"""
Unit tests for configuration loader and validator.
"""

from pathlib import Path
import pytest
from utils.config_loader import ConfigLoader, Config


def test_load_valid_config(tmp_path: Path):
    yaml_content = """
city:
  name: "Chennai"
  state: "Tamil Nadu"
  country: "India"
  output_directory: "data/raw"
  crs: "EPSG:4326"

ingestion:
  vector:
    layers:
      - roads
      - buildings
"""
    config_file = tmp_path / "city.yaml"
    config_file.write_text(yaml_content)

    cfg = ConfigLoader.load_config(config_file)
    assert isinstance(cfg, Config)
    assert cfg.city.name == "Chennai"
    assert cfg.city.query_name == "Chennai, Tamil Nadu, India"
    assert cfg.city.crs == "EPSG:4326"
    assert "roads" in cfg.ingestion.vector.layers


def test_missing_city_name_raises_error(tmp_path: Path):
    yaml_content = """
city:
  state: "Tamil Nadu"
"""
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(yaml_content)

    with pytest.raises(ValueError, match="'city.name' is required"):
        ConfigLoader.load_config(config_file)
