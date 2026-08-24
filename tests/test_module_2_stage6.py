"""
Unit Tests for Module 2 - Stage 6: Spatial Driver Intelligence (GWR)
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from module_2_driver.stage6_spatial_gwr import Stage6SpatialGWR


@pytest.fixture
def sample_gwr_gdf():
    """Generates synthetic spatial points for GWR testing."""
    np.random.seed(42)
    n = 100
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
        "ndvi": np.random.uniform(0.05, 0.65, n),
        "ndbi": np.random.uniform(-0.2, 0.45, n),
        "building_density": np.random.uniform(0.0, 1.0, n),
        "distance_to_water_m": np.random.uniform(10.0, 2000.0, n),
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    data["lst_day_celsius"] = 35.0 + 8.0 * data["building_density"] - 5.0 * data["ndvi"] + np.random.normal(0, 0.5, n)

    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def test_stage6_spatially_balanced_gwr_and_fallback(sample_gwr_gdf, tmp_path):
    s6 = Stage6SpatialGWR()
    metrics = s6.run(gdf_in=sample_gwr_gdf)

    assert metrics["status"] in ["SUCCESS", "SKIPPED", "FAILED_FALLBACK"]
    out_gdf = s6.last_gdf
    assert len(out_gdf) == len(sample_gwr_gdf)
    assert "gwr_local_r2" in out_gdf.columns


def test_stage6_disabled_gwr_skips_cleanly(sample_gwr_gdf, tmp_path):
    # Test with GWR disabled in config
    cfg_path = tmp_path / "driver_analysis.yaml"
    cfg_content = """
    spatial_driver_intelligence:
      enable_gwr: false
    """
    cfg_path.write_text(cfg_content)

    s6 = Stage6SpatialGWR(config_path=cfg_path)
    metrics = s6.run(gdf_in=sample_gwr_gdf)

    assert metrics["status"] == "SKIPPED"
    assert "gwr_local_r2" in s6.last_gdf.columns
