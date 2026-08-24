"""
Unit Tests for Module 2 - Stage 3: Advanced Driver Modeling (LightGBM)
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from module_2_driver.stage3_advanced_lgbm import Stage3AdvancedLGBM


@pytest.fixture
def sample_stage3_gdf():
    """Generates a synthetic feature GeoDataFrame for Stage 3."""
    np.random.seed(42)
    n = 200
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
        "ndvi": np.random.uniform(0.05, 0.65, n),
        "ndbi": np.random.uniform(-0.2, 0.45, n),
        "ndwi": np.random.uniform(-0.3, 0.1, n),
        "building_density": np.random.uniform(0.0, 1.0, n),
        "distance_to_roads_m": np.random.uniform(5.0, 150.0, n),
        "distance_to_water_m": np.random.uniform(10.0, 2000.0, n),
        "distance_to_parks_m": np.random.uniform(20.0, 3000.0, n),
        "elevation_m": np.random.uniform(2.0, 50.0, n),
        "slope_deg": np.random.uniform(0.0, 35.0, n),
        "aspect_sin": np.random.uniform(-1.0, 1.0, n),
        "aspect_cos": np.random.uniform(-1.0, 1.0, n),
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    # Non-linear thermal relationship
    data["lst_day_celsius"] = 34.0 + 9.0 * (data["building_density"] ** 1.5) - 7.0 * np.sqrt(np.maximum(data["ndvi"], 0.01)) + np.random.normal(0, 0.4, n)
    data["lst_night_celsius"] = 24.0 + 5.0 * data["building_density"] - 3.0 * data["ndvi"] + np.random.normal(0, 0.3, n)

    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def test_stage3_lightgbm_training_and_gate(sample_stage3_gdf):
    s3 = Stage3AdvancedLGBM()
    metrics = s3.run(gdf_in=sample_stage3_gdf)

    assert metrics["status"] == "SUCCESS"
    assert "lst_day_celsius" in s3.lgbm_models
    assert "lst_night_celsius" in s3.lgbm_models

    out_gdf = s3.last_gdf
    assert "lgbm_pred_lst_day_celsius" in out_gdf.columns
    assert "lgbm_residual_lst_day_celsius" in out_gdf.columns

    # Verify quality gate was recorded
    assert metrics["gate_statuses"]["lst_day_celsius"] in ["PASSED", "WARNING"]
    assert "r2_mean" in metrics["cv_metrics"]["lst_day_celsius"]
