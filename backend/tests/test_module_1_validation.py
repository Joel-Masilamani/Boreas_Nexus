"""
Consolidated Tests for Module 1 Standalone Validation Layer
"""

import pytest
from validation.module_1.suhii_baseline_validator import SuhiiBaselineValidator
from validation.module_1.spatial_stats_validator import SpatialStatsValidator
from validation.module_1.cluster_topology_validator import ClusterTopologyValidator
from validation.module_1.diurnal_persistence_validator import DiurnalPersistenceValidator
from validation.module_1.schema_contract_validator import SchemaContractValidator
from validation.module_1.pipeline import Module1ValidationPipeline
from validation.core.models import ValidationStatus


def test_suhii_baseline_validator(sample_m1_gdf):
    val = SuhiiBaselineValidator({})
    summary, results, diag = val.validate(sample_m1_gdf)
    assert summary.fail_count == 0
    assert "recalculated_rural_base_day" in diag


def test_spatial_stats_validator(sample_m1_gdf):
    val = SpatialStatsValidator({})
    summary, results, diag = val.validate(sample_m1_gdf)
    assert summary.fail_count == 0
    assert diag["total_points_evaluated"] == len(sample_m1_gdf)


def test_cluster_topology_validator(sample_m1_gdf):
    val = ClusterTopologyValidator({"min_cluster_points": 1})
    summary, results, diag = val.validate(sample_m1_gdf)
    assert summary.fail_count == 0
    assert diag["total_validated_clusters"] > 0


def test_diurnal_persistence_validator(sample_m1_gdf):
    val = DiurnalPersistenceValidator({})
    summary, results, diag = val.validate(sample_m1_gdf)
    assert summary.fail_count == 0
    assert results[0].status == ValidationStatus.PASS


def test_schema_contract_validator_module1(sample_m1_gdf):
    contracts = {
        "point_id": {"datatype": "string", "nullable": False},
        "lst_day_celsius": {"datatype": "float", "valid_min": -50.0, "valid_max": 80.0, "nullable": False},
        "is_hotspot_day": {"datatype": "bool", "nullable": False}
    }
    val = SchemaContractValidator({"data_contracts": {"fields": contracts}})
    summary, results, diag = val.validate(sample_m1_gdf)
    assert summary.fail_count == 0


def test_module1_validation_pipeline_real_dataset():
    pipeline = Module1ValidationPipeline()
    report = pipeline.run()
    assert report.total_checks > 5
    assert report.fail_count == 0
    assert report.overall_status in [ValidationStatus.PASS, ValidationStatus.WARN]
    assert (pipeline.output_dir / "reports/validation_summary.json").exists()
    assert (pipeline.output_dir / "reports/validation_details.json").exists()
