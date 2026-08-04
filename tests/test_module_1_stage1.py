"""
Unit Tests for Module 1 - Stage 1: Data Acquisition & Preprocessing Alignment
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import pytest

from module_1_thermal.stage1_data_aligner import Stage1DataAligner


def test_stage1_alignment_pipeline(tmp_path):
    # Setup dummy features parquet
    features_path = tmp_path / "features.parquet"
    dummy_df = pd.DataFrame({
        "point_id": [1, 2, 3],
        "latitude": [13.0827, 13.0837, 13.0847],
        "longitude": [80.2707, 80.2717, 80.2727],
        "ndvi": [0.2, 0.5, 0.1],
        "ndbi": [0.4, 0.1, 0.6],
        "ndwi": [-0.1, -0.2, 0.3],
        "lst_celsius": [34.5, 32.0, 36.1],
        "land_cover_code": [50, 10, 50],
        "building_density": [0.8, 0.1, 0.9]
    })
    dummy_df.to_parquet(features_path, index=False)

    aligner = Stage1DataAligner(
        input_features_path=features_path,
        output_dir=tmp_path
    )

    metrics = aligner.run()

    assert metrics["status"] == "PASSED"
    assert metrics["total_samples"] == 3
    assert (tmp_path / "module_1_stage1_aligned.parquet").exists()

    df_out = pd.read_parquet(tmp_path / "module_1_stage1_aligned.parquet")
    assert "utm_x_m" in df_out.columns
    assert "utm_y_m" in df_out.columns
    assert "lst_day_celsius" in df_out.columns
    assert "lst_night_celsius" in df_out.columns
    assert df_out["lst_day_celsius"].min() >= 10.0
    assert df_out["lst_night_celsius"].min() >= 10.0
