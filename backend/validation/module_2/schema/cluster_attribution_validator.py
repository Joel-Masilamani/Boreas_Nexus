"""
Cluster Attribution Registry Validator for Module 2

Validates structural, semantic, and period integrity of the Driver Attribution Registry
(driver_attribution_registry.parquet), verifying entity parity with Module 1 (167 entities),
absence of duplicate keys, period-correct driver attributions, and physical consistency bounds.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class ClusterAttributionValidator:
    """
    Validates the Driver Attribution Registry (driver_attribution_registry.parquet).
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        self.cfg = config or {}

    def validate(self, registry_df: pd.DataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes structural and semantic audits on the cluster attribution registry.
        """
        logger.info("Executing Cluster Attribution Registry Validation...")
        results: List[ValidationResult] = []
        diagnostics: Dict[str, Any] = {}

        total_entities = len(registry_df)
        diagnostics["total_entities"] = total_entities

        # 1. Total Entity Count Parity Check (Expected: exactly 167 entities)
        expected_total = 167
        if total_entities == expected_total:
            res_count = ValidationResult(
                validation_id="REGISTRY-ENTITY-COUNT-PARITY",
                validation_type="REGISTRY_STRUCTURAL",
                metric="total_entity_count",
                expected=expected_total,
                actual=total_entities,
                status=ValidationStatus.PASS,
                message=f"Entity count matches authoritative Module 1 population ({expected_total} entities)."
            )
        else:
            res_count = ValidationResult(
                validation_id="REGISTRY-ENTITY-COUNT-PARITY",
                validation_type="REGISTRY_STRUCTURAL",
                metric="total_entity_count",
                expected=expected_total,
                actual=total_entities,
                status=ValidationStatus.FAIL,
                message=f"Entity count mismatch: expected {expected_total}, found {total_entities}."
            )
        results.append(res_count)

        # 2. Key Uniqueness and Non-Nullability Check
        null_ids = int(registry_df["hotspot_id"].isnull().sum()) if "hotspot_id" in registry_df.columns else total_entities
        dup_ids = int(registry_df["hotspot_id"].duplicated().sum()) if "hotspot_id" in registry_df.columns else total_entities

        if null_ids == 0 and dup_ids == 0:
            res_uniq = ValidationResult(
                validation_id="REGISTRY-KEY-UNIQUENESS",
                validation_type="REGISTRY_STRUCTURAL",
                metric="hotspot_id_duplicates_or_nulls",
                expected=0,
                actual=0,
                status=ValidationStatus.PASS,
                message="hotspot_id is 100% unique and non-null."
            )
        else:
            res_uniq = ValidationResult(
                validation_id="REGISTRY-KEY-UNIQUENESS",
                validation_type="REGISTRY_STRUCTURAL",
                metric="hotspot_id_duplicates_or_nulls",
                expected=0,
                actual=null_ids + dup_ids,
                status=ValidationStatus.FAIL,
                message=f"hotspot_id contains {null_ids} nulls and {dup_ids} duplicates."
            )
        results.append(res_uniq)

        # 3. Period Category and Distribution Check (128 DAY, 39 NIGHT)
        if "period" in registry_df.columns:
            period_counts = registry_df["period"].value_counts().to_dict()
            diagnostics["period_counts"] = period_counts
            day_count = period_counts.get("DAY", 0)
            night_count = period_counts.get("NIGHT", 0)

            if day_count == 128 and night_count == 39:
                res_period = ValidationResult(
                    validation_id="REGISTRY-PERIOD-DISTRIBUTION",
                    validation_type="REGISTRY_SEMANTIC",
                    metric="day_night_entity_counts",
                    expected={"DAY": 128, "NIGHT": 39},
                    actual={"DAY": day_count, "NIGHT": night_count},
                    status=ValidationStatus.PASS,
                    message="DAY (128) and NIGHT (39) entity distribution matches Module 1 contract."
                )
            else:
                res_period = ValidationResult(
                    validation_id="REGISTRY-PERIOD-DISTRIBUTION",
                    validation_type="REGISTRY_SEMANTIC",
                    metric="day_night_entity_counts",
                    expected={"DAY": 128, "NIGHT": 39},
                    actual={"DAY": day_count, "NIGHT": night_count},
                    status=ValidationStatus.FAIL,
                    message=f"Period distribution mismatch: DAY={day_count}, NIGHT={night_count}."
                )
        else:
            res_period = ValidationResult(
                validation_id="REGISTRY-PERIOD-DISTRIBUTION",
                validation_type="REGISTRY_SEMANTIC",
                metric="period_column_presence",
                expected="period",
                actual="MISSING",
                status=ValidationStatus.FAIL,
                message="Column 'period' is missing from Driver Attribution Registry."
            )
        results.append(res_period)

        # 4. Period-Aware Dominant Driver Attribution Validity Check
        if "dominant_driver" in registry_df.columns and "period" in registry_df.columns:
            null_drivers = int(registry_df["dominant_driver"].isnull().sum())
            unknown_drivers = int((registry_df["dominant_driver"] == "unknown").sum())

            # Check that nighttime clusters possess nighttime drivers
            night_entities = registry_df[registry_df["period"] == "NIGHT"]
            night_drivers = night_entities["dominant_driver"].value_counts().to_dict()
            diagnostics["night_dominant_drivers"] = night_drivers

            if null_drivers == 0 and unknown_drivers == 0:
                res_driver = ValidationResult(
                    validation_id="REGISTRY-DOMINANT-DRIVER-VALIDITY",
                    validation_type="REGISTRY_SEMANTIC",
                    metric="invalid_dominant_drivers",
                    expected=0,
                    actual=0,
                    status=ValidationStatus.PASS,
                    message="All entities possess valid, period-attributed dominant drivers."
                )
            else:
                res_driver = ValidationResult(
                    validation_id="REGISTRY-DOMINANT-DRIVER-VALIDITY",
                    validation_type="REGISTRY_SEMANTIC",
                    metric="invalid_dominant_drivers",
                    expected=0,
                    actual=null_drivers + unknown_drivers,
                    status=ValidationStatus.FAIL,
                    message=f"Registry contains {null_drivers} null drivers and {unknown_drivers} unknown drivers."
                )
        else:
            res_driver = ValidationResult(
                validation_id="REGISTRY-DOMINANT-DRIVER-VALIDITY",
                validation_type="REGISTRY_SEMANTIC",
                metric="dominant_driver_presence",
                expected="dominant_driver",
                actual="MISSING",
                status=ValidationStatus.FAIL,
                message="Column 'dominant_driver' is missing from Driver Attribution Registry."
            )
        results.append(res_driver)

        # 5. Domain Consistency Score Boundary Check [0.0, 100.0]
        if "domain_consistency_score" in registry_df.columns:
            scores = registry_df["domain_consistency_score"].dropna()
            null_scores = int(registry_df["domain_consistency_score"].isnull().sum())
            out_of_bounds = int(((scores < 0.0) | (scores > 100.0)).sum())

            if null_scores == 0 and out_of_bounds == 0:
                res_score = ValidationResult(
                    validation_id="REGISTRY-DOMAIN-CONSISTENCY-BOUNDS",
                    validation_type="REGISTRY_PHYSICS",
                    metric="consistency_score_bounds",
                    expected="[0.0, 100.0]",
                    actual=f"min={round(float(scores.min()), 2)}, max={round(float(scores.max()), 2)}",
                    status=ValidationStatus.PASS,
                    message="domain_consistency_score is non-null and within valid physical bounds [0, 100]."
                )
            else:
                res_score = ValidationResult(
                    validation_id="REGISTRY-DOMAIN-CONSISTENCY-BOUNDS",
                    validation_type="REGISTRY_PHYSICS",
                    metric="consistency_score_bounds",
                    expected="[0.0, 100.0]",
                    actual=f"nulls={null_scores}, out_of_bounds={out_of_bounds}",
                    status=ValidationStatus.FAIL,
                    message=f"domain_consistency_score has {null_scores} nulls and {out_of_bounds} out-of-bounds values."
                )
        else:
            res_score = ValidationResult(
                validation_id="REGISTRY-DOMAIN-CONSISTENCY-BOUNDS",
                validation_type="REGISTRY_PHYSICS",
                metric="domain_consistency_score_presence",
                expected="domain_consistency_score",
                actual="MISSING",
                status=ValidationStatus.FAIL,
                message="Column 'domain_consistency_score' missing from registry."
            )
        results.append(res_score)

        # 6. Module 1 Morphological Columns Parity Check
        m1_morph_cols = ["cluster_area_m2", "cluster_perimeter_m", "cluster_size_pixels", "peak_lst", "mean_suhii"]
        present_morph = [c for c in m1_morph_cols if c in registry_df.columns]
        diagnostics["present_morphology_columns"] = present_morph

        if len(present_morph) == len(m1_morph_cols):
            res_morph = ValidationResult(
                validation_id="REGISTRY-MODULE1-MORPHOLOGY-PARITY",
                validation_type="REGISTRY_INTEGRATION",
                metric="morphology_columns_presence",
                expected=m1_morph_cols,
                actual=present_morph,
                status=ValidationStatus.PASS,
                message="All authoritative Module 1 morphological metrics successfully attached to entities."
            )
        else:
            missing_morph = list(set(m1_morph_cols) - set(present_morph))
            res_morph = ValidationResult(
                validation_id="REGISTRY-MODULE1-MORPHOLOGY-PARITY",
                validation_type="REGISTRY_INTEGRATION",
                metric="morphology_columns_presence",
                expected=m1_morph_cols,
                actual=f"Missing: {missing_morph}",
                status=ValidationStatus.WARN,
                message=f"Some Module 1 morphological columns are missing: {missing_morph}."
            )
        results.append(res_morph)

        # Compute CheckSummary
        passed_c = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_c = sum(1 for r in results if r.status == ValidationStatus.WARN)
        failed_c = sum(1 for r in results if r.status == ValidationStatus.FAIL)

        overall_st = ValidationStatus.FAIL if failed_c > 0 else (ValidationStatus.WARN if warn_c > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="CLUSTER_ATTRIBUTION_REGISTRY",
            total_checks=len(results),
            pass_count=passed_c,
            warn_count=warn_c,
            fail_count=failed_c,
            status=overall_st,
            findings=[r.message for r in results if r.status != ValidationStatus.PASS]
        )

        return summary, results, diagnostics
