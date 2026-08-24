"""
Integration Test for Module 2: Full End-to-End Pipeline Execution
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from module_2_driver.pipeline import Module2DriverPipeline


@pytest.fixture
def synthetic_pipeline_gdf():
    """Generates synthetic input data for pipeline integration test."""
    np.random.seed(42)
    n = 150
    lats = np.linspace(13.0, 13.2, n)
    lons = np.linspace(80.1, 80.3, n)
    utm_x = 400000 + (np.arange(n) % 10) * 2000
    utm_y = 1400000 + (np.arange(n) // 10) * 2000

    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": utm_x,
        "utm_y_m": utm_y,
        "spatial_block_id": (np.floor(utm_x / 2000.0) * 100000 + np.floor(utm_y / 2000.0)).astype(int),
        "land_cover_code": np.random.choice([10, 20, 50, 80], n),
        "is_urban": [True] * n,
        "is_rural": [False] * n,
        "is_water": [False] * n,
        "ndvi": np.random.uniform(0.05, 0.65, n),
        "ndbi": np.random.uniform(-0.2, 0.45, n),
        "ndwi": np.random.uniform(-0.3, 0.1, n),
        "building_density": np.random.uniform(0.0, 1.0, n),
        "distance_to_roads_m": np.random.uniform(5.0, 150.0, n),
        "distance_to_water_m": np.random.uniform(10.0, 2000.0, n),
        "distance_to_parks_m": np.random.uniform(20.0, 3000.0, n),
        "elevation_m": np.random.uniform(2.0, 50.0, n),
        "slope_deg": np.random.uniform(0.0, 35.0, n),
        "aspect_deg": np.random.uniform(0.0, 360.0, n),
        "hotspot_id": [f"HOT_{(i // 30) + 1:04d}" if i < 90 else None for i in range(n)],
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    data["lst_day_celsius"] = 35.0 + 8.0 * data["building_density"] - 5.0 * data["ndvi"] + np.random.normal(0, 0.3, n)
    data["lst_night_celsius"] = 25.0 + 4.0 * data["building_density"] - 3.0 * data["ndvi"] + np.random.normal(0, 0.2, n)

    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def test_module_2_pipeline_end_to_end(synthetic_pipeline_gdf, tmp_path):
    pipeline = Module2DriverPipeline()
    summary = pipeline.run(gdf_in=synthetic_pipeline_gdf)

    assert summary["status"] == "SUCCESS"
    assert "stage1_metrics" in summary
    assert "stage2_metrics" in summary
    assert "stage3_metrics" in summary
    assert "stage4_metrics" in summary
    assert "stage5_metrics" in summary
    assert "stage6_metrics" in summary
    assert "stage7_manifest" in summary
