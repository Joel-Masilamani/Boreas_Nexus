"""
Unit Tests for Module 1 - Stage 6: Urban Heat Hotspot Knowledge Layer Export
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import json
import pytest

from module_1_thermal.stage6_knowledge_export import Stage6KnowledgeExporter
from utils.crs_utils import transform_wgs84_to_utm


def test_stage6_knowledge_export_pipeline(tmp_path):
    hotspot_path = tmp_path / "module_1_stage5_hotspots.parquet"
    lats = [13.08 + i*0.001 for i in range(50)]
    lons = [80.27 + i*0.001 for i in range(50)]
    utm_x, utm_y, _ = transform_wgs84_to_utm(lons, lats)

    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 51)),
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": utm_x,
        "utm_y_m": utm_y,
        "is_urban": [True if i < 30 else False for i in range(50)],
        "is_rural": [False if i < 30 else True for i in range(50)],
        "is_water": [False for _ in range(50)],
        "land_cover_code": [50 if i < 30 else 10 for i in range(50)],
        "lst_day_celsius": [38.0 if i < 30 else 30.0 for i in range(50)],
        "lst_night_celsius": [28.0 if i < 30 else 22.0 for i in range(50)],
        "suhii_day_celsius": [8.0 if i < 30 else 0.0 for i in range(50)],
        "suhii_night_celsius": [6.0 if i < 30 else 0.0 for i in range(50)],
        "delta_lst_diurnal": [10.0 if i < 30 else 8.0 for i in range(50)],
        "heat_persistence_index": [0.73 if i < 30 else 0.55 for i in range(50)],
        "thermal_retention_class": ["High Nocturnal Heat Retention" if i < 30 else "Moderate Retention" for i in range(50)],
        "gi_zscore_day": [2.5 if i < 30 else -0.5 for i in range(50)],
        "gi_pvalue_day": [0.01 if i < 30 else 0.6 for i in range(50)],
        "gi_zscore_night": [2.8 if i < 30 else -0.4 for i in range(50)],
        "gi_pvalue_night": [0.005 if i < 30 else 0.65 for i in range(50)],
        "day_hotspot_significance": [95 if i < 30 else None for i in range(50)],
        "night_hotspot_significance": [99 if i < 10 else (95 if i < 30 else None) for i in range(50)],
        "is_validated_hotspot": [True if i < 30 else False for i in range(50)],
        "hotspot_id": [f"HOT_{(i // 10) + 1:04d}" if i < 30 else None for i in range(50)],
        "city_temperature_percentile": [90.0 if i < 30 else 20.0 for i in range(50)],
        "temperature_rank": [40 - i if i < 30 else 10 for i in range(50)],
        "temperature_total_pixels": [50 for _ in range(50)],
        "hotspot_confidence_score": [85.0 if i < 30 else None for i in range(50)],
        "confidence_class": ["Very High" if i < 30 else None for i in range(50)],
        "hotspot_classification": ["95% Confidence Hotspot" if i < 30 else "Not Significant / Noise" for i in range(50)],
        "ndvi": [0.2 if i < 30 else 0.6 for i in range(50)],
        "ndbi": [0.4 if i < 30 else -0.1 for i in range(50)],
        "ndwi": [-0.1 for _ in range(50)],
        "building_density": [0.8 if i < 30 else 0.1 for i in range(50)],
        "distance_to_water_m": [200.0 for _ in range(50)],
        "distance_to_roads_m": [30.0 for _ in range(50)],
        "distance_to_parks_m": [800.0 for _ in range(50)],
        "elevation_m": [12.0 for _ in range(50)],
        "slope_deg": [1.5 for _ in range(50)],
        "aspect_deg": [90.0 for _ in range(50)]
    })
    dummy_df.to_parquet(hotspot_path, index=False)

    exporter = Stage6KnowledgeExporter(
        input_hotspot_path=hotspot_path,
        output_dir=tmp_path,
        metadata_dir=tmp_path
    )

    manifest = exporter.run()

    assert manifest["status"] == "SUCCESS"
    assert manifest["total_sample_points"] == 50
    assert (tmp_path / "urban_heat_hotspot_knowledge_layer.geoparquet").exists()
    assert (tmp_path / "hotspot_registry.parquet").exists()
    assert (tmp_path / "cluster_validation.json").exists()
    assert (tmp_path / "metadata.json").exists()

    # Verify schema of knowledge layer
    gdf_out = gpd.read_parquet(tmp_path / "urban_heat_hotspot_knowledge_layer.geoparquet")
    assert "surface_class" not in gdf_out.columns
    assert "lst_celsius" not in gdf_out.columns
    assert "is_hotspot_day_95" not in gdf_out.columns
    assert "day_hotspot_significance" in gdf_out.columns
    assert "night_hotspot_significance" in gdf_out.columns
    assert "sensor" in gdf_out.columns

    # Verify registry
    df_reg = pd.read_parquet(tmp_path / "hotspot_registry.parquet")
    assert "cluster_centroid_x" in df_reg.columns
    assert "cluster_centroid_y" in df_reg.columns
    assert "mean_hotspot_confidence_score" in df_reg.columns
    assert len(df_reg) == 3

    with open(tmp_path / "cluster_validation.json") as f:
        val_report = json.load(f)
        assert val_report["status"] == "PASSED"
