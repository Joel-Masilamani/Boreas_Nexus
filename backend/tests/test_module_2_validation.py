"""
Consolidated Tests for Module 2 Standalone Validation Layer
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import geopandas as gpd

from validation.core.models import ValidationStatus, ValidationResult, DatasetValidationReport
from validation.module_2.config import ValidationConfig
from validation.module_2.geospatial.building_density_validator import BuildingDensityValidator
from validation.module_2.geospatial.terrain_validator import TerrainValidator
from validation.module_2.temporal.temporal_alignment_validator import TemporalAlignmentValidator
from validation.module_2.ml.spatial_leakage_validator import SpatialBlockSplitter, SpatialLeakageValidator
from validation.module_2.explainability.shap_validator import ShapValidator
from validation.module_2.spatial.gwr_validator import GWRValidator
from validation.module_2.schema.schema_range_validator import SchemaRangeValidator
from validation.module_2.schema.cluster_attribution_validator import ClusterAttributionValidator
from validation.module_2.pipeline import Module2ValidationPipeline


# =====================================================================
# 1. Framework Tests
# =====================================================================
def test_validation_result_serialization():
    res = ValidationResult(
        validation_id="TEST-001",
        validation_type="GEOSPATIAL",
        metric="building_density",
        expected=0.5,
        actual=0.52,
        status=ValidationStatus.PASS,
        message="Values within tolerance"
    )
    d = res.to_dict()
    assert d["validation_id"] == "TEST-001"
    assert d["status"] == "PASS"


def test_validation_config_loading():
    cfg = ValidationConfig("config/module2_validation_config.yaml")
    assert cfg.version == "1.0.0"
    assert len(str(cfg.dataset_path)) > 0


# =====================================================================
# 2. Geospatial Validators Tests
# =====================================================================
def test_building_density_validator(sample_shap_gdf):
    sample_shap_gdf["building_density"] = [0.45] * len(sample_shap_gdf)
    val = BuildingDensityValidator({})
    summary, results, diag = val.validate(sample_shap_gdf)
    assert summary.total_checks >= 2
    assert summary.fail_count == 0


def test_terrain_validator(sample_shap_gdf):
    sample_shap_gdf["elevation_m"] = [10.0] * len(sample_shap_gdf)
    sample_shap_gdf["slope_deg"] = [2.5] * len(sample_shap_gdf)
    val = TerrainValidator({})
    summary, results, diag = val.validate(sample_shap_gdf)
    assert summary.total_checks >= 2
    assert summary.fail_count == 0


# =====================================================================
# 3. Temporal Validator Tests
# =====================================================================
def test_temporal_alignment_undefined_windows_warn(sample_shap_gdf):
    val = TemporalAlignmentValidator({"temporal_windows": {"lst_weather": None, "lst_ndvi": None}})
    summary, results, gaps = val.validate(sample_shap_gdf)
    assert len(gaps) >= 2
    assert summary.warn_count >= 2
    assert summary.fail_count == 0


# =====================================================================
# 4. ML Spatial Leakage Tests
# =====================================================================
def test_spatial_block_splitter_disjoint():
    n = 100
    df = pd.DataFrame({
        "point_id": [f"pt_{i}" for i in range(n)],
        "spatial_block_id": [f"block_{i % 10}" for i in range(n)]
    })
    splitter = SpatialBlockSplitter(block_col="spatial_block_id")
    train_idx, val_idx, test_idx, block_sets = splitter.split(df)
    assert block_sets["train_blocks"].isdisjoint(block_sets["val_blocks"])
    assert block_sets["train_blocks"].isdisjoint(block_sets["test_blocks"])
    assert block_sets["val_blocks"].isdisjoint(block_sets["test_blocks"])


# =====================================================================
# 5. SHAP & GWR Explainability Tests
# =====================================================================
def test_shap_validator_exact_reconstruction(sample_shap_gdf):
    val = ShapValidator({"shap_reconstruction": {"tolerance_max_error": 1.0e-4}})
    summary, results, diag = val.validate(sample_shap_gdf)
    assert summary.fail_count == 0


def test_gwr_validator_distribution(sample_shap_gdf):
    sample_shap_gdf["gwr_local_r2_day"] = np.random.uniform(0.2, 0.6, len(sample_shap_gdf))
    sample_shap_gdf["gwr_coef_day_ndvi"] = np.random.uniform(-3.0, -1.0, len(sample_shap_gdf))
    sample_shap_gdf["gwr_coef_day_building_density"] = np.random.uniform(1.0, 4.0, len(sample_shap_gdf))
    val = GWRValidator({})
    summary, results, diag = val.validate(sample_shap_gdf)
    assert summary.fail_count == 0


# =====================================================================
# 6. Schema & Master Validation Pipeline Tests
# =====================================================================
def test_schema_range_validator(sample_shap_gdf):
    cfg = ValidationConfig("config/module2_validation_config.yaml")
    val = SchemaRangeValidator(cfg.raw_cfg)
    summary, results, diag = val.validate(sample_shap_gdf)
    assert summary.total_checks > 0


def test_cluster_attribution_validator_pass():
    """Tests ClusterAttributionValidator against a valid 167-entity synthetic registry."""
    day_ids = [f"DAY_HOT_{i:04d}" for i in range(1, 129)]
    night_ids = [f"NIGHT_HOT_{i:04d}" for i in range(1, 40)]
    all_ids = day_ids + night_ids
    periods = ["DAY"] * 128 + ["NIGHT"] * 39

    df = pd.DataFrame({
        "hotspot_id": all_ids,
        "period": periods,
        "hotspot_group_id": ["HG_0001"] * 72 + [None] * 95,
        "cluster_area_m2": [10000.0] * 167,
        "cluster_perimeter_m": [400.0] * 167,
        "cluster_size_pixels": [10] * 167,
        "peak_lst": [42.0] * 128 + [28.0] * 39,
        "mean_suhii": [3.5] * 167,
        "dominant_driver": ["ndvi"] * 128 + ["building_density"] * 39,
        "domain_consistency_score": [95.0] * 167,
        "mean_shap_building_density": [0.5] * 167
    })

    validator = ClusterAttributionValidator()
    summary, results, diag = validator.validate(df)
    assert summary.fail_count == 0
    assert summary.pass_count >= 5


def test_module2_validation_pipeline_real_dataset():
    pipeline = Module2ValidationPipeline()
    report = pipeline.run()
    assert report.total_checks >= 50
    assert report.fail_count == 0
    assert report.overall_status in [ValidationStatus.PASS, ValidationStatus.WARN]
    assert (pipeline.output_dir / "reports/validation_summary.json").exists()
    assert (pipeline.output_dir / "reports/validation_details.json").exists()
