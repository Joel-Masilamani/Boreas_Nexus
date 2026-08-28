"""
Consolidated Tests for Module 1: Urban Heat Island & Hotspot Delineation Pipeline
"""

from pathlib import Path
import json
import pytest
import numpy as np
import pandas as pd
import geopandas as gpd

from module_1_thermal.stage1_data_aligner import Stage1DataAligner
from module_1_thermal.stage2_urban_delineation import Stage2UrbanDelineator
from module_1_thermal.stage3_suhii_calculator import Stage3SUHIICalculator
from module_1_thermal.stage4_nighttime_thermal import Stage4NighttimeThermal
from module_1_thermal.stage5_hotspot_validator import Stage5HotspotValidator
from module_1_thermal.stage6_knowledge_export import Stage6KnowledgeExporter
from module_1_thermal.city_temperature_percentile import CityTemperaturePercentileCalculator
from module_1_thermal.hotspot_confidence_scorer import HotspotConfidenceScorer
from module_1_thermal.hotspot_cluster_generator import HotspotClusterGenerator
from utils.crs_utils import transform_wgs84_to_utm
from storage.storage_manager import StorageManager


def test_stage1_alignment_pipeline(tmp_path):
    features_path = tmp_path / "features.geoparquet"
    lats = [13.08 + i*0.001 for i in range(10)]
    lons = [80.27 + i*0.001 for i in range(10)]
    utm_x, utm_y, _ = transform_wgs84_to_utm(lons, lats)

    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 11)),
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": utm_x,
        "utm_y_m": utm_y,
        "land_cover_code": [50] * 10,
        "lst_day_celsius": [35.5] * 10,
        "lst_night_celsius": [25.0] * 10,
        "ndvi": [0.2] * 10,
        "ndbi": [0.3] * 10,
        "ndwi": [-0.1] * 10,
        "building_density": [0.8] * 10
    })
    dummy_df.to_parquet(features_path, index=False)

    aligner = Stage1DataAligner(
        input_features_path=features_path,
        output_dir=tmp_path
    )
    metrics = aligner.run()

    assert metrics["status"] == "PASSED"
    assert metrics["total_samples"] == 10
    assert (tmp_path / "module_1_stage1_aligned.parquet").exists()


def test_stage2_delineation_pipeline(tmp_path):
    aligned_path = tmp_path / "module_1_stage1_aligned.parquet"
    n_pts = 25
    lats = [13.08 + i*0.001 for i in range(n_pts)]
    lons = [80.27 + i*0.001 for i in range(n_pts)]
    utm_x, utm_y, _ = transform_wgs84_to_utm(lons, lats)

    dummy_df = pd.DataFrame({
        "point_id": list(range(1, n_pts + 1)),
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": utm_x,
        "utm_y_m": utm_y,
        "land_cover_code": [50]*10 + [10]*10 + [80]*5,
        "building_density": [0.8]*10 + [0.1]*10 + [0.0]*5,
        "ndvi": [0.1]*10 + [0.6]*10 + [0.0]*5,
        "lst_day_celsius": [38.0]*10 + [30.0]*10 + [28.0]*5,
        "lst_night_celsius": [28.0]*10 + [22.0]*10 + [20.0]*5
    })
    dummy_df.to_parquet(aligned_path, index=False)

    delineator = Stage2UrbanDelineator(
        input_aligned_path=aligned_path,
        output_dir=tmp_path
    )
    metrics = delineator.run()

    assert metrics["status"] == "PASSED"
    assert metrics["urban_pixel_count"] == 10
    assert metrics["rural_pixel_count"] == 10
    assert metrics["water_pixel_count"] == 5


def test_stage3_suhii_pipeline(tmp_path):
    delineated_path = tmp_path / "module_1_stage2_delineated.parquet"
    lats = [13.08 + i*0.001 for i in range(20)]
    lons = [80.27 + i*0.001 for i in range(20)]
    utm_x, utm_y, _ = transform_wgs84_to_utm(lons, lats)

    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 21)),
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": utm_x,
        "utm_y_m": utm_y,
        "is_urban": [True]*10 + [False]*10,
        "is_rural": [False]*10 + [True]*10,
        "is_water": [False]*20,
        "lst_day_celsius": [38.0]*10 + [30.0]*10,
        "lst_night_celsius": [28.0]*10 + [22.0]*10
    })
    dummy_df.to_parquet(delineated_path, index=False)

    calculator = Stage3SUHIICalculator(
        input_delineated_path=delineated_path,
        output_dir=tmp_path
    )
    metrics = calculator.run()

    assert metrics["status"] == "PASSED"
    assert metrics["rural_mean_day_celsius"] == 30.0
    assert metrics["city_baseline_urban_suhii_day_celsius"] == 8.0


