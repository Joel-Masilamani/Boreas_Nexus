"""
Unit tests for Phase 2 Preprocessing & Feature Extraction Engine.
"""

import pytest
import geopandas as gpd
from shapely.geometry import Polygon, Point
from preprocessing.grid_builder import GridBuilder
from preprocessing.feature_extractor import FeatureExtractor
from preprocessing.raster_processor import RasterProcessor
from preprocessing.vector_processor import VectorProcessor


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
