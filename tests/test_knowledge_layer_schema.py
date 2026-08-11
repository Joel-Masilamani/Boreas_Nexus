"""
Unit and Regression Tests for Authoritative Knowledge Layer Schema & Validation
"""

from pathlib import Path
import json
import geopandas as gpd
import pandas as pd
import numpy as np
import pytest

from module_1_thermal.pipeline import Module1ThermalPipeline
from module_1_thermal.stage6_knowledge_export import AUTHORITATIVE_COLUMNS, FORBIDDEN_COLUMNS
from storage.storage_manager import StorageManager
from utils.crs_utils import validate_projected_utm_coords


def test_authoritative_knowledge_layer_schema_and_integrity():
    """Runs complete pipeline and rigorously validates final output schema against requirements."""
    pipeline = Module1ThermalPipeline()
    summary = pipeline.run()
    assert summary["status"] == "SUCCESS"

    sm = StorageManager()
    processed_dir = sm.get_processed_dir("module_1")

    kl_path = processed_dir / "urban_heat_hotspot_knowledge_layer.geoparquet"
    reg_path = processed_dir / "hotspot_registry.parquet"
    val_path = processed_dir / "cluster_validation.json"
    meta_path = processed_dir / "metadata.json"

    assert kl_path.exists()
    assert reg_path.exists()
    assert val_path.exists()
    assert meta_path.exists()

    # 1. Check Knowledge Layer GeoParquet
    gdf = gpd.read_parquet(kl_path)
    assert len(gdf) > 0

    # Verify column presence
    for col in AUTHORITATIVE_COLUMNS:
        assert col in gdf.columns, f"Authoritative column missing: {col}"

    # Verify forbidden columns absent
    for col in FORBIDDEN_COLUMNS:
        assert col not in gdf.columns, f"Forbidden column present: {col}"

    # Verify exact column set
    expected_set = set(AUTHORITATIVE_COLUMNS)
    actual_set = set(gdf.columns)
    assert actual_set == expected_set, f"Mismatch in column set: {actual_set - expected_set}"

    # 2. Check UTM projection
    is_utm_valid, utm_msg = validate_projected_utm_coords(gdf["utm_x_m"].values, gdf["utm_y_m"].values)
    assert is_utm_valid, f"UTM validation failed: {utm_msg}"

    # 3. Check Water Exclusion in Percentiles
    water_pcts = gdf[gdf["is_water"]]["city_temperature_percentile"].dropna()
    assert len(water_pcts) == 0, "Water pixels must have null temperature percentiles"

    # 4. Check Hotspot Registry
    df_reg = pd.read_parquet(reg_path)
    expected_reg_cols = [
        "hotspot_id", "cluster_area_m2", "cluster_perimeter_m",
        "cluster_size_pixels", "cluster_centroid_x", "cluster_centroid_y", "cluster_bbox",
        "mean_lst", "peak_lst", "mean_suhii", "mean_heat_persistence",
        "mean_hotspot_confidence_score"
    ]
    for col in expected_reg_cols:
        assert col in df_reg.columns, f"Registry column missing: {col}"

    assert len(df_reg) == len(df_reg["hotspot_id"].unique()), "Cluster IDs must be unique in registry"
    if len(df_reg) > 0:
        assert (df_reg["cluster_area_m2"] > 0).all()
        assert (df_reg["cluster_perimeter_m"] > 0).all()

    # 5. Check cluster_validation.json
    with open(val_path, "r", encoding="utf-8") as f:
        val_data = json.load(f)
    assert val_data["status"] == "PASSED"
    for check_name, passed in val_data["checks"].items():
        assert passed is True, f"Validation check failed: {check_name}"
