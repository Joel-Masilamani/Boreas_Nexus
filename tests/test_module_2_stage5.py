"""
Unit Tests for Module 2 - Stage 5: XAI Attribution Plausibility Audit
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from module_2_driver.stage5_physics_validator import Stage5PhysicsValidator


@pytest.fixture
def sample_shap_gdf():
    """Generates synthetic SHAP output data for Stage 5 auditing."""
    np.random.seed(42)
    n = 100
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)

    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        # 80% negative for ndvi (consistent with cooling)
        "shap_day_ndvi": np.concatenate([-np.random.uniform(0.1, 2.0, 80), np.random.uniform(0.01, 0.2, 20)]),
        # 90% positive for building density (consistent with heating)
        "shap_day_building_density": np.concatenate([np.random.uniform(0.1, 2.5, 90), -np.random.uniform(0.01, 0.1, 10)]),
        "shap_day_ndbi": np.random.uniform(0.0, 1.5, n),
        "shap_day_distance_to_water_m": np.random.uniform(0.0, 1.0, n),
        "shap_day_distance_to_parks_m": np.random.uniform(0.0, 0.8, n),
        "shap_night_ndvi": -np.random.uniform(0.05, 1.0, n),
        "shap_night_building_density": np.random.uniform(0.1, 1.5, n),
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def test_stage5_directional_consistency_audit(sample_shap_gdf):
    s5 = Stage5PhysicsValidator()
    metrics = s5.run(gdf_in=sample_shap_gdf)

    assert metrics["status"] == "SUCCESS"
    assert "day" in metrics["audit_results"]
    assert "night" in metrics["audit_results"]

    day_audit = metrics["audit_results"]["day"]
    assert day_audit["status"] in ["PASSED", "WARNING"]
    assert day_audit["city_mean_consistency_pct"] >= 70.0
    assert "ndvi" in day_audit["per_driver_statistics"]
    assert day_audit["per_driver_statistics"]["ndvi"]["consistency_percentage"] >= 80.0

    out_gdf = s5.last_gdf
    assert "physics_consistency_score_day" in out_gdf.columns
    assert "physics_anomaly_flag_day" in out_gdf.columns
