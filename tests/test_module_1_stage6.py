"""
Unit Tests for Module 1 - Stage 6: Urban Heat Hotspot Knowledge Layer Export
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import json
import pytest

from module_1_thermal.stage6_knowledge_export import Stage6KnowledgeExporter
from module_1_thermal.pipeline import Module1ThermalPipeline


def test_stage6_knowledge_export_pipeline(tmp_path):
    hotspot_path = tmp_path / "module_1_stage5_hotspots.parquet"
    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 51)),
        "latitude": [13.08 + i*0.001 for i in range(50)],
        "longitude": [80.27 + i*0.001 for i in range(50)],
        "utm_x_m": [80.27*100000 + i for i in range(50)],
        "utm_y_m": [13.08*100000 + i for i in range(50)],
        "surface_class": ["Urban" if i < 30 else "Rural Baseline" for i in range(50)],
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
        "is_hotspot_day_95": [True if i < 30 else False for i in range(50)],
        "is_hotspot_day_99": [False for _ in range(50)],
        "is_hotspot_night_95": [True if i < 30 else False for i in range(50)],
        "is_hotspot_night_99": [True if i < 10 else False for i in range(50)],
        "is_validated_hotspot": [True if i < 30 else False for i in range(50)],
        "hotspot_classification": ["95% Confidence Hotspot" for _ in range(50)]
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
    assert (tmp_path / "urban_heat_hotspot_knowledge_layer.parquet").exists()
    assert (tmp_path / "urban_heat_hotspot_knowledge_layer.geojson").exists()
    assert (tmp_path / "module_1_manifest.json").exists()

    with open(tmp_path / "module_1_manifest.json") as f:
        data = json.load(f)
        assert data["module_id"] == "module_1_thermal"
        assert data["consumed_by_next_module"] == "Module 2: Urban Heat Driver Intelligence Engine"
