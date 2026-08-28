"""
Consolidated Tests for Core Config, Storage, Ingestion, and Feature Preprocessing
"""

from pathlib import Path
import pytest
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point

from utils.config_loader import ConfigLoader
from storage.file_manager import FileManager
from storage.storage_manager import StorageManager
from ingestion.stac_fetcher import get_stac_catalog
from preprocessing.grid_builder import GridBuilder
from preprocessing.feature_extractor import FeatureExtractor
from preprocessing.raster_processor import RasterProcessor
from preprocessing.vector_processor import VectorProcessor
from preprocessing.preprocessor_pipeline import PreprocessorPipeline


# =====================================================================
# 1. Config Tests
# =====================================================================
def test_load_valid_config():
    cfg = ConfigLoader.load_config("config/city.yaml")
    assert cfg.city.name.lower() == "chennai"
    assert cfg.preprocessing.grid_resolution_meters == 100
    assert cfg.preprocessing.target_crs == "EPSG:4326"


def test_missing_city_name_raises_error(tmp_path):
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("city:\n  country: India\n", encoding="utf-8")
    with pytest.raises((ValueError, KeyError, TypeError)):
        ConfigLoader.load_config(invalid_yaml)


# =====================================================================
# 2. File & Storage Manager Tests
# =====================================================================
def test_file_manager_directory_creation(tmp_path):
    fm = FileManager(base_raw_dir=tmp_path / "raw")
    assert fm.base_raw_dir.exists()
    assert fm.metadata_dir.exists()


def test_checksum_calculation(tmp_path):
    fm = FileManager(base_raw_dir=tmp_path / "raw")
    sample_file = tmp_path / "test.txt"
    sample_file.write_text("boreas-nexus-checksum-test", encoding="utf-8")
    info = fm.get_file_info(sample_file)
    assert len(info["checksum"]) == 64


def test_storage_manager_paths():
    sm = StorageManager()
    p = sm.get_processed_filepath("module_1", "test.geoparquet")
    assert "data" in str(p)
    assert "processed" in str(p)
    assert p.name == "test.geoparquet"


def test_storage_manager_debug_toggle(tmp_path):
    debug_yaml = tmp_path / "debug.yaml"
    debug_yaml.write_text("debug:\n  enabled: true\n", encoding="utf-8")
    sm = StorageManager(debug_config_path=debug_yaml)
    assert sm.is_debug_enabled() is True


# =====================================================================
# 3. STAC Ingestion Client Tests
# =====================================================================
def test_stac_catalog_client():
    client = get_stac_catalog()
    assert client is not None


# =====================================================================
# 4. Preprocessing & Feature Extraction Tests
# =====================================================================
def test_grid_builder_generates_points(sample_boundary):
    builder = GridBuilder(target_crs="EPSG:4326")
    grid = builder.generate_grid_points(sample_boundary, resolution_meters=2000)
    assert not grid.empty
    assert "point_id" in grid.columns
    assert grid.crs.to_string().upper() == "EPSG:4326"


def test_feature_extractor_proximity(sample_boundary):
    builder = GridBuilder(target_crs="EPSG:4326")
    sample_grid = builder.generate_grid_points(sample_boundary, resolution_meters=1000)
    extractor = FeatureExtractor(target_crs="EPSG:4326")
    water_poly = Polygon([(80.21, 13.01), (80.22, 13.01), (80.22, 13.02), (80.21, 13.02)])
    water_gdf = gpd.GeoDataFrame([{"geometry": water_poly}], crs="EPSG:4326")

    res = extractor.extract_proximity_features(sample_grid, {"water": water_gdf})
    assert "distance_to_water_m" in res.columns
    assert (res["distance_to_water_m"] >= 0).all()


def test_raster_processor_spectral_indices():
    red = np.array([0.1, 0.2, 0.3])
    nir = np.array([0.5, 0.6, 0.7])
    ndvi = RasterProcessor.compute_ndvi(red, nir)
    assert len(ndvi) == 3
    assert (ndvi >= -1.0).all() and (ndvi <= 1.0).all()


def test_vector_processor_distance_calculation(sample_boundary):
    builder = GridBuilder(target_crs="EPSG:4326")
    sample_grid = builder.generate_grid_points(sample_boundary, resolution_meters=1000)
    dist_series = VectorProcessor.compute_distance_to_features(sample_grid, sample_boundary)
    assert len(dist_series) == len(sample_grid)
    assert (dist_series >= 0).all()


def test_feature_extractor_building_density(sample_boundary):
    builder = GridBuilder(target_crs="EPSG:4326")
    sample_grid = builder.generate_grid_points(sample_boundary, resolution_meters=1000)
    extractor = FeatureExtractor(target_crs="EPSG:4326")
    bldg_poly = Polygon([(80.21, 13.01), (80.215, 13.01), (80.215, 13.015), (80.21, 13.015)])
    bldg_gdf = gpd.GeoDataFrame([{"geometry": bldg_poly}], crs="EPSG:4326")

    res = extractor.extract_building_density(sample_grid, {"buildings": bldg_gdf})
    assert "building_density" in res.columns
    assert (res["building_density"] >= 0.0).all() and (res["building_density"] <= 1.0).all()


def test_preprocessor_pipeline_run():
    pipeline = PreprocessorPipeline(config_path="config/city.yaml")
    boundary_gdf = pipeline.load_boundary_gdf()
    assert not boundary_gdf.empty
    assert boundary_gdf.crs is not None

    vector_layers = pipeline.load_raw_vector_layers()
    assert isinstance(vector_layers, dict)
    assert len(vector_layers) > 0


def test_vector_processor_validate_geometries(sample_boundary):
    repaired_gdf = VectorProcessor.validate_and_repair_geometries(sample_boundary)
    assert not repaired_gdf.empty
    assert (repaired_gdf.is_valid).all()
