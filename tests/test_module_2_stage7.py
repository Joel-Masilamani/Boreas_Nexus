"""
Unit Tests for Module 2 - Stage 7: Urban Heat Driver Knowledge Layer Export
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from module_2_driver.stage7_driver_knowledge_export import Stage7DriverKnowledgeExporter


@pytest.fixture
def sample_complete_gdf():
    """Generates a complete synthetic Module 2 dataset."""
    np.random.seed(42)
    n = 60
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)

    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": 400000 + np.arange(n) * 100,
        "utm_y_m": 1400000 + np.arange(n) * 100,
        "land_cover_code": [50] * n,
        "ndvi": [0.3] * n,
        "ndbi": [0.2] * n,
        "ndwi": [-0.1] * n,
        "building_density": [0.6] * n,
        "distance_to_roads_m": [25.0] * n,
        "distance_to_water_m": [300.0] * n,
        "distance_to_parks_m": [500.0] * n,
        "elevation_m": [15.0] * n,
        "slope_deg": [2.0] * n,
        "aspect_sin": [0.0] * n,
        "aspect_cos": [1.0] * n,
        "lst_day_celsius": [38.5] * n,
        "lst_night_celsius": [26.0] * n,
        "rf_pred_lst_day_celsius": [38.2] * n,
        "lgbm_pred_lst_day_celsius": [38.4] * n,
        "shap_day_ndvi": [-0.8] * n,
        "shap_day_building_density": [1.2] * n,
        "primary_driver_day": ["building_density"] * n,
        "secondary_driver_day": ["ndvi"] * n,
        "tertiary_driver_day": ["ndbi"] * n,
        "physics_consistency_score_day": [90.0] * n,
        "hotspot_id": [f"HOT_{(i // 20) + 1:04d}" if i < 40 else None for i in range(n)],
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def test_stage7_export_and_registry_generation(sample_complete_gdf, tmp_path):
    exporter = Stage7DriverKnowledgeExporter(output_dir=tmp_path, metadata_dir=tmp_path)
    manifest = exporter.run(gdf_in=sample_complete_gdf)

    assert manifest["status"] == "SUCCESS"
    assert manifest["total_sample_points"] == 60
    assert manifest["hotspot_clusters_registered"] == 2  # HOT_0001, HOT_0002

    # Check exported files exist
    assert (tmp_path / "urban_heat_driver_knowledge_layer.geoparquet").exists()
    assert (tmp_path / "driver_attribution_registry.parquet").exists()
    assert (tmp_path / "driver_physics_audit.json").exists()

    # Verify Registry content
    reg_df = pd.read_parquet(tmp_path / "driver_attribution_registry.parquet")
    assert len(reg_df) == 2
    assert "dominant_cluster_driver_day" in reg_df.columns
    assert "mean_shap_day_building_density" in reg_df.columns
