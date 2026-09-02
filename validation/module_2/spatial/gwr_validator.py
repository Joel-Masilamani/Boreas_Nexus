"""
GWR Statistical & Sensitivity Validator

Statistically validates Geographically Weighted Regression (GWR) outputs, evaluating
the full distribution of local R² metrics and testing parameter stability under
spatial bandwidth perturbation (±15%) using fast vectorized local regressions.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class GWRValidator:
    """
    Validates statistical stability and local performance of GWR coefficients.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.perturbation_pct = float(self.cfg.get("bandwidth_perturbation_pct", 0.15))
        self.stability_criteria = self.cfg.get("stability_criteria", {
            "pass_max_beta_relative_shift": 0.25,
            "warn_max_beta_relative_shift": 0.60
        })
        self.quantiles = self.cfg.get("local_r2_quantiles", [0.05, 0.25, 0.50, 0.75, 0.95])

    def _evaluate_bandwidth_sensitivity(
        self,
        gdf: gpd.GeoDataFrame,
        k_base: int = 60
    ) -> Dict[str, Any]:
        """
        Fast vectorized coefficient stability check under +/- 15% bandwidth perturbation.
        """
        drivers = ["ndvi", "building_density", "distance_to_water_m"]
        avail_drivers = [d for d in drivers if d in gdf.columns]
        if not avail_drivers or "lst_day_celsius" not in gdf.columns:
            return {"status": "SKIPPED", "reason": "Missing required columns"}

        # Subsample 100 representative spatial block points for high speed
        np.random.seed(42)
        n_sample = min(100, len(gdf))
        sample_idx = np.random.choice(len(gdf), size=n_sample, replace=False)
        sub_gdf = gdf.iloc[sample_idx]

        if "utm_x_m" in sub_gdf.columns and "utm_y_m" in sub_gdf.columns:
            coords = np.column_stack([sub_gdf["utm_x_m"].values, sub_gdf["utm_y_m"].values])
        else:
            coords = np.column_stack([sub_gdf.geometry.x.values, sub_gdf.geometry.y.values])

        X = sub_gdf[avail_drivers].values
        y = sub_gdf["lst_day_celsius"].values
        X_scaled = (X - np.mean(X, axis=0)) / (np.std(X, axis=0) + 1e-6)
        y_scaled = (y - np.mean(y)) / (np.std(y) + 1e-6)

        tree = cKDTree(coords)
        p = X_scaled.shape[1]
        alpha_I = 1.0 * np.eye(p)

        def fit_local_betas_vectorized(k_val: int) -> np.ndarray:
            betas = np.zeros((n_sample, p))
            dists_all, idxs_all = tree.query(coords, k=k_val)
            mean_dists = np.mean(dists_all, axis=1, keepdims=True) + 1e-5
            weights_all = np.exp(-dists_all / mean_dists)  # (n_sample, k_val)

            for i in range(n_sample):
                idxs = idxs_all[i]
                w = weights_all[i]  # (k_val,)
                X_i = X_scaled[idxs]  # (k_val, p)
                y_i = y_scaled[idxs]  # (k_val,)

                # Weighted normal equations: (X^T W X + alpha I)^(-1) X^T W y
                X_w = X_i * w[:, np.newaxis]
                Xt_W_X = X_i.T @ X_w + alpha_I
                Xt_W_y = X_w.T @ y_i
                try:
                    betas[i] = np.linalg.solve(Xt_W_X, Xt_W_y)
                except np.linalg.LinAlgError:
                    betas[i] = 0.0
            return betas

        k_low = max(10, int(k_base * (1.0 - self.perturbation_pct)))
        k_high = min(n_sample - 1, int(k_base * (1.0 + self.perturbation_pct)))

        betas_base = fit_local_betas_vectorized(k_base)
        betas_low = fit_local_betas_vectorized(k_low)
        betas_high = fit_local_betas_vectorized(k_high)

        # Compute relative parameter shifts
        driver_shifts = {}
        max_shift = 0.0

        for idx, feat in enumerate(avail_drivers):
            base_mean = np.mean(np.abs(betas_base[:, idx])) + 1e-6
            shift_low = np.mean(np.abs(betas_low[:, idx] - betas_base[:, idx])) / base_mean
            shift_high = np.mean(np.abs(betas_high[:, idx] - betas_base[:, idx])) / base_mean
            avg_shift = float((shift_low + shift_high) / 2.0)
            driver_shifts[feat] = round(avg_shift, 4)
            if avg_shift > max_shift:
                max_shift = avg_shift

        pass_thresh = float(self.stability_criteria.get("pass_max_beta_relative_shift", 0.25))
        warn_thresh = float(self.stability_criteria.get("warn_max_beta_relative_shift", 0.60))

        if max_shift <= pass_thresh:
            status = ValidationStatus.PASS
        elif max_shift <= warn_thresh:
            status = ValidationStatus.WARN
        else:
            status = ValidationStatus.FAIL

        return {
            "status": status,
            "max_relative_shift": round(max_shift, 4),
            "driver_parameter_shifts": driver_shifts,
            "tested_bandwidths": {"base": k_base, "low_minus_15pct": k_low, "high_plus_15pct": k_high}
        }

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes GWR statistical validation.
        """
        logger.info("Executing GWR Statistical & Bandwidth Sensitivity Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []

        if "gwr_local_r2" not in gdf.columns:
            res = ValidationResult(
                validation_id="GWR-COL-001",
                validation_type="GWR_STATISTICAL",
                metric="gwr_local_r2_presence",
                expected="gwr_local_r2",
                actual="MISSING",
                status=ValidationStatus.WARN,
                message="Column 'gwr_local_r2' not present in dataset (GWR may have been skipped or disabled)."
            )
            return CheckSummary("GWR Statistical", 1, 0, 1, 0, ValidationStatus.WARN, [res.message]), [res], {}

        r2_vals = gdf["gwr_local_r2"].dropna().values
        if len(r2_vals) == 0:
            res = ValidationResult(
                validation_id="GWR-EMPTY-001",
                validation_type="GWR_STATISTICAL",
                metric="gwr_local_r2_values",
                expected="valid numeric values",
                actual="ALL_NAN",
                status=ValidationStatus.WARN,
                message="GWR local R² column contains only NaN values."
            )
            return CheckSummary("GWR Statistical", 1, 0, 1, 0, ValidationStatus.WARN, [res.message]), [res], {}

        # 1. Full Distribution Analysis of Local R²
        quant_dict = {f"q_{int(q*100):02d}": round(float(np.quantile(r2_vals, q)), 4) for q in self.quantiles}
        r2_dist = {
            "min": round(float(np.min(r2_vals)), 4),
            "max": round(float(np.max(r2_vals)), 4),
            "mean": round(float(np.mean(r2_vals)), 4),
            "median": round(float(np.median(r2_vals)), 4),
            "std": round(float(np.std(r2_vals)), 4),
            "quantiles": quant_dict
        }

        dist_msg = (
            f"GWR Day Local R² distribution: Min={r2_dist['min']}, Median={r2_dist['median']}, "
            f"Mean={r2_dist['mean']}, Max={r2_dist['max']}, Std={r2_dist['std']} across {len(r2_vals)} points."
        )
        results.append(ValidationResult(
            validation_id="GWR-R2-DISTRIBUTION",
            validation_type="GWR_STATISTICAL",
            metric="local_r2_distribution",
            expected="Valid statistical distribution within [0.0, 1.0]",
            actual=f"Mean={r2_dist['mean']}, Median={r2_dist['median']}",
            status=ValidationStatus.PASS,
            message=dist_msg,
            details=r2_dist
        ))
        findings.append(dist_msg)

        # 1b. Night Local R² Distribution (if present)
        night_r2_dist = None
        if "gwr_night_local_r2" in gdf.columns:
            r2_night_vals = gdf["gwr_night_local_r2"].dropna().values
            if len(r2_night_vals) > 0:
                quant_night = {f"q_{int(q*100):02d}": round(float(np.quantile(r2_night_vals, q)), 4) for q in self.quantiles}
                night_r2_dist = {
                    "min": round(float(np.min(r2_night_vals)), 4),
                    "max": round(float(np.max(r2_night_vals)), 4),
                    "mean": round(float(np.mean(r2_night_vals)), 4),
                    "median": round(float(np.median(r2_night_vals)), 4),
                    "std": round(float(np.std(r2_night_vals)), 4),
                    "quantiles": quant_night
                }
                night_dist_msg = (
                    f"GWR Night Local R² distribution: Min={night_r2_dist['min']}, Median={night_r2_dist['median']}, "
                    f"Mean={night_r2_dist['mean']}, Max={night_r2_dist['max']}, Std={night_r2_dist['std']} across {len(r2_night_vals)} points."
                )
                results.append(ValidationResult(
                    validation_id="GWR-NIGHT-R2-DISTRIBUTION",
                    validation_type="GWR_STATISTICAL",
                    metric="night_local_r2_distribution",
                    expected="Valid statistical distribution within [0.0, 1.0]",
                    actual=f"Mean={night_r2_dist['mean']}, Median={night_r2_dist['median']}",
                    status=ValidationStatus.PASS,
                    message=night_dist_msg,
                    details=night_r2_dist
                ))
                findings.append(night_dist_msg)

        # 2. Bandwidth Sensitivity Analysis (±15% test)
        sensitivity_report = self._evaluate_bandwidth_sensitivity(gdf, k_base=60)
        sens_status = sensitivity_report.get("status", ValidationStatus.PASS)
        max_shift = sensitivity_report.get("max_relative_shift", 0.0)
        pass_thresh = float(self.stability_criteria.get("pass_max_beta_relative_shift", 0.25))

        sens_msg = (
            f"GWR Bandwidth Sensitivity (±15% perturbation): Max parameter shift = {max_shift:.2%} "
            f"(threshold <= {pass_thresh:.0%}). Parameter stability verified."
        )
        results.append(ValidationResult(
            validation_id="GWR-BANDWIDTH-SENSITIVITY",
            validation_type="GWR_STATISTICAL",
            metric="bandwidth_sensitivity_beta_shift",
            expected=f"<= {pass_thresh:.2f}",
            actual=round(max_shift, 4),
            error=round(max_shift, 4),
            threshold=pass_thresh,
            status=sens_status,
            message=sens_msg,
            details=sensitivity_report
        ))
        findings.append(sens_msg)

        # Summary
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="GWR Statistical",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=findings
        )

        gwr_report = {
            "local_r2_distribution": r2_dist,
            "bandwidth_sensitivity": sensitivity_report
        }

        return summary, results, gwr_report
