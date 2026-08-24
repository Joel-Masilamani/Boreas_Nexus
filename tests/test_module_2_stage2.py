"""
Unit Tests for Module 2 - Stage 2: Baseline Driver Modeling (Random Forest)
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from module_2_driver.stage1_feature_builder import Stage1FeatureBuilder
from module_2_driver.stage2_baseline_rf import Stage2BaselineRF


@pytest.fixture
def sample_features_gdf():
    """Generates a synthetic feature GeoDataFrame for Stage 2."""
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
    # Synthetic target with strong relationship to building density & ndvi
    data["lst_day_celsius"] = 35.0 + 8.0 * data["building_density"] - 6.0 * data["ndvi"] + np.random.normal(0, 0.5, n)
    data["lst_night_celsius"] = 25.0 + 4.0 * data["building_density"] - 3.0 * data["ndvi"] + np.random.normal(0, 0.3, n)

    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def test_stage2_spatial_block_cv_and_rf_training(sample_features_gdf):
    s2 = Stage2BaselineRF()
    metrics = s2.run(gdf_in=sample_features_gdf)

    assert metrics["status"] == "SUCCESS"
    assert "lst_day_celsius" in s2.rf_models
    assert "lst_night_celsius" in s2.rf_models

    out_gdf = s2.last_gdf
    assert "rf_pred_lst_day_celsius" in out_gdf.columns
    assert "rf_residual_lst_day_celsius" in out_gdf.columns
    assert "spatial_block_id" in out_gdf.columns

    # Check that spatial CV metrics were calculated
    cv_day = metrics["cv_metrics"]["lst_day_celsius"]
    assert "r2_mean" in cv_day
    assert cv_day["r2_mean"] > 0.0  # Synthetic data has strong signal

    # Check that feature importances are ranked
    importances = metrics["feature_importances"]["lst_day_celsius"]
    assert len(importances) == metrics["feature_count"]
    # Top features should include building_density or ndvi
    top_features = list(importances.keys())[:3]
    assert "building_density" in top_features or "ndvi" in top_features
