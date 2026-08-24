"""
Unit Tests for Module 2 - Stage 1: Multi-Source Feature Engineering
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from module_2_driver.stage1_feature_builder import Stage1FeatureBuilder


@pytest.fixture
def sample_module1_gdf():
    """Generates a synthetic Module 1 Knowledge Layer GeoDataFrame."""
    np.random.seed(42)
    n = 100
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)
    aspects = np.array([0.0, 90.0, 180.0, 270.0] * 25)

    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": 400000 + np.arange(n) * 100,
        "utm_y_m": 1400000 + np.arange(n) * 100,
        "land_cover_code": np.random.choice([10, 20, 50, 80], n),
        "is_urban": [True] * n,
        "is_rural": [False] * n,
        "is_water": [False] * n,
        "lst_day_celsius": np.random.uniform(32.0, 44.0, n),
        "lst_night_celsius": np.random.uniform(22.0, 30.0, n),
        "suhii_day_celsius": np.random.uniform(0.0, 8.0, n),
        "suhii_night_celsius": np.random.uniform(0.0, 6.0, n),
        "ndvi": np.random.uniform(0.05, 0.65, n),
        "ndbi": np.random.uniform(-0.2, 0.45, n),
        "ndwi": np.random.uniform(-0.3, 0.1, n),
        "building_density": np.random.uniform(0.0, 1.0, n),
        "distance_to_roads_m": np.random.uniform(5.0, 150.0, n),
        "distance_to_water_m": np.random.uniform(10.0, 2000.0, n),
        "distance_to_parks_m": np.random.uniform(20.0, 3000.0, n),
        "elevation_m": np.random.uniform(2.0, 50.0, n),
        "slope_deg": np.random.uniform(0.0, 35.0, n),
        "aspect_deg": aspects,
        "hotspot_id": [f"HOT_{(i // 10) + 1:04d}" if i < 30 else None for i in range(n)],
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def test_stage1_circular_aspect_transformation(sample_module1_gdf):
    builder = Stage1FeatureBuilder()
    metrics = builder.run(gdf_in=sample_module1_gdf)

    assert metrics["status"] == "SUCCESS"
    assert metrics["total_points"] == 100
    assert "aspect_sin" in builder.last_gdf.columns
    assert "aspect_cos" in builder.last_gdf.columns

    # Test trigonometric properties
    # 0 deg: sin = 0, cos = 1
    assert np.isclose(builder.last_gdf.loc[0, "aspect_sin"], 0.0, atol=1e-5)
    assert np.isclose(builder.last_gdf.loc[0, "aspect_cos"], 1.0, atol=1e-5)

    # 90 deg: sin = 1, cos = 0
    assert np.isclose(builder.last_gdf.loc[1, "aspect_sin"], 1.0, atol=1e-5)
    assert np.isclose(builder.last_gdf.loc[1, "aspect_cos"], 0.0, atol=1e-5)

    # 180 deg: sin = 0, cos = -1
    assert np.isclose(builder.last_gdf.loc[2, "aspect_sin"], 0.0, atol=1e-5)
    assert np.isclose(builder.last_gdf.loc[2, "aspect_cos"], -1.0, atol=1e-5)

    # 270 deg: sin = -1, cos = 0
    assert np.isclose(builder.last_gdf.loc[3, "aspect_sin"], -1.0, atol=1e-5)
    assert np.isclose(builder.last_gdf.loc[3, "aspect_cos"], 0.0, atol=1e-5)


def test_stage1_spatial_alignment_and_point_count(sample_module1_gdf):
    builder = Stage1FeatureBuilder()
    builder.run(gdf_in=sample_module1_gdf)

    out_gdf = builder.last_gdf
    assert len(out_gdf) == len(sample_module1_gdf)
    assert list(out_gdf["point_id"]) == list(sample_module1_gdf["point_id"])
    assert (out_gdf.geometry.x == sample_module1_gdf.geometry.x).all()
    assert (out_gdf.geometry.y == sample_module1_gdf.geometry.y).all()


def test_stage1_missing_required_column_raises():
    invalid_df = pd.DataFrame({"point_id": [1, 2], "ndvi": [0.2, 0.3]})
    invalid_gdf = gpd.GeoDataFrame(invalid_df, geometry=[Point(0, 0), Point(1, 1)], crs="EPSG:4326")

    builder = Stage1FeatureBuilder()
    with pytest.raises(ValueError, match="aspect_deg"):
        builder.run(gdf_in=invalid_gdf)
