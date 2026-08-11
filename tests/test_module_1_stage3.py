"""
Unit Tests for Module 1 - Stage 3: Surface Urban Heat Island (SUHII) Computation
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import pytest

from module_1_thermal.stage3_suhii_calculator import Stage3SUHIICalculator


def test_stage3_suhii_pipeline(tmp_path):
    delineated_path = tmp_path / "module_1_stage2_delineated.parquet"
    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 101)),
        "latitude": [13.08 + i*0.001 for i in range(100)],
        "longitude": [80.27 + i*0.001 for i in range(100)],
        "is_urban": [True if i < 60 else False for i in range(100)],
        "is_rural": [False if i < 60 else True for i in range(100)],
        "is_water": [False for _ in range(100)],
        "lst_day_celsius": [40.0 if i < 60 else 32.0 for i in range(100)],
        "lst_night_celsius": [28.0 if i < 60 else 22.0 for i in range(100)]
    })
    dummy_df.to_parquet(delineated_path, index=False)

    calculator = Stage3SUHIICalculator(
        input_delineated_path=delineated_path,
        output_dir=tmp_path
    )

    metrics = calculator.run()

    assert metrics["status"] == "PASSED"
    assert metrics["rural_mean_day_celsius"] == 32.0
    assert metrics["rural_mean_night_celsius"] == 22.0
    assert metrics["city_baseline_urban_suhii_day_celsius"] == 8.0
    assert metrics["city_baseline_urban_suhii_night_celsius"] == 6.0

    df_out = pd.read_parquet(tmp_path / "module_1_stage3_suhii.parquet")
    assert "suhii_day_celsius" in df_out.columns
    assert "suhii_night_celsius" in df_out.columns
    assert df_out[df_out["is_urban"]]["suhii_day_celsius"].mean() == 8.0
