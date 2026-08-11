"""
Unit and Integration Tests for Module 1 Extensions:
1. Hotspot Cluster Generator (CCA)
2. City Temperature Percentile Calculator
3. Hotspot Confidence Scorer (0-100 Weighted Model)
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import pytest

from module_1_thermal.hotspot_cluster_generator import HotspotClusterGenerator
from module_1_thermal.city_temperature_percentile import CityTemperaturePercentileCalculator
from module_1_thermal.hotspot_confidence_scorer import HotspotConfidenceScorer
from module_1_thermal.pipeline import Module1ThermalPipeline
from storage.storage_manager import StorageManager


def test_cluster_generator(tmp_path):
    """Tests Connected Component Analysis and cluster polygon generation."""
    data = {
        "point_id": [1, 2, 3, 4],
        "latitude": [13.0827, 13.0827, 13.0900, 13.0900],
        "longitude": [80.2707, 80.2717, 80.2800, 80.2810],
        "utm_x_m": [420800.0, 420900.0, 421800.0, 421900.0],
        "utm_y_m": [1446500.0, 1446500.0, 1447300.0, 1447300.0],
        "is_validated_hotspot": [True, True, False, True],
        "lst_day_celsius": [38.5, 39.0, 31.0, 37.5],
        "suhii_day_celsius": [6.5, 7.0, -1.0, 5.5],
        "heat_persistence_index": [0.72, 0.74, 0.50, 0.68]
    }
    df = pd.DataFrame(data)
    parquet_path = tmp_path / "stage5_hotspots.parquet"
    df.to_parquet(parquet_path, index=False)

    generator = HotspotClusterGenerator(
        input_hotspot_path=parquet_path,
        output_dir=tmp_path
    )

    metrics = generator.run()
    assert metrics["status"] == "SUCCESS"
    assert metrics["total_clusters_found"] == 2

    df_labeled = pd.read_parquet(tmp_path / "module_1_stage5_labeled.parquet")
    assert "hotspot_id" in df_labeled.columns
    assert df_labeled["hotspot_id"].notnull().sum() == 3

    assert (tmp_path / "hotspot_clusters.geojson").exists()
    assert (tmp_path / "hotspot_clusters.gpkg").exists()


def test_temperature_percentile(tmp_path):
    """Tests relative temperature percentile calculation across land pixels."""
    data = {
        "point_id": list(range(1, 101)),
        "latitude": [13.08 + i*0.0001 for i in range(100)],
        "longitude": [80.27 + i*0.0001 for i in range(100)],
        "lst_day_celsius": [30.0 + i*0.1 for i in range(100)],
        "is_water": [True if i < 10 else False for i in range(100)],
        "is_urban": [True for _ in range(100)]
    }
    df = pd.DataFrame(data)
    parquet_path = tmp_path / "stage5_labeled.parquet"
    df.to_parquet(parquet_path, index=False)

    calc = CityTemperaturePercentileCalculator(
        input_path=parquet_path,
        output_dir=tmp_path
    )

    metrics = calc.run()
    assert metrics["status"] == "SUCCESS"
    assert metrics["evaluated_land_pixels"] == 90

    df_pct = pd.read_parquet(tmp_path / "module_1_stage5_pct.parquet")
    assert "city_temperature_percentile" in df_pct.columns
    assert "temperature_rank" in df_pct.columns
    assert "temperature_total_pixels" in df_pct.columns

    land_pcts = df_pct[df_pct["is_water"] == False]["city_temperature_percentile"]
    assert land_pcts.min() == 0.0
    assert land_pcts.max() == 100.0

    water_pcts = df_pct[df_pct["is_water"] == True]["city_temperature_percentile"]
    assert water_pcts.isnull().all()


def test_confidence_scorer(tmp_path):
    """Tests weighted hotspot confidence scoring model."""
    data = {
        "point_id": [1, 2, 3],
        "latitude": [13.08, 13.09, 13.10],
        "longitude": [80.27, 80.28, 80.29],
        "gi_zscore_day": [3.5, 2.5, 0.1],
        "gi_zscore_night": [2.8, 2.2, 0.0],
        "suhii_day_celsius": [8.0, 5.0, 0.0],
        "suhii_night_celsius": [5.0, 3.0, 0.0],
        "heat_persistence_index": [0.75, 0.65, 0.50],
        "city_temperature_percentile": [95.0, 80.0, 30.0],
        "hotspot_id": ["HOT_0001", "HOT_0001", None]
    }
    df = pd.DataFrame(data)
    parquet_path = tmp_path / "stage5_pct.parquet"
    df.to_parquet(parquet_path, index=False)

    scorer = HotspotConfidenceScorer(
        input_path=parquet_path,
        output_dir=tmp_path
    )

    metrics = scorer.run()
    assert metrics["status"] == "SUCCESS"

    df_scored = pd.read_parquet(tmp_path / "module_1_stage5_scored.parquet")
    assert "hotspot_confidence_score" in df_scored.columns
    assert "confidence_class" in df_scored.columns

    scores = df_scored["hotspot_confidence_score"].dropna()
    assert (scores >= 0.0).all() and (scores <= 100.0).all()
    assert len(scores) == 2
    assert df_scored.loc[2, "hotspot_confidence_score"] is None or np.isnan(df_scored.loc[2, "hotspot_confidence_score"])


def test_full_extended_pipeline(tmp_path):
    """End-to-end integration test of extended Module 1 pipeline."""
    pipeline = Module1ThermalPipeline()
    summary = pipeline.run()

    assert summary["status"] == "SUCCESS"

    storage_manager = StorageManager()
    processed_dir = storage_manager.get_processed_dir("module_1")

    # Verify primary internal GeoParquet output in module_1 owned directory
    assert (processed_dir / "urban_heat_hotspot_knowledge_layer.geoparquet").exists()

    # Verify normalized Hotspot Registry Parquet
    assert (processed_dir / "hotspot_registry.parquet").exists()

    # Verify validation reports and metadata
    assert (processed_dir / "cluster_validation.json").exists()
    assert (processed_dir / "metadata.json").exists()