def test_stage4_nighttime_pipeline(tmp_path):
    suhii_path = tmp_path / "module_1_stage3_suhii.parquet"
    lats = [13.08 + i*0.001 for i in range(20)]
    lons = [80.27 + i*0.001 for i in range(20)]
    utm_x, utm_y, _ = transform_wgs84_to_utm(lons, lats)

    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 21)),
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": utm_x,
        "utm_y_m": utm_y,
        "is_urban": [True]*10 + [False]*10,
        "is_rural": [False]*10 + [True]*10,
        "lst_day_celsius": [38.0]*10 + [30.0]*10,
        "suhii_day_celsius": [8.0]*10 + [0.0]*10,
        "lst_night_celsius": [28.0]*10 + [22.0]*10
    })
    dummy_df.to_parquet(suhii_path, index=False)

    analyzer = Stage4NighttimeThermal(
        input_suhii_path=suhii_path,
        output_dir=tmp_path
    )
    metrics = analyzer.run()

    assert metrics["status"] == "PASSED"
    assert metrics["urban_mean_hpi"] > metrics["rural_mean_hpi"]


def test_stage5_hotspot_pipeline(tmp_path):
    nighttime_path = tmp_path / "module_1_stage4_nighttime.parquet"
    xs = [80.20 + (i % 10)*0.01 for i in range(100)]
    ys = [13.00 + (i // 10)*0.01 for i in range(100)]
    utm_x, utm_y, _ = transform_wgs84_to_utm(xs, ys)

    suhii_day, suhii_night = [], []
    for i in range(100):
        r, c = i // 10, i % 10
        if 3 <= r <= 6 and 3 <= c <= 6:
            suhii_day.append(8.0)
            suhii_night.append(6.0)
        else:
            suhii_day.append(0.5)
            suhii_night.append(0.2)

    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 101)),
        "longitude": xs,
        "latitude": ys,
        "utm_x_m": utm_x,
        "utm_y_m": utm_y,
        "lst_day_celsius": [34.0 + s for s in suhii_day],
        "lst_night_celsius": [22.0 + s for s in suhii_night],
        "suhii_day_celsius": suhii_day,
        "suhii_night_celsius": suhii_night,
        "is_urban": [True]*100,
        "is_rural": [False]*100
    })
    dummy_df.to_parquet(nighttime_path, index=False)

    validator = Stage5HotspotValidator(
        input_nighttime_path=nighttime_path,
        output_dir=tmp_path,
        knn_k=4
    )
    metrics = validator.run()

    assert metrics["status"] == "PASSED"
    assert metrics["total_validated_hotspot_pixels"] >= 10


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
        "is_water": [False]*50,
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
        "temperature_total_pixels": [50]*50,
        "hotspot_confidence_score": [85.0 if i < 30 else None for i in range(50)],
        "confidence_class": ["Very High" if i < 30 else None for i in range(50)],
        "hotspot_classification": ["95% Confidence Hotspot" if i < 30 else "Not Significant / Noise" for i in range(50)],
        "ndvi": [0.2 if i < 30 else 0.6 for i in range(50)],
        "ndbi": [0.4 if i < 30 else -0.1 for i in range(50)],
        "ndwi": [-0.1]*50,
        "building_density": [0.8 if i < 30 else 0.1 for i in range(50)],
        "distance_to_water_m": [200.0]*50,
        "distance_to_roads_m": [30.0]*50,
        "distance_to_parks_m": [800.0]*50,
        "elevation_m": [12.0]*50,
        "slope_deg": [1.5]*50,
        "aspect_deg": [90.0]*50
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


def test_module_1_extensions(sample_m1_gdf):
    perc_calc = CityTemperaturePercentileCalculator()
    gdf_p = perc_calc.compute_percentiles(sample_m1_gdf)
    assert "city_temperature_percentile" in gdf_p.columns

    scorer = HotspotConfidenceScorer()
    gdf_c = scorer.compute_confidence_scores(gdf_p)
    assert "hotspot_confidence_score" in gdf_c.columns


def test_authoritative_knowledge_layer_schema():
    sm = StorageManager()
    p = sm.get_processed_filepath("module_1", "urban_heat_hotspot_knowledge_layer.geoparquet")
    if p.exists():
        gdf = gpd.read_parquet(p)
        assert len(gdf) == 44298
        required = ["point_id", "lst_day_celsius", "lst_night_celsius", "suhii_day_celsius", "gi_zscore_day"]
        for col in required:
            assert col in gdf.columns
