"""
Unit Tests for Module 1 - Stage 2: Urban-Non-Urban Delineation
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import pytest

from module_1_thermal.stage2_urban_delineation import Stage2UrbanDelineator


def test_stage2_delineation_pipeline(tmp_path):
    aligned_path = tmp_path / "module_1_stage1_aligned.parquet"
    # Create test data with built-up (50), trees (10), water (80)
    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 201)),
        "latitude": [13.08 + i*0.001 for i in range(200)],
        "longitude": [80.27 + i*0.001 for i in range(200)],
        "lst_day_celsius": [38.0 if i < 100 else 30.0 for i in range(200)],
        "lst_night_celsius": [28.0 if i < 100 else 22.0 for i in range(200)],
        "ndvi": [0.15 if i < 100 else 0.60 for i in range(200)],
        "ndbi": [0.45 if i < 100 else -0.20 for i in range(200)],
        "ndwi": [-0.10 for _ in range(190)] + [0.40 for _ in range(10)],
        "land_cover_code": [50 if i < 100 else (80 if i >= 190 else 10) for i in range(200)],
        "building_density": [0.70 if i < 100 else 0.0 for i in range(200)]
    })
    dummy_df.to_parquet(aligned_path, index=False)

    delineator = Stage2UrbanDelineator(
        input_aligned_path=aligned_path,
        output_dir=tmp_path
    )

    metrics = delineator.run()

    assert metrics["status"] == "PASSED"
    assert metrics["urban_pixel_count"] == 100
    assert metrics["rural_pixel_count"] == 90
    assert metrics["water_pixel_count"] == 10
    assert metrics["urban_mean_day_lst_celsius"] > metrics["rural_mean_day_lst_celsius"]

    df_out = pd.read_parquet(tmp_path / "module_1_stage2_delineated.parquet")
    assert "is_urban" in df_out.columns
    assert "is_rural" in df_out.columns
    assert "is_water" in df_out.columns
    assert "surface_class" in df_out.columns
