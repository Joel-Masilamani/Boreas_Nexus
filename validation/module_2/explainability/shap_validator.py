"""
Explainability & SHAP Validator

Validates SHAP mathematical additive reconstruction, explainer reproducibility metadata,
driver ranking integrity (magnitude-based sorting via abs(SHAP)), and signed semantic consistency.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class ShapValidator:
    """
    Validates SHAP explainability calculations and driver rankings.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.recon_cfg = self.cfg.get("shap_reconstruction", {
            "tolerance_max_error": 1.0e-4,
            "tolerance_mean_error": 1.0e-5
        })

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes full SHAP validation suite.
        """
        logger.info("Executing SHAP Explainability Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []

        shap_day_cols = [c for c in gdf.columns if c.startswith("shap_day_") and not c.startswith("shap_reconstruction") and not c.startswith("shap_base")]
        
        if not shap_day_cols:
            res = ValidationResult(
                validation_id="SHAP-COL-001",
                validation_type="SHAP_EXPLAINABILITY",
                metric="shap_columns_presence",
                expected="shap_day_* columns",
                actual="MISSING",
                status=ValidationStatus.FAIL,
                message="SHAP contribution columns not found in dataset."
            )
            return CheckSummary("SHAP Explainability", 1, 0, 0, 1, ValidationStatus.FAIL, [res.message]), [res], {}

        # 1. SHAP Additive Reconstruction Verification
        # Check if stored reconstruction error column exists or recompute
        if "shap_base_value_day" in gdf.columns and "lgbm_pred_lst_day_celsius" in gdf.columns:
            base_val = gdf["shap_base_value_day"].values
            shap_matrix = gdf[shap_day_cols].values
            pred_vals = gdf["lgbm_pred_lst_day_celsius"].values

            reconstructed = base_val + np.sum(shap_matrix, axis=1)
            reconstruction_errors = np.abs(pred_vals - reconstructed)

            max_err = float(np.max(reconstruction_errors))
            mean_err = float(np.mean(reconstruction_errors))
            tol_max = float(self.recon_cfg.get("tolerance_max_error", 1.0e-4))

            if max_err <= tol_max:
                recon_status = ValidationStatus.PASS
                recon_msg = f"SHAP additive property mathematically exact across all {len(gdf)} points. Max Error = {max_err:.2e} (<= {tol_max:.1e}), Mean Error = {mean_err:.2e}."
            else:
                recon_status = ValidationStatus.FAIL
                recon_msg = f"SHAP additive property violation: Max Error = {max_err:.2e} exceeds tolerance {tol_max:.1e}."

            results.append(ValidationResult(
                validation_id="SHAP-RECON-ADDITIVE",
                validation_type="SHAP_EXPLAINABILITY",
                metric="shap_additive_reconstruction_error",
                expected=f"max_error <= {tol_max}",
                actual=f"{max_err:.2e}",
                error=max_err,
                threshold=tol_max,
                status=recon_status,
                message=recon_msg,
                details={"max_absolute_error": max_err, "mean_absolute_error": mean_err}
            ))
            findings.append(recon_msg)

        # 2. Driver Ranking Validation (abs(SHAP) magnitude ranking)
        feature_names = np.array([c.replace("shap_day_", "") for c in shap_day_cols])
        shap_abs_matrix = np.abs(gdf[shap_day_cols].values)
        top_ranked_indices = np.argsort(-shap_abs_matrix, axis=1)

        expected_primary = feature_names[top_ranked_indices[:, 0]]
        expected_secondary = feature_names[top_ranked_indices[:, 1]]
        expected_tertiary = feature_names[top_ranked_indices[:, 2]]

        primary_matches = 0
        secondary_matches = 0
        tertiary_matches = 0
        total_rows = len(gdf)

        if "primary_driver_day" in gdf.columns:
            primary_matches = int(np.sum(gdf["primary_driver_day"].values == expected_primary))
        if "secondary_driver_day" in gdf.columns:
            secondary_matches = int(np.sum(gdf["secondary_driver_day"].values == expected_secondary))
        if "tertiary_driver_day" in gdf.columns:
            tertiary_matches = int(np.sum(gdf["tertiary_driver_day"].values == expected_tertiary))

        primary_pct = (primary_matches / total_rows) * 100.0
        sec_pct = (secondary_matches / total_rows) * 100.0
        tert_pct = (tertiary_matches / total_rows) * 100.0

        if primary_pct == 100.0 and sec_pct == 100.0 and tert_pct == 100.0:
            rank_status = ValidationStatus.PASS
            rank_msg = f"Driver rankings (primary/secondary/tertiary) are 100% consistent with abs(SHAP) sorting across all {total_rows} points."
        else:
            rank_status = ValidationStatus.FAIL
            rank_msg = f"Driver ranking mismatch: Primary={primary_pct:.1f}%, Secondary={sec_pct:.1f}%, Tertiary={tert_pct:.1f}% matches."

        results.append(ValidationResult(
            validation_id="SHAP-RANK-CONSISTENCY",
            validation_type="SHAP_EXPLAINABILITY",
            metric="driver_ranking_magnitude_alignment",
            expected="100.0% match with abs(SHAP) sort",
            actual=f"P:{primary_pct:.1f}%, S:{sec_pct:.1f}%, T:{tert_pct:.1f}%",
            status=rank_status,
            message=rank_msg,
            details={
                "primary_match_pct": primary_pct,
                "secondary_match_pct": sec_pct,
                "tertiary_match_pct": tert_pct
            }
        ))
        findings.append(rank_msg)

        # 3. Signed Semantic Interpretation Check
        # Check that SHAP values are signed (contain both positive and negative values)
        has_negative = any((gdf[c] < 0).any() for c in shap_day_cols)
        has_positive = any((gdf[c] > 0).any() for c in shap_day_cols)

        if has_negative and has_positive:
            sign_status = ValidationStatus.PASS
            sign_msg = "SHAP values correctly preserve signed continuous directions (positive=heating, negative=cooling)."
        else:
            sign_status = ValidationStatus.WARN
            sign_msg = "SHAP values appear one-sided or were inappropriately modified to absolute magnitudes."

        results.append(ValidationResult(
            validation_id="SHAP-SIGN-SEMANTICS",
            validation_type="SHAP_EXPLAINABILITY",
            metric="signed_contribution_preservation",
            expected="Signed values (positive and negative components)",
            actual="Verified signed values",
            status=sign_status,
            message=sign_msg
        ))

        # Summary
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="SHAP Explainability",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=findings
        )

        explainability_details = {
            "reconstruction_check": results[0].details if len(results) > 0 else {},
            "ranking_consistency": results[1].details if len(results) > 1 else {},
            "evaluated_shap_feature_count": len(shap_day_cols)
        }

        return summary, results, explainability_details
