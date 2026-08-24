"""
Unit Tests for Module 2 - Stage 4: Explainable AI Driver Attribution (SHAP)
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from module_2_driver.stage3_advanced_lgbm import Stage3AdvancedLGBM
from module_2_driver.stage4_shap_explainer import Stage4ShapExplainer


@pytest.fixture
def fitted_stage3_data():
    """Generates synthetic data and fits LightGBM model for SHAP testing."""
    np.random.seed(42)
    n = 100
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)
    utm_x = 400000 + np.arange(n) * 100
    utm_y = 1400000 + np.arange(n) * 100

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
    data["lst_day_celsius"] = 35.0 + 8.0 * data["building_density"] - 6.0 * data["ndvi"] + np.random.normal(0, 0.2, n)
    data["lst_night_celsius"] = 25.0 + 4.0 * data["building_density"] - 3.0 * data["ndvi"] + np.random.normal(0, 0.2, n)

    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    s3 = Stage3AdvancedLGBM()
    s3.run(gdf_in=gdf)
    return s3.last_gdf, s3.lgbm_models


def test_stage4_shap_attribution_and_additive_reconstruction(fitted_stage3_data):
    gdf, lgbm_models = fitted_stage3_data
    s4 = Stage4ShapExplainer()
    metrics = s4.run(gdf_in=gdf, lgbm_models=lgbm_models)

    assert metrics["status"] == "SUCCESS"
    assert "lst_day_celsius" in metrics["reconstruction_errors"]

    # Verify SHAP Additive Reconstruction Check
    day_err = metrics["reconstruction_errors"]["lst_day_celsius"]
    assert day_err["validation_passed"] is True
    assert day_err["max_absolute_error"] < 1e-3

    # Check that dominant drivers are assigned
    out_gdf = s4.last_gdf
    assert "primary_driver_day" in out_gdf.columns
    assert "secondary_driver_day" in out_gdf.columns
    assert "shap_day_building_density" in out_gdf.columns
    assert "shap_day_ndvi" in out_gdf.columns
