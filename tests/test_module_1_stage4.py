"""
Unit Tests for Module 1 - Stage 4: Night-Time Thermal Behaviour Analysis
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import pytest

from module_1_thermal.stage4_nighttime_thermal import Stage4NighttimeThermal


def test_stage4_nighttime_pipeline(tmp_path):
    suhii_path = tmp_path / "module_1_stage3_suhii.parquet"
    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 101)),
        "latitude": [13.08 + i*0.001 for i in range(100)],
        "longitude": [80.27 + i*0.001 for i in range(100)],
        "is_urban": [True if i < 60 else False for i in range(100)],
        "is_rural": [False if i < 60 else True for i in range(100)],
        "lst_day_celsius": [40.0 if i < 60 else 35.0 for i in range(100)],
        "lst_night_celsius": [28.0 if i < 60 else 20.0 for i in range(100)],
        "suhii_day_celsius": [8.0 if i < 60 else 0.0 for i in range(100)],
        "suhii_night_celsius": [6.0 if i < 60 else 0.0 for i in range(100)]
    })
    dummy_df.to_parquet(suhii_path, index=False)

    analyzer = Stage4NighttimeThermal(
        input_suhii_path=suhii_path,
        output_dir=tmp_path
    )

    metrics = analyzer.run()

    assert metrics["status"] == "PASSED"
    assert metrics["urban_mean_hpi"] > metrics["rural_mean_hpi"]
    assert metrics["urban_mean_diurnal_range_celsius"] < metrics["rural_mean_diurnal_range_celsius"]

    df_out = pd.read_parquet(tmp_path / "module_1_stage4_nighttime.parquet")
    assert "delta_lst_diurnal" in df_out.columns
    assert "heat_persistence_index" in df_out.columns
    assert "thermal_retention_class" in df_out.columns
