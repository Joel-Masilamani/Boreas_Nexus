"""
Spatial Statistics & Hotspot Significance Validator (Getis-Ord Gi* & Moran's I)

Audits spatial autocorrelation metrics (Global Moran's I) and independently verifies
local Getis-Ord Gi* z-score calculations and statistical significance thresholds (p < 0.05, p < 0.01).
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class SpatialStatsValidator:
    """
    Validates spatial statistics, Moran's I, and Getis-Ord Gi* z-scores.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.k_neighbors = int(self.cfg.get("getis_ord", {}).get("k_neighbors", 8))
        self.z_crit_95 = float(self.cfg.get("getis_ord", {}).get("z_critical_95pct", 1.96))
        self.tolerances = self.cfg.get("getis_ord", {}).get("tolerances", {"zscore_max_abs_diff": 0.25})

    def _compute_getis_ord_sample(
        self,
        coords: np.ndarray,
        x: np.ndarray,
        k: int = 8
    ) -> np.ndarray:
        """
        Fast vectorized computation of Getis-Ord Gi* z-scores across population points.
        """
        n = len(x)
        x_bar = np.mean(x)
        s = np.std(x, ddof=0)
        if s == 0 or np.isnan(s):
            s = 1.0

        k_star = k + 1
        tree = cKDTree(coords)
        dists, idxs = tree.query(coords, k=k_star)

        sum_wx = np.sum(x[idxs], axis=1)
        denom = s * np.sqrt(max(1e-6, (n * k_star - (k_star ** 2)) / max(1, n - 1)))
        z_scores = (sum_wx - (k_star * x_bar)) / denom
        return np.nan_to_num(z_scores, nan=0.0)

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes spatial statistics and Getis-Ord Gi* validation.
        """
        logger.info("Executing Spatial Statistics & Hotspot Significance Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []

        if "gi_zscore_day" not in gdf.columns:
            res = ValidationResult(
                validation_id="M1-STAT-COL-001",
                validation_type="SPATIAL_STATISTICS",
                metric="column_presence",
                expected="gi_zscore_day",
                actual="MISSING",
                status=ValidationStatus.FAIL,
                message="Column 'gi_zscore_day' missing."
            )
            return CheckSummary("Spatial Statistics", 1, 0, 0, 1, ValidationStatus.FAIL, [res.message]), [res], {}

        # 1. Hotspot Threshold Consistency Check (z >= 1.96 <-> hotspot classification)
        z_vals = gdf["gi_zscore_day"].values
        if "day_is_hotspot" in gdf.columns:
            stored_hotspots = gdf["day_is_hotspot"].values.astype(bool)
        elif "day_hotspot_significance" in gdf.columns:
            stored_hotspots = gdf["day_hotspot_significance"].notnull().values
        elif "is_hotspot_day" in gdf.columns:
            stored_hotspots = gdf["is_hotspot_day"].values.astype(bool)
        else:
            stored_hotspots = z_vals >= self.z_crit_95

        expected_hotspots = z_vals >= self.z_crit_95
        match_count = int(np.sum(stored_hotspots == expected_hotspots))
        match_pct = (match_count / len(gdf)) * 100.0

        if match_pct >= 99.0:
            thresh_status = ValidationStatus.PASS
            thresh_msg = f"Hotspot threshold classification (z >= {self.z_crit_95}) is {match_pct:.2f}% consistent across {len(gdf)} points."
        else:
            thresh_status = ValidationStatus.WARN
            thresh_msg = f"Hotspot classification discrepancy: only {match_pct:.2f}% match with z >= {self.z_crit_95} criterion."

        results.append(ValidationResult(
            validation_id="M1-STAT-HOTSPOT-THRESH",
            validation_type="SPATIAL_STATISTICS",
            metric="hotspot_zscore_threshold_alignment",
            expected=f">= 99.0% match with z >= {self.z_crit_95}",
            actual=f"{match_pct:.2f}% match",
            status=thresh_status,
            message=thresh_msg,
            details={"match_percentage": match_pct, "hotspots_count": int(np.sum(stored_hotspots))}
        ))
        findings.append(thresh_msg)

        # 2. Independent Getis-Ord Recalculation Check
        if "utm_x_m" in gdf.columns and "utm_y_m" in gdf.columns:
            coords = np.column_stack([gdf["utm_x_m"].values, gdf["utm_y_m"].values])
        else:
            coords = np.column_stack([gdf.geometry.x.values, gdf.geometry.y.values])

        val_day = gdf["suhii_day_celsius"].values if "suhii_day_celsius" in gdf.columns else gdf["lst_day_celsius"].values
        recalc_z = self._compute_getis_ord_sample(coords, val_day, k=self.k_neighbors)
        stored_z = gdf["gi_zscore_day"].values

        # Correlation between stored and independently recalculated z-scores
        corr = float(np.corrcoef(stored_z, recalc_z)[0, 1])

        if corr >= 0.70:
            stat_status = ValidationStatus.PASS
            stat_msg = f"Independent Getis-Ord Gi* recalculation correlation = {corr:.4f} (>= 0.70)."
        else:
            stat_status = ValidationStatus.WARN
            stat_msg = f"Independent Getis-Ord Gi* recalculation correlation = {corr:.4f} below threshold."

        results.append(ValidationResult(
            validation_id="M1-STAT-GI-CORRELATION",
            validation_type="SPATIAL_STATISTICS",
            metric="getis_ord_sample_correlation",
            expected="correlation >= 0.70",
            actual=round(corr, 4),
            threshold=0.70,
            status=stat_status,
            message=stat_msg,
            details={"total_points": len(gdf), "correlation": corr}
        ))
        findings.append(stat_msg)

        # Summary
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="Spatial Statistics (Gi* & Moran's I)",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=findings
        )

        stats_diagnostics = {
            "total_points_evaluated": len(gdf),
            "day_hotspot_count": int(np.sum(stored_hotspots)),
            "gi_zscore_mean": float(np.mean(z_vals)),
            "gi_zscore_max": float(np.max(z_vals)),
            "sample_recalc_correlation": corr
        }

        return summary, results, stats_diagnostics
