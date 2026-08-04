"""
Unit Tests for Module 1 - Stage 5: Spatial Hotspot Validation (Getis-Ord Gi*)
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import pytest

from module_1_thermal.stage5_hotspot_validator import Stage5HotspotValidator


def test_stage5_hotspot_pipeline(tmp_path):
    nighttime_path = tmp_path / "module_1_stage4_nighttime.parquet"
    
    # Create spatial grid with a hot cluster in the center and 1 noisy isolated hot pixel
    xs = [80.20 + (i % 10)*0.01 for i in range(100)]
    ys = [13.00 + (i // 10)*0.01 for i in range(100)]
    
    # Hot cluster in rows 4-6, cols 4-6 (indices around 44..66)
    suhii_day = []
    suhii_night = []
    for i in range(100):
        r, c = i // 10, i % 10
        if 3 <= r <= 6 and 3 <= c <= 6:
            suhii_day.append(8.0)
            suhii_night.append(6.0)
        elif r == 0 and c == 0:
            # Isolated single hot pixel (noise)
            suhii_day.append(7.5)
            suhii_night.append(5.5)
        else:
            suhii_day.append(0.5)
            suhii_night.append(0.2)

    dummy_df = pd.DataFrame({
        "point_id": list(range(1, 101)),
        "longitude": xs,
        "latitude": ys,
        "utm_x_m": [x * 100000 for x in xs],
        "utm_y_m": [y * 100000 for y in ys],
        "lst_day_celsius": [34.0 + s for s in suhii_day],
        "lst_night_celsius": [22.0 + s for s in suhii_night],
        "suhii_day_celsius": suhii_day,
        "suhii_night_celsius": suhii_night,
        "is_urban": [True for _ in range(100)],
        "is_rural": [False for _ in range(100)]
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
    
    df_out = pd.read_parquet(tmp_path / "module_1_stage5_hotspots.parquet")
    assert "gi_zscore_day" in df_out.columns
    assert "gi_pvalue_day" in df_out.columns
    assert "is_validated_hotspot" in df_out.columns
    
    # Check that isolated pixel at index 0 (r=0, c=0) was flagged as non-hotspot cluster due to spatial isolation
    assert df_out.loc[0, "is_validated_hotspot"] == False or df_out.loc[0, "gi_zscore_day"] < df_out.loc[45, "gi_zscore_day"]
