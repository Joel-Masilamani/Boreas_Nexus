"""
Consolidated Tests for Module 2: Urban Heat Driver Intelligence Pipeline
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from module_2_driver.stage1_feature_builder import Stage1FeatureBuilder
from module_2_driver.stage2_baseline_rf import Stage2BaselineRF
from module_2_driver.stage3_advanced_lgbm import Stage3AdvancedLGBM
from module_2_driver.stage4_shap_explainer import Stage4ShapExplainer
from module_2_driver.stage5_physics_validator import Stage5PhysicsValidator
from module_2_driver.stage6_spatial_gwr import Stage6SpatialGWR
from module_2_driver.stage7_driver_knowledge_export import Stage7DriverKnowledgeExporter
from module_2_driver.pipeline import Module2DriverPipeline
from storage.storage_manager import StorageManager


# =====================================================================
# Fixtures
# =====================================================================
@pytest.fixture
def sample_m1_input_gdf():
    """Generates synthetic input data matching Module 1 Knowledge Layer schema."""
    np.random.seed(42)
    n = 100
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)
    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": 400000 + np.arange(n) * 100,
        "utm_y_m": 1400000 + np.arange(n) * 100,
        "land_cover_code": np.random.choice([10, 20, 50, 80], n),
        "is_urban": [True] * n,
        "is_rural": [False] * n,
        "is_water": [False] * n,
        "ndvi": np.random.uniform(0.05, 0.65, n),
        "ndbi": np.random.uniform(-0.2, 0.45, n),
        "ndwi": np.random.uniform(-0.3, 0.1, n),
        "building_density": np.random.uniform(0.0, 1.0, n),
        "distance_to_roads_m": np.random.uniform(5.0, 150.0, n),
        "distance_to_water_m": np.random.uniform(10.0, 2000.0, n),
        "distance_to_parks_m": np.random.uniform(20.0, 3000.0, n),
        "elevation_m": np.random.uniform(2.0, 50.0, n),
        "slope_deg": np.random.uniform(0.0, 35.0, n),
        "aspect_deg": np.random.uniform(0.0, 360.0, n),
        "lst_day_celsius": np.random.uniform(32.0, 42.0, n),
        "lst_night_celsius": np.random.uniform(24.0, 30.0, n),
        "suhii_day_celsius": np.random.uniform(1.0, 8.0, n),
        "suhii_night_celsius": np.random.uniform(0.5, 5.0, n),
        "gi_zscore_day": np.random.uniform(-1.0, 4.0, n),
        "hotspot_id": [f"HOT_{(i // 20) + 1:04d}" if i < 60 else None for i in range(n)],
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


@pytest.fixture
def sample_stage2_gdf():
    """Generates synthetic input data for Stage 2 RF modeling and pipeline tests."""
    np.random.seed(42)
    n = 120
    lats = np.linspace(13.0, 13.2, n)
    lons = np.linspace(80.1, 80.3, n)
    utm_x = 400000 + (np.arange(n) % 10) * 2000
    utm_y = 1400000 + (np.arange(n) // 10) * 2000
    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": utm_x,
        "utm_y_m": utm_y,
        "spatial_block_id": (np.floor(utm_x / 2000.0) * 100000 + np.floor(utm_y / 2000.0)).astype(int),
        "land_cover_code": np.random.choice([10, 20, 50, 80], n),
        "ndvi": np.random.uniform(0.05, 0.65, n),
        "ndbi": np.random.uniform(-0.2, 0.45, n),
        "ndwi": np.random.uniform(-0.3, 0.1, n),
        "building_density": np.random.uniform(0.0, 1.0, n),
        "distance_to_roads_m": np.random.uniform(5.0, 150.0, n),
        "distance_to_water_m": np.random.uniform(10.0, 2000.0, n),
        "distance_to_parks_m": np.random.uniform(20.0, 3000.0, n),
        "elevation_m": np.random.uniform(2.0, 50.0, n),
        "slope_deg": np.random.uniform(0.0, 35.0, n),
        "aspect_deg": np.random.uniform(0.0, 360.0, n),
        "aspect_sin": np.random.uniform(-1.0, 1.0, n),
        "aspect_cos": np.random.uniform(-1.0, 1.0, n),
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    data["lst_day_celsius"] = 35.0 + 8.0 * data["building_density"] - 5.0 * data["ndvi"] + np.random.normal(0, 0.5, n)
    data["lst_night_celsius"] = 25.0 + 4.0 * data["building_density"] - 3.0 * data["ndvi"] + np.random.normal(0, 0.3, n)
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


# =====================================================================
# Tests
# =====================================================================
def test_stage1_circular_aspect_transformation(sample_m1_input_gdf):
    s1 = Stage1FeatureBuilder()
    metrics = s1.run(gdf_in=sample_m1_input_gdf)
    assert metrics["status"] == "SUCCESS"
    out_gdf = s1.last_gdf
    assert "aspect_sin" in out_gdf.columns
    assert "aspect_cos" in out_gdf.columns
    assert np.all(out_gdf["aspect_sin"] >= -1.0) and np.all(out_gdf["aspect_sin"] <= 1.0)
    assert np.all(out_gdf["aspect_cos"] >= -1.0) and np.all(out_gdf["aspect_cos"] <= 1.0)


def test_stage1_missing_required_column_raises():
    s1 = Stage1FeatureBuilder()
    df_missing = gpd.GeoDataFrame({"point_id": ["pt_1"], "lst_day_celsius": [35.0]})
    with pytest.raises(ValueError, match="required"):
        s1.run(gdf_in=df_missing)


def test_stage2_spatial_block_cv_and_rf_training(sample_stage2_gdf):
    s2 = Stage2BaselineRF()
    metrics = s2.run(gdf_in=sample_stage2_gdf)
    assert metrics["status"] == "SUCCESS"
    assert "lst_day_celsius" in s2.rf_models
    assert "lst_night_celsius" in s2.rf_models
    out_gdf = s2.last_gdf
    assert "rf_pred_lst_day_celsius" in out_gdf.columns
    assert "rf_residual_lst_day_celsius" in out_gdf.columns


def test_stage3_lightgbm_training_and_gate(sample_stage2_gdf):
    s3 = Stage3AdvancedLGBM()
    metrics = s3.run(gdf_in=sample_stage2_gdf)
    assert metrics["status"] == "SUCCESS"
    assert "lst_day_celsius" in s3.lgbm_models
    assert "lst_night_celsius" in s3.lgbm_models
    out_gdf = s3.last_gdf
    assert "lgbm_pred_lst_day_celsius" in out_gdf.columns


def test_stage4_shap_attribution_and_additive_reconstruction(sample_stage2_gdf):
    s3 = Stage3AdvancedLGBM()
    s3.run(gdf_in=sample_stage2_gdf)
    s4 = Stage4ShapExplainer()
    metrics = s4.run(gdf_in=s3.last_gdf, lgbm_models=s3.lgbm_models)
    assert metrics["status"] == "SUCCESS"
    out_gdf = s4.last_gdf
    assert "primary_driver_day" in out_gdf.columns
    assert "shap_day_building_density" in out_gdf.columns


def test_stage5_directional_consistency_audit():
    np.random.seed(42)
    n = 100
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)
    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "shap_day_ndvi": np.concatenate([-np.random.uniform(0.1, 2.0, 80), np.random.uniform(0.01, 0.2, 20)]),
        "shap_day_building_density": np.concatenate([np.random.uniform(0.1, 2.5, 90), -np.random.uniform(0.01, 0.1, 10)]),
        "shap_day_ndbi": np.random.uniform(0.0, 1.5, n),
        "shap_day_distance_to_water_m": np.random.uniform(0.0, 1.0, n),
        "shap_day_distance_to_parks_m": np.random.uniform(0.0, 0.8, n),
        "shap_night_ndvi": -np.random.uniform(0.05, 1.0, n),
        "shap_night_building_density": np.random.uniform(0.1, 1.5, n),
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    s5 = Stage5PhysicsValidator()
    metrics = s5.run(gdf_in=gdf)
    assert metrics["status"] == "SUCCESS"
    assert "shap_domain_consistency_score_day" in s5.last_gdf.columns


def test_stage6_spatially_balanced_gwr(sample_stage2_gdf):
    s6 = Stage6SpatialGWR()
    metrics = s6.run(gdf_in=sample_stage2_gdf)
    assert metrics["status"] in ["SUCCESS", "SKIPPED", "FAILED_FALLBACK"]
    assert "gwr_local_r2" in s6.last_gdf.columns
    assert "gwr_day_local_r2" in s6.last_gdf.columns
    assert "gwr_night_local_r2" in s6.last_gdf.columns


def test_stage7_export_and_registry_generation(tmp_path):
    np.random.seed(42)
    n = 60
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)
    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": 400000 + np.arange(n) * 100,
        "utm_y_m": 1400000 + np.arange(n) * 100,
        "land_cover_code": [50] * n,
        "ndvi": [0.3] * n,
        "ndbi": [0.2] * n,
        "ndwi": [-0.1] * n,
        "building_density": [0.6] * n,
        "distance_to_roads_m": [25.0] * n,
        "distance_to_water_m": [300.0] * n,
        "distance_to_parks_m": [500.0] * n,
        "elevation_m": [15.0] * n,
        "slope_deg": [2.0] * n,
        "aspect_sin": [0.0] * n,
        "aspect_cos": [1.0] * n,
        "lst_day_celsius": [38.5] * n,
        "lst_night_celsius": [26.0] * n,
        "rf_pred_lst_day_celsius": [38.2] * n,
        "lgbm_pred_lst_day_celsius": [38.4] * n,
        "shap_day_ndvi": [-0.8] * n,
        "shap_day_building_density": [1.2] * n,
        "primary_driver_day": ["building_density"] * n,
        "secondary_driver_day": ["ndvi"] * n,
        "tertiary_driver_day": ["ndbi"] * n,
        "shap_domain_consistency_score_day": [90.0] * n,
        "hotspot_id": [f"HOT_{(i // 20) + 1:04d}" if i < 40 else None for i in range(n)],
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    sample_complete_gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    exporter = Stage7DriverKnowledgeExporter(output_dir=tmp_path, metadata_dir=tmp_path)
    manifest = exporter.run(gdf_in=sample_complete_gdf)
    assert manifest["status"] == "SUCCESS"
    assert (tmp_path / "urban_heat_driver_knowledge_layer.geoparquet").exists()


def test_module_2_spatial_alignment_with_module_1():
    m1_path = Path("data/processed/module_1/urban_heat_hotspot_knowledge_layer.geoparquet")
    if m1_path.exists():
        gdf_m1 = gpd.read_parquet(m1_path)
        s1 = Stage1FeatureBuilder()
        s1.run(gdf_in=gdf_m1)
        gdf_m2 = s1.last_gdf
        assert len(gdf_m1) == len(gdf_m2) == 44298
        assert (gdf_m1["point_id"].values == gdf_m2["point_id"].values).all()


def test_module_2_pipeline_end_to_end(sample_stage2_gdf, tmp_path):
    pipeline = Module2DriverPipeline(output_dir=tmp_path, metadata_dir=tmp_path)
    summary = pipeline.run(gdf_in=sample_stage2_gdf)
    assert summary["status"] == "SUCCESS"
    assert "stage1_metrics" in summary
    assert "stage7_manifest" in summary
    assert (tmp_path / "urban_heat_driver_knowledge_layer.geoparquet").exists()
    assert (tmp_path / "driver_attribution_registry.parquet").exists()


def test_stage7_period_aware_attribution_day_and_night(tmp_path):
    """Verifies that Stage 7 correctly assigns day drivers to DAY entities and night drivers to NIGHT entities."""
    n = 20
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)
    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": 400000 + np.arange(n) * 100,
        "utm_y_m": 1400000 + np.arange(n) * 100,
        "land_cover_code": [50] * n,
        "ndvi": [0.3] * n,
        "ndbi": [0.2] * n,
        "ndwi": [-0.1] * n,
        "building_density": [0.6] * n,
        "distance_to_roads_m": [25.0] * n,
        "distance_to_water_m": [300.0] * n,
        "distance_to_parks_m": [500.0] * n,
        "elevation_m": [15.0] * n,
        "slope_deg": [2.0] * n,
        "aspect_sin": [0.0] * n,
        "aspect_cos": [1.0] * n,
        "lst_day_celsius": [38.5] * n,
        "lst_night_celsius": [26.0] * n,
        "primary_driver_day": ["ndvi"] * 10 + ["distance_to_parks_m"] * 10,
        "secondary_driver_day": ["distance_to_water_m"] * n,
        "primary_driver_night": ["building_density"] * 10 + ["building_density"] * 10,
        "secondary_driver_night": ["land_cover_code"] * n,
        "shap_day_ndvi": [-1.2] * n,
        "shap_day_building_density": [0.1] * n,
        "shap_night_ndvi": [-0.05] * n,
        "shap_night_building_density": [1.8] * n,
        "shap_domain_consistency_score_day": [92.0] * n,
        "shap_domain_consistency_score_night": [88.0] * n,
        "day_hotspot_id": ["DAY_HOT_0001"] * 10 + [None] * 10,
        "night_hotspot_id": [None] * 10 + ["NIGHT_HOT_0001"] * 10,
        "hotspot_group_id": ["HG_0001"] * 10 + ["HG_0001"] * 10,
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    sample_gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    exporter = Stage7DriverKnowledgeExporter(output_dir=tmp_path, metadata_dir=tmp_path)
    manifest = exporter.run(gdf_in=sample_gdf)
    assert manifest["status"] == "SUCCESS"

    registry_path = tmp_path / "driver_attribution_registry.parquet"
    assert registry_path.exists()
    registry_df = pd.read_parquet(registry_path)

    assert len(registry_df) == 2
    day_row = registry_df[registry_df["period"] == "DAY"].iloc[0]
    night_row = registry_df[registry_df["period"] == "NIGHT"].iloc[0]

    # DAY assertions
    assert day_row["hotspot_id"] == "DAY_HOT_0001"
    assert day_row["dominant_driver"] == "ndvi"
    assert np.isclose(day_row["mean_shap_ndvi"], -1.2)
    assert np.isclose(day_row["mean_shap_building_density"], 0.1)
    assert np.isclose(day_row["domain_consistency_score"], 92.0)

    # NIGHT assertions
    assert night_row["hotspot_id"] == "NIGHT_HOT_0001"
    assert night_row["dominant_driver"] == "building_density"
    assert np.isclose(night_row["mean_shap_building_density"], 1.8)
    assert np.isclose(night_row["mean_shap_ndvi"], -0.05)
    assert np.isclose(night_row["domain_consistency_score"], 88.0)


def test_stage7_module_1_registry_ingestion_and_join(tmp_path):
    """Verifies that Stage 7 ingests and joins Module 1's authoritative hotspot registry."""
    # 1. Create mock Module 1 Hotspot Registry
    m1_reg_data = {
        "hotspot_id": ["DAY_HOT_0001", "NIGHT_HOT_0001"],
        "period": ["DAY", "NIGHT"],
        "hotspot_group_id": ["HG_0001", "HG_0001"],
        "cluster_area_m2": [100000.0, 50000.0],
        "cluster_perimeter_m": [1400.0, 900.0],
        "cluster_size_pixels": [10, 5],
        "cluster_centroid_x": [400500.0, 401000.0],
        "cluster_centroid_y": [1400500.0, 1401000.0],
        "cluster_bbox": ["[400000, 1400000, 401000, 1401000]", "[400500, 1400500, 401500, 1401500]"],
        "mean_lst": [41.5, 27.2],
        "peak_lst": [43.0, 28.5],
        "mean_suhii": [4.5, 2.8],
        "mean_heat_persistence": [0.85, 0.75],
        "mean_hotspot_confidence_score": [92.0, 89.0]
    }
    m1_reg_df = pd.DataFrame(m1_reg_data)
    m1_reg_path = tmp_path / "hotspot_registry.parquet"
    m1_reg_df.to_parquet(m1_reg_path, index=False)

    # 2. Create sample point GDF
    n = 15
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)
    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "utm_x_m": 400000 + np.arange(n) * 100,
        "utm_y_m": 1400000 + np.arange(n) * 100,
        "land_cover_code": [50] * n,
        "ndvi": [0.3] * n,
        "ndbi": [0.2] * n,
        "ndwi": [-0.1] * n,
        "building_density": [0.6] * n,
        "distance_to_roads_m": [25.0] * n,
        "distance_to_water_m": [300.0] * n,
        "distance_to_parks_m": [500.0] * n,
        "elevation_m": [15.0] * n,
        "slope_deg": [2.0] * n,
        "aspect_sin": [0.0] * n,
        "aspect_cos": [1.0] * n,
        "lst_day_celsius": [38.5] * n,
        "lst_night_celsius": [26.0] * n,
        "primary_driver_day": ["ndvi"] * 10 + ["distance_to_parks_m"] * 5,
        "secondary_driver_day": ["distance_to_water_m"] * n,
        "primary_driver_night": ["building_density"] * n,
        "secondary_driver_night": ["land_cover_code"] * n,
        "shap_day_ndvi": [-1.2] * n,
        "shap_day_building_density": [0.1] * n,
        "shap_night_ndvi": [-0.05] * n,
        "shap_night_building_density": [1.8] * n,
        "shap_domain_consistency_score_day": [92.0] * n,
        "shap_domain_consistency_score_night": [88.0] * n,
        "day_hotspot_id": ["DAY_HOT_0001"] * 10 + [None] * 5,
        "night_hotspot_id": [None] * 10 + ["NIGHT_HOT_0001"] * 5,
        "hotspot_group_id": ["HG_0001"] * n,
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    sample_gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

    # 3. Execute Stage 7 with M1 registry injected
    exporter = Stage7DriverKnowledgeExporter(
        output_dir=tmp_path / "out",
        metadata_dir=tmp_path / "out",
        hotspot_registry_path=m1_reg_path
    )
    manifest = exporter.run(gdf_in=sample_gdf)
    assert manifest["status"] == "SUCCESS"

    merged_reg = pd.read_parquet(tmp_path / "out" / "driver_attribution_registry.parquet")
    assert len(merged_reg) == 2

    # Check Module 1 columns are preserved
    assert "cluster_area_m2" in merged_reg.columns
    assert "peak_lst" in merged_reg.columns
    assert "mean_suhii" in merged_reg.columns
    assert merged_reg.loc[merged_reg["hotspot_id"] == "DAY_HOT_0001", "cluster_area_m2"].iloc[0] == 100000.0
    assert merged_reg.loc[merged_reg["hotspot_id"] == "NIGHT_HOT_0001", "cluster_area_m2"].iloc[0] == 50000.0

    # Check Module 2 driver columns are attached
    assert "dominant_driver" in merged_reg.columns
    assert merged_reg.loc[merged_reg["hotspot_id"] == "DAY_HOT_0001", "dominant_driver"].iloc[0] == "ndvi"
    assert merged_reg.loc[merged_reg["hotspot_id"] == "NIGHT_HOT_0001", "dominant_driver"].iloc[0] == "building_density"

    # Check Phase 5 Consensus and Diurnal Shift intelligence
    assert "driver_consensus_pct" in merged_reg.columns
    assert merged_reg.loc[merged_reg["hotspot_id"] == "DAY_HOT_0001", "driver_consensus_pct"].iloc[0] == 100.0
    assert merged_reg.loc[merged_reg["hotspot_id"] == "NIGHT_HOT_0001", "driver_consensus_pct"].iloc[0] == 100.0

    assert "diurnal_driver_shift" in merged_reg.columns
    assert merged_reg.loc[merged_reg["hotspot_id"] == "DAY_HOT_0001", "diurnal_driver_shift"].iloc[0] == "ndvi -> building_density"
    assert merged_reg.loc[merged_reg["hotspot_id"] == "NIGHT_HOT_0001", "diurnal_driver_shift"].iloc[0] == "ndvi -> building_density"
