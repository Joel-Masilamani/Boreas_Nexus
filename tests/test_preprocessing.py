"""
Unit and Integration tests for Phase 2 Preprocessing & Feature Extraction Engine.
"""

from pathlib import Path
import pytest
import geopandas as gpd
from shapely.geometry import Polygon, Point
from preprocessing.grid_builder import GridBuilder
from preprocessing.feature_extractor import FeatureExtractor
from preprocessing.raster_processor import RasterProcessor
from preprocessing.vector_processor import VectorProcessor
from preprocessing.preprocessor_pipeline import PreprocessorPipeline
from storage.storage_manager import StorageManager


@pytest.fixture
def sample_boundary():
    # Square polygon around Chennai coordinates
    poly = Polygon([(80.20, 13.00), (80.25, 13.00), (80.25, 13.05), (80.20, 13.05)])
    return gpd.GeoDataFrame([{"geometry": poly}], crs="EPSG:4326")


@pytest.fixture
def sample_grid(sample_boundary):
    builder = GridBuilder(target_crs="EPSG:4326")
    return builder.generate_grid_points(sample_boundary, resolution_meters=1000)


def test_grid_builder_generates_points(sample_boundary):
    builder = GridBuilder(target_crs="EPSG:4326")
    grid = builder.generate_grid_points(sample_boundary, resolution_meters=2000)
    assert not grid.empty
    assert "point_id" in grid.columns
    assert grid.crs.to_string().upper() == "EPSG:4326"


def test_feature_extractor_proximity(sample_grid, sample_boundary):
    extractor = FeatureExtractor(target_crs="EPSG:4326")
    water_poly = Polygon([(80.21, 13.01), (80.22, 13.01), (80.22, 13.02), (80.21, 13.02)])
    water_gdf = gpd.GeoDataFrame([{"geometry": water_poly}], crs="EPSG:4326")

    res = extractor.extract_proximity_features(sample_grid, {"water": water_gdf})
    assert "distance_to_water_m" in res.columns
    assert (res["distance_to_water_m"] >= 0).all()


def test_raster_processor_spectral_indices():
    import numpy as np
    red = np.array([0.1, 0.2, 0.3])
    nir = np.array([0.5, 0.6, 0.7])

    ndvi = RasterProcessor.compute_ndvi(red, nir)
    assert len(ndvi) == 3
    assert (ndvi >= -1.0).all() and (ndvi <= 1.0).all()


def test_vector_processor_distance_calculation(sample_grid, sample_boundary):
    dist_series = VectorProcessor.compute_distance_to_features(sample_grid, sample_boundary)
    assert len(dist_series) == len(sample_grid)
    assert (dist_series >= 0).all()


def test_feature_extractor_building_density(sample_grid):
    extractor = FeatureExtractor(target_crs="EPSG:4326")
    bldg_poly = Polygon([(80.21, 13.01), (80.215, 13.01), (80.215, 13.015), (80.21, 13.015)])
    bldg_gdf = gpd.GeoDataFrame([{"geometry": bldg_poly}], crs="EPSG:4326")

    res = extractor.extract_building_density(sample_grid, {"buildings": bldg_gdf})
    assert "building_density" in res.columns
    assert (res["building_density"] >= 0.0).all() and (res["building_density"] <= 1.0).all()


def test_preprocessor_pipeline_run(tmp_path):
    """End-to-end test for PreprocessorPipeline execution."""
    pipeline = PreprocessorPipeline(config_path="config/city.yaml")
    
    # Verify boundary loader
    boundary_gdf = pipeline.load_boundary_gdf()
    assert not boundary_gdf.empty
    assert boundary_gdf.crs is not None

    # Verify vector loader
    vector_layers = pipeline.load_raw_vector_layers()
    assert isinstance(vector_layers, dict)
    assert "roads" in vector_layers or "buildings" in vector_layers or "water" in vector_layers

    # Run pipeline
    summary = pipeline.run()
    assert summary["status"] == "SUCCESS"
    assert summary["sample_count"] > 0

    sm = StorageManager()
    features_path = sm.get_processed_filepath("feature_engineering", "features.geoparquet")
    assert features_path.exists()

    features_gdf = gpd.read_parquet(features_path)
    assert len(features_gdf) == summary["sample_count"]
    expected_cols = ["point_id", "geometry", "distance_to_water_m", "distance_to_parks_m", "distance_to_roads_m", "building_density", "ndvi", "ndbi", "ndwi", "lst_celsius", "elevation_m", "slope_deg", "aspect_deg", "land_cover_code"]
    for col in expected_cols:
        assert col in features_gdf.columns, f"Expected column {col} missing in features.geoparquet"
