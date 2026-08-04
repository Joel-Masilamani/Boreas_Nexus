"""
Unit and integration tests for Module 1 extensions:
- Hotspot Cluster Generator
- City Temperature Percentile Calculator
- Hotspot Confidence Scorer
- GeoParquet Knowledge Layer & Hotspot Registry Exporter
"""

from pathlib import Path
import json
import pandas as pd
import geopandas as gpd
import numpy as np
import pytest

from module_1_thermal.hotspot_cluster_generator import HotspotClusterGenerator
from module_1_thermal.city_temperature_percentile import CityTemperaturePercentileCalculator
from module_1_thermal.hotspot_confidence_scorer import HotspotConfidenceScorer
from module_1_thermal.stage6_knowledge_export import Stage6KnowledgeExporter
from module_1_thermal.pipeline import Module1ThermalPipeline


def test_cluster_generator(tmp_path):
    """Tests connected component clustering and cluster polygon generation."""
    data = {
        "latitude": [13.0, 13.0, 13.0, 13.1, 13.1],
        "longitude": [80.0, 80.001, 80.002, 80.05, 80.051],
        "utm_x_m": [1000.0, 1100.0, 1200.0, 5000.0, 5100.0],
        "utm_y_m": [2000.0, 2000.0, 2000.0, 6000.0, 6000.0],
        "is_validated_hotspot": [True, True, True, True, True],
        "lst_day_celsius": [35.0, 36.0, 37.0, 40.0, 41.0],
        "suhii_day_celsius": [3.0, 4.0, 5.0, 8.0, 9.0],
        "heat_persistence_index": [0.7, 0.75, 0.8, 0.85, 0.9]
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
    assert metrics["total_clusters_found"] >= 1

    labeled_parquet = tmp_path / "module_1_stage5_labeled.parquet"
    assert labeled_parquet.exists()

    df_labeled = pd.read_parquet(labeled_parquet)
    assert "hotspot_id" in df_labeled.columns
    assert df_labeled["hotspot_id"].notnull().all()


def test_temperature_percentile(tmp_path):
    """Tests city temperature percentile ranking."""
    data = {
        "latitude": [13.0, 13.01, 13.02, 13.03],
        "longitude": [80.0, 80.01, 80.02, 80.03],
        "lst_day_celsius": [30.0, 35.0, 40.0, 45.0],
        "is_water": [False, False, False, True]
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
    assert metrics["evaluated_land_pixels"] == 3

    df_pct = pd.read_parquet(tmp_path / "module_1_stage5_pct.parquet")
    assert "city_temperature_percentile" in df_pct.columns
    assert "temperature_rank" in df_pct.columns
    assert "temperature_total_pixels" in df_pct.columns

    # Water pixel should have NaN percentile
    assert np.isnan(df_pct.loc[3, "city_temperature_percentile"])
    # Coldest land pixel (30.0) should have lowest percentile ~0.0
    assert df_pct.loc[0, "city_temperature_percentile"] == 0.0
    # Hottest land pixel (40.0) should have highest percentile 100.0
    assert df_pct.loc[2, "city_temperature_percentile"] == 100.0


def test_confidence_scorer(tmp_path):
    """Tests deterministic confidence scoring model."""
    data = {
        "latitude": [13.0, 13.01],
        "longitude": [80.0, 80.01],
        "gi_zscore_day": [2.5, 3.5],
        "gi_zscore_night": [2.0, 3.0],
        "suhii_day_celsius": [4.0, 8.0],
        "suhii_night_celsius": [3.0, 6.0],
        "heat_persistence_index": [0.6, 0.9],
        "city_temperature_percentile": [50.0, 99.0]
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

    scores = df_scored["hotspot_confidence_score"]
    assert (scores >= 0.0).all() and (scores <= 100.0).all()


def test_full_extended_pipeline(tmp_path):
    """End-to-end integration test of extended Module 1 pipeline."""
    pipeline = Module1ThermalPipeline()
    summary = pipeline.run()

    assert summary["status"] == "SUCCESS"

    processed_dir = Path("data/processed")
    metadata_dir = Path("data/metadata")

    # Verify primary internal GeoParquet outputs
    assert (processed_dir / "urban_heat_hotspot_knowledge_layer.geoparquet").exists()
    assert (processed_dir / "urban_heat_hotspots.geoparquet").exists()

    # Verify normalized Hotspot Registry Parquet
    assert (processed_dir / "hotspot_registry.parquet").exists()

    # Verify validation reports
    assert (metadata_dir / "cluster_validation.json").exists()
    assert (metadata_dir / "metadata.json").exists()

    # Verify cluster validation checks passed
    with open(metadata_dir / "cluster_validation.json") as f:
        val_report = json.load(f)
    assert val_report["status"] == "PASSED"
    for check_name, passed in val_report["checks"].items():
        assert passed, f"Validation check failed: {check_name}"

    # Verify optional derived export products
    assert (processed_dir / "urban_heat_hotspots.geojson").exists()
    assert (processed_dir / "urban_heat_hotspots.gpkg").exists()
    assert (processed_dir / "hotspot_clusters.geojson").exists()
    assert (processed_dir / "hotspot_clusters.gpkg").exists()
