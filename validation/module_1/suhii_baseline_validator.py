"""
SUHII Urban-Rural Baseline Validator

Independently recalculates rural reference baseline temperatures and surface urban
heat island intensity (SUHII) anomalies across diurnal cycles, verifying mathematical
correctness against stored values.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class SuhiiBaselineValidator:
    """
    Validates SUHII baseline temperature calculations and anomaly deltas.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.rural_codes = self.cfg.get("rural_landcover_codes", [10, 20, 30, 40])
        self.tolerances = self.cfg.get("tolerances", {
            "baseline_max_abs_diff_celsius": 0.50,
            "suhii_max_abs_diff_celsius": 0.50
        })

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes SUHII baseline and anomaly validation.
        """
        logger.info("Executing SUHII Urban-Rural Baseline Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []

        required_cols = ["lst_day_celsius", "lst_night_celsius", "suhii_day_celsius", "suhii_night_celsius"]
        missing = [c for c in required_cols if c not in gdf.columns]
        if missing:
            res = ValidationResult(
                validation_id="M1-SUHII-COL-001",
                validation_type="SUHII_BASELINE",
                metric="column_presence",
                expected=str(required_cols),
                actual=f"Missing: {missing}",
                status=ValidationStatus.FAIL,
                message=f"Missing required SUHII columns: {missing}"
            )
            return CheckSummary("SUHII Baseline", 1, 0, 0, 1, ValidationStatus.FAIL, [res.message]), [res], {}

        # 1. Identify Rural Reference Samples
        if "is_rural" in gdf.columns:
            rural_mask = gdf["is_rural"] == True
        elif "land_cover_code" in gdf.columns:
            rural_mask = gdf["land_cover_code"].isin(self.rural_codes)
        else:
            # Fallback: lowest 15% building density points
            bd_col = "building_density" if "building_density" in gdf.columns else None
            if bd_col:
                rural_mask = gdf[bd_col] <= gdf[bd_col].quantile(0.15)
            else:
                rural_mask = np.ones(len(gdf), dtype=bool)

        rural_df = gdf[rural_mask]
        rural_count = len(rural_df)

        if rural_count == 0:
            res = ValidationResult(
                validation_id="M1-SUHII-RURAL-COUNT",
                validation_type="SUHII_BASELINE",
                metric="rural_reference_count",
                expected="> 0 points",
                actual="0 points",
                status=ValidationStatus.FAIL,
                message="No rural reference points found in dataset to compute baseline."
            )
            return CheckSummary("SUHII Baseline", 1, 0, 0, 1, ValidationStatus.FAIL, [res.message]), [res], {}

        # Compute independent mean rural baselines
        recalc_rural_base_day = float(rural_df["lst_day_celsius"].mean())
        recalc_rural_base_night = float(rural_df["lst_night_celsius"].mean())

        # Check expected baseline temperature ranges
        day_range = self.cfg.get("expected_rural_baseline_range_day_celsius", [25.0, 40.0])
        night_range = self.cfg.get("expected_rural_baseline_range_night_celsius", [20.0, 32.0])

        day_base_valid = day_range[0] <= recalc_rural_base_day <= day_range[1]
        night_base_valid = night_range[0] <= recalc_rural_base_night <= night_range[1]

        base_status = ValidationStatus.PASS if (day_base_valid and night_base_valid) else ValidationStatus.WARN
        base_msg = (
            f"Rural Reference Baseline: Day = {recalc_rural_base_day:.2f}°C (valid range {day_range}), "
            f"Night = {recalc_rural_base_night:.2f}°C (valid range {night_range}) across {rural_count} points."
        )

        results.append(ValidationResult(
            validation_id="M1-SUHII-BASE-RANGE",
            validation_type="SUHII_BASELINE",
            metric="rural_baseline_temperature",
            expected=f"Day: {day_range}°C, Night: {night_range}°C",
            actual=f"Day: {recalc_rural_base_day:.2f}°C, Night: {recalc_rural_base_night:.2f}°C",
            status=base_status,
            message=base_msg,
            details={
                "recalculated_rural_base_day": recalc_rural_base_day,
                "recalculated_rural_base_night": recalc_rural_base_night,
                "rural_sample_count": rural_count
            }
        ))
        findings.append(base_msg)

        # 2. Re-calculate SUHII and compare with stored values
        recalc_suhii_day = gdf["lst_day_celsius"].values - recalc_rural_base_day
        recalc_suhii_night = gdf["lst_night_celsius"].values - recalc_rural_base_night

        stored_suhii_day = gdf["suhii_day_celsius"].values
        stored_suhii_night = gdf["suhii_night_celsius"].values

        day_diff = np.abs(stored_suhii_day - recalc_suhii_day)
        night_diff = np.abs(stored_suhii_night - recalc_suhii_night)

        max_day_diff = float(np.max(day_diff))
        mean_day_diff = float(np.mean(day_diff))
        max_night_diff = float(np.max(night_diff))
        mean_night_diff = float(np.mean(night_diff))

        tol_suhii = float(self.tolerances.get("suhii_max_abs_diff_celsius", 0.50))

        if max_day_diff <= tol_suhii and max_night_diff <= tol_suhii:
            suhii_status = ValidationStatus.PASS
            suhii_msg = (
                f"SUHII Anomaly Re-calculation verified: Max Day Diff = {max_day_diff:.3f}°C (Mean: {mean_day_diff:.3f}°C), "
                f"Max Night Diff = {max_night_diff:.3f}°C (Mean: {mean_night_diff:.3f}°C) <= {tol_suhii}°C tolerance."
            )
        else:
            suhii_status = ValidationStatus.WARN
            suhii_msg = f"SUHII discrepancies observed: Max Day Diff = {max_day_diff:.3f}°C, Max Night Diff = {max_night_diff:.3f}°C."

        results.append(ValidationResult(
            validation_id="M1-SUHII-ANOMALY-CHECK",
            validation_type="SUHII_BASELINE",
            metric="suhii_anomaly_delta",
            expected=f"diff <= {tol_suhii}°C",
            actual=f"MaxDay: {max_day_diff:.3f}°C, MaxNight: {max_night_diff:.3f}°C",
            error=max(max_day_diff, max_night_diff),
            threshold=tol_suhii,
            status=suhii_status,
            message=suhii_msg,
            details={
                "max_day_diff_celsius": max_day_diff,
                "mean_day_diff_celsius": mean_day_diff,
                "max_night_diff_celsius": max_night_diff,
                "mean_night_diff_celsius": mean_night_diff
            }
        ))
        findings.append(suhii_msg)

        # Summary
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="SUHII Rural Baseline",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=findings
        )

        suhii_diagnostics = {
            "rural_sample_count": rural_count,
            "recalculated_rural_base_day": recalc_rural_base_day,
            "recalculated_rural_base_night": recalc_rural_base_night,
            "mean_suhii_day": float(np.mean(stored_suhii_day)),
            "mean_suhii_night": float(np.mean(stored_suhii_night))
        }

        return summary, results, suhii_diagnostics
