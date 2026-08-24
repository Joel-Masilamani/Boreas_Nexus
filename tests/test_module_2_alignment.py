"""
Critical Integration Test: Spatial Alignment Verification for Module 2

Verifies that Module 1's 44,298 grid points remain 100% spatially aligned throughout
Module 2 processing without row reordering, index shuffling, or coordinate drift.
"""

from pathlib import Path
import pytest
import geopandas as gpd
import numpy as np

from module_2_driver.stage1_feature_builder import Stage1FeatureBuilder


def test_module_2_spatial_alignment_with_module_1():
    m1_path = Path("data/processed/module_1/urban_heat_hotspot_knowledge_layer.geoparquet")
    if not m1_path.exists():
        pytest.skip("Module 1 Knowledge Layer not found. Skipping spatial alignment test.")

    gdf_m1 = gpd.read_parquet(m1_path)
    initial_count = len(gdf_m1)
    assert initial_count == 44298, f"Expected 44,298 points in Module 1, found {initial_count}"

    # Run Stage 1 Feature Engineering
    s1 = Stage1FeatureBuilder()
    s1.run(gdf_in=gdf_m1)
    gdf_m2 = s1.last_gdf

    assert len(gdf_m2) == initial_count, "Row count changed after Stage 1!"

    # 1. Verify exact 1-to-1 Point ID alignment
    assert (gdf_m1["point_id"].values == gdf_m2["point_id"].values).all(), "Point IDs are misaligned!"

    # 2. Verify exact Coordinate alignment
    np.testing.assert_array_almost_equal(gdf_m1.geometry.x.values, gdf_m2.geometry.x.values, decimal=6)
    np.testing.assert_array_almost_equal(gdf_m1.geometry.y.values, gdf_m2.geometry.y.values, decimal=6)

    # 3. Verify UTM Coordinate alignment
    if "utm_x_m" in gdf_m1.columns and "utm_x_m" in gdf_m2.columns:
        np.testing.assert_array_almost_equal(gdf_m1["utm_x_m"].values, gdf_m2["utm_x_m"].values, decimal=2)
        np.testing.assert_array_almost_equal(gdf_m1["utm_y_m"].values, gdf_m2["utm_y_m"].values, decimal=2)
