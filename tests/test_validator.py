"""
Unit tests for data validator module.
"""

from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point
from utils.config_loader import ConfigLoader
from storage.metadata_store import MetadataStore
from preprocessing.validator import DatasetValidator


def test_validator_vector_check(tmp_path: Path):
    # Create dummy config and metadata store
    config_file = tmp_path / "city.yaml"
    config_file.write_text("""
city:
  name: "Chennai"
  state: "TN"
  country: "India"
  output_directory: "data/raw"
  crs: "EPSG:4326"
ingestion: {}
""")
    config = ConfigLoader.load_config(config_file)
    store = MetadataStore(tmp_path / "metadata.json")
    validator = DatasetValidator(config, store)

    # Create dummy geojson
    gdf = gpd.GeoDataFrame(geometry=[Point(80.27, 13.08)], crs="EPSG:4326")
    vec_file = tmp_path / "test.geojson"
    gdf.to_file(vec_file, driver="GeoJSON")

    res = validator.validate_vector_file(vec_file)
    assert res["status"] == "PASSED"
    assert res["feature_count"] == 1
