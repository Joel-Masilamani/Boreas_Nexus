"""
Master Validation Pipeline for Module 1: Urban Heat Island & Hotspot Delineation

Orchestrates independent validation of rural reference baselines, SUHII thermal anomalies,
spatial autocorrelation & Getis-Ord Gi* significance, DBSCAN cluster topology,
diurnal persistence, and Knowledge Layer data contracts.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import datetime
import json
import uuid
import geopandas as gpd

from utils.logger import logger
from validation.core.models import (
    ValidationStatus, ValidationResult, DatasetValidationReport, CheckSummary
)
from validation.core.config import BaseValidationConfig
from validation.module_1.suhii_baseline_validator import SuhiiBaselineValidator
from validation.module_1.spatial_stats_validator import SpatialStatsValidator
from validation.module_1.cluster_topology_validator import ClusterTopologyValidator
from validation.module_1.diurnal_persistence_validator import DiurnalPersistenceValidator
from validation.module_1.schema_contract_validator import SchemaContractValidator


class Module1ValidationPipeline:
    """
    Executes end-to-end standalone validation of Module 1 outputs.
    """

    def __init__(self, config_path: Path | str = Path("config/module1_validation_config.yaml")):
        self.val_config = BaseValidationConfig(config_path)
        self.output_dir = self.val_config.output_dir
        self._ensure_output_dirs()

    def _ensure_output_dirs(self):
        """Creates subdirectories for machine-readable validation artifacts."""
        for sub in ["suhii", "spatial_stats", "cluster_topology", "diurnal_persistence", "reports"]:
            (self.output_dir / sub).mkdir(parents=True, exist_ok=True)

    def run(self, gdf_in: Optional[gpd.GeoDataFrame] = None) -> DatasetValidationReport:
        """
        Runs all independent validation suites on the Module 1 knowledge layer.
        """
        run_id = f"VAL-M1-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.info(f"=================================================================")
        logger.info(f"STARTING MODULE 1 VALIDATION ENGINE [Run ID: {run_id}]")
        logger.info(f"=================================================================")

        if gdf_in is not None:
            gdf = gdf_in
        else:
            dataset_file = self.val_config.dataset_path
            if not dataset_file.exists():
                raise FileNotFoundError(f"Module 1 Knowledge Layer not found at: {dataset_file}")
            logger.info(f"Loading Module 1 Knowledge Layer from {dataset_file}...")
            gdf = gpd.read_parquet(dataset_file)

        all_results: List[ValidationResult] = []
        all_summaries: Dict[str, Any] = {}
        all_details: Dict[str, Any] = {}
        critical_findings: List[Dict[str, Any]] = []
        manual_inspection_items: List[Dict[str, Any]] = []

        # 1. SUHII Baseline Validation
        suhii_val = SuhiiBaselineValidator(self.val_config.get_section("suhii_validation"))
        s_sum, s_res, s_diag = suhii_val.validate(gdf)
        all_results.extend(s_res)
        all_summaries["suhii_baseline"] = s_sum.to_dict()
        all_details["suhii_diagnostics"] = s_diag
        with open(self.output_dir / "suhii/suhii_baseline_report.json", "w", encoding="utf-8") as f:
            json.dump(s_diag, f, indent=2, default=str)

        # 2. Spatial Statistics (Getis-Ord Gi* & Moran's I)
        stats_val = SpatialStatsValidator(self.val_config.get_section("spatial_statistics"))
        st_sum, st_res, st_diag = stats_val.validate(gdf)
        all_results.extend(st_res)
        all_summaries["spatial_statistics"] = st_sum.to_dict()
        all_details["spatial_stats_diagnostics"] = st_diag
        with open(self.output_dir / "spatial_stats/spatial_stats_report.json", "w", encoding="utf-8") as f:
            json.dump(st_diag, f, indent=2, default=str)

        # 3. Cluster Topology & Continuity
        clust_val = ClusterTopologyValidator(self.val_config.get_section("cluster_topology"))
        c_sum, c_res, c_diag = clust_val.validate(gdf)
        all_results.extend(c_res)
        all_summaries["cluster_topology"] = c_sum.to_dict()
        all_details["cluster_diagnostics"] = c_diag
        with open(self.output_dir / "cluster_topology/cluster_topology_report.json", "w", encoding="utf-8") as f:
            json.dump(c_diag, f, indent=2, default=str)

        # 4. Day-Night Diurnal Persistence
        diurnal_val = DiurnalPersistenceValidator(self.val_config.get_section("diurnal_persistence"))
        d_sum, d_res, d_diag = diurnal_val.validate(gdf)
        all_results.extend(d_res)
        all_summaries["diurnal_persistence"] = d_sum.to_dict()
        all_details["persistence_diagnostics"] = d_diag
        with open(self.output_dir / "diurnal_persistence/diurnal_persistence_report.json", "w", encoding="utf-8") as f:
            json.dump(d_diag, f, indent=2, default=str)

        # 5. Schema & Data Contracts
        schema_val = SchemaContractValidator(self.val_config.raw_cfg)
        sc_sum, sc_res, sc_diag = schema_val.validate(gdf)
        all_results.extend(sc_res)
        all_summaries["schema_data_contracts"] = sc_sum.to_dict()
        all_details["schema_diagnostics"] = sc_diag

        # Aggregate Report & Status Computation
        total_checks = len(all_results)
        pass_count = sum(1 for r in all_results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in all_results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in all_results if r.status == ValidationStatus.FAIL)

        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        for r in all_results:
            if r.status == ValidationStatus.FAIL:
                critical_findings.append(r.to_dict())
            elif r.status == ValidationStatus.WARN:
                manual_inspection_items.append(r.to_dict())

        report = DatasetValidationReport(
            dataset="urban_heat_hotspot_knowledge_layer.geoparquet",
            validation_run_id=run_id,
            timestamp=timestamp,
            configuration_version=self.val_config.version,
            total_checks=total_checks,
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            overall_status=overall_status,
            critical_findings=critical_findings,
            manual_inspection_items=manual_inspection_items,
            validation_summaries=all_summaries,
            validation_details=all_details
        )

        summary_path = self.output_dir / "reports/validation_summary.json"
        details_path = self.output_dir / "reports/validation_details.json"

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "dataset": report.dataset,
                "validation_run_id": report.validation_run_id,
                "timestamp": report.timestamp,
                "overall_status": report.overall_status.value,
                "total_checks": report.total_checks,
                "pass_count": report.pass_count,
                "warn_count": report.warn_count,
                "fail_count": report.fail_count,
                "validation_summaries": all_summaries
            }, f, indent=2, default=str)

        with open(details_path, "w", encoding="utf-8") as f:
            f.write(report.to_json(indent=2))

        logger.info("=================================================================")
        logger.info(f"MODULE 1 VALIDATION COMPLETED -> OVERALL STATUS: {overall_status.value}")
        logger.info(f"CHECKS: {total_checks} | PASS: {pass_count} | WARN: {warn_count} | FAIL: {fail_count}")
        logger.info(f"Artifacts exported to: {self.output_dir}")
        logger.info("=================================================================")

        return report
