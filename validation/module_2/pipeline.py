"""
Master Validation Pipeline for Module 2: Urban Heat Driver Intelligence

Orchestrates all independent validation engines, aggregates check summaries,
generates machine-readable structured validation artifacts, and produces the
authoritative DatasetValidationReport.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import datetime
import json
import uuid
import geopandas as gpd
import pandas as pd

from utils.logger import logger
from validation.core.models import (
    ValidationStatus, ValidationResult, DatasetValidationReport, CheckSummary
)
from validation.module_2.config import ValidationConfig
from validation.module_2.geospatial.building_density_validator import BuildingDensityValidator
from validation.module_2.geospatial.terrain_validator import TerrainValidator
from validation.module_2.temporal.temporal_alignment_validator import TemporalAlignmentValidator
from validation.module_2.ml.spatial_leakage_validator import SpatialLeakageValidator
from validation.module_2.explainability.shap_validator import ShapValidator
from validation.module_2.spatial.gwr_validator import GWRValidator
from validation.module_2.schema.schema_range_validator import SchemaRangeValidator


class Module2ValidationPipeline:
    """
    Executes end-to-end standalone validation of Module 2 outputs.
    """

    def __init__(self, config_path: Path | str = Path("config/module2_validation_config.yaml")):
        self.val_config = ValidationConfig(config_path)
        self.output_dir = self.val_config.output_dir
        self._ensure_output_dirs()

    def _ensure_output_dirs(self):
        """Creates subdirectories for machine-readable validation artifacts."""
        for sub in ["geospatial", "temporal", "ml", "explainability", "spatial", "reports"]:
            (self.output_dir / sub).mkdir(parents=True, exist_ok=True)

    def run(self, gdf_in: Optional[gpd.GeoDataFrame] = None) -> DatasetValidationReport:
        """
        Runs all independent validation suites on the Module 2 knowledge layer.
        """
        run_id = f"VAL-M2-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.info(f"=================================================================")
        logger.info(f"STARTING MODULE 2 VALIDATION ENGINE [Run ID: {run_id}]")
        logger.info(f"=================================================================")

        # 1. Load Dataset
        if gdf_in is not None:
            gdf = gdf_in
        else:
            dataset_file = self.val_config.dataset_path
            if not dataset_file.exists():
                raise FileNotFoundError(f"Knowledge Layer file not found at: {dataset_file}")
            logger.info(f"Loading Module 2 Knowledge Layer from {dataset_file}...")
            gdf = gpd.read_parquet(dataset_file)

        all_results: List[ValidationResult] = []
        all_summaries: Dict[str, Any] = {}
        all_details: Dict[str, Any] = {}
        spec_gaps: List[Dict[str, Any]] = []
        critical_findings: List[Dict[str, Any]] = []
        manual_inspection_items: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # Suite 1: Geospatial Building Density & Terrain
        # -------------------------------------------------------------
        bd_validator = BuildingDensityValidator(self.val_config.get_section("geospatial").get("building_density", {}))
        bd_sum, bd_res, bd_diag = bd_validator.validate(gdf)
        all_results.extend(bd_res)
        all_summaries["geospatial_building_density"] = bd_sum.to_dict()
        all_details["building_density_investigation"] = bd_diag

        # Save machine-readable artifact
        with open(self.output_dir / "geospatial/building_density_investigation.json", "w", encoding="utf-8") as f:
            json.dump(bd_diag, f, indent=2, default=str)

        terrain_validator = TerrainValidator(self.val_config.get_section("geospatial").get("terrain_dem", {}))
        tr_sum, tr_res, tr_diag = terrain_validator.validate(gdf)
        all_results.extend(tr_res)
        all_summaries["terrain_dem"] = tr_sum.to_dict()
        all_details["terrain_investigation"] = tr_diag

        # Save machine-readable artifact
        with open(self.output_dir / "geospatial/terrain_investigation.json", "w", encoding="utf-8") as f:
            json.dump(tr_diag, f, indent=2, default=str)

        # -------------------------------------------------------------
        # Suite 2: Temporal Alignment & Lineage
        # -------------------------------------------------------------
        temp_validator = TemporalAlignmentValidator(self.val_config.get_section("temporal_lineage"))
        temp_sum, temp_res, temp_gaps = temp_validator.validate(gdf)
        all_results.extend(temp_res)
        all_summaries["temporal_lineage"] = temp_sum.to_dict()
        spec_gaps.extend(temp_gaps)

        with open(self.output_dir / "temporal/temporal_alignment_report.json", "w", encoding="utf-8") as f:
            json.dump({"summary": temp_sum.to_dict(), "specification_gaps": temp_gaps}, f, indent=2, default=str)

        # -------------------------------------------------------------
        # Suite 3: ML Generalization & Spatial Leakage
        # -------------------------------------------------------------
        ml_validator = SpatialLeakageValidator(self.val_config.get_section("ml_validation"))
        ml_sum, ml_res, ml_bench = ml_validator.validate(gdf)
        all_results.extend(ml_res)
        all_summaries["ml_spatial_leakage"] = ml_sum.to_dict()
        all_details["ml_benchmark"] = ml_bench

        with open(self.output_dir / "ml/spatial_split_benchmark.json", "w", encoding="utf-8") as f:
            json.dump(ml_bench, f, indent=2, default=str)

        # -------------------------------------------------------------
        # Suite 4: Explainability & SHAP Reconstruction
        # -------------------------------------------------------------
        shap_validator = ShapValidator(self.val_config.get_section("explainability"))
        shap_sum, shap_res, shap_diag = shap_validator.validate(gdf)
        all_results.extend(shap_res)
        all_summaries["shap_explainability"] = shap_sum.to_dict()
        all_details["shap_details"] = shap_diag

        with open(self.output_dir / "explainability/shap_validation_report.json", "w", encoding="utf-8") as f:
            json.dump(shap_diag, f, indent=2, default=str)

        # -------------------------------------------------------------
        # Suite 5: GWR Statistical Validation
        # -------------------------------------------------------------
        gwr_validator = GWRValidator(self.val_config.get_section("spatial_gwr"))
        gwr_sum, gwr_res, gwr_diag = gwr_validator.validate(gdf)
        all_results.extend(gwr_res)
        all_summaries["gwr_statistical"] = gwr_sum.to_dict()
        all_details["gwr_details"] = gwr_diag

        with open(self.output_dir / "spatial/gwr_validation_report.json", "w", encoding="utf-8") as f:
            json.dump(gwr_diag, f, indent=2, default=str)

        # -------------------------------------------------------------
        # Suite 6: Schema & Data Contracts
        # -------------------------------------------------------------
        schema_validator = SchemaRangeValidator(self.val_config.raw_cfg)
        sch_sum, sch_res, sch_diag = schema_validator.validate(gdf)
        all_results.extend(sch_res)
        all_summaries["schema_data_contracts"] = sch_sum.to_dict()
        all_details["schema_details"] = sch_diag

        # -------------------------------------------------------------
        # Aggregate Report & Status Computation
        # -------------------------------------------------------------
        total_checks = len(all_results)
        pass_count = sum(1 for r in all_results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in all_results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL) if 'results' in locals() else sum(1 for r in all_results if r.status == ValidationStatus.FAIL)

        # Overall status semantics:
        # A single FAIL results in overall FAIL.
        # Warnings (such as specification gaps) result in WARN.
        if fail_count > 0:
            overall_status = ValidationStatus.FAIL
        elif warn_count > 0:
            overall_status = ValidationStatus.WARN
        else:
            overall_status = ValidationStatus.PASS

        # Collect critical findings and manual inspection items
        for r in all_results:
            if r.status == ValidationStatus.FAIL:
                critical_findings.append(r.to_dict())
            elif r.status == ValidationStatus.WARN:
                manual_inspection_items.append(r.to_dict())

        report = DatasetValidationReport(
            dataset="urban_heat_driver_knowledge_layer.geoparquet",
            validation_run_id=run_id,
            timestamp=timestamp,
            configuration_version=self.val_config.version,
            total_checks=total_checks,
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            overall_status=overall_status,
            configuration_gaps=spec_gaps,
            critical_findings=critical_findings,
            manual_inspection_items=manual_inspection_items,
            validation_summaries=all_summaries,
            validation_details=all_details
        )

        # Export consolidated reports
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
                "configuration_gaps_count": len(spec_gaps),
                "validation_summaries": all_summaries
            }, f, indent=2, default=str)

        with open(details_path, "w", encoding="utf-8") as f:
            f.write(report.to_json(indent=2))

        logger.info("=================================================================")
        logger.info(f"MODULE 2 VALIDATION COMPLETED -> OVERALL STATUS: {overall_status.value}")
        logger.info(f"CHECKS: {total_checks} | PASS: {pass_count} | WARN: {warn_count} | FAIL: {fail_count}")
        logger.info(f"Artifacts exported to: {self.output_dir}")
        logger.info("=================================================================")

        return report
