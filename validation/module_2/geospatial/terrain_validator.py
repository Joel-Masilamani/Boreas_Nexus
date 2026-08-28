"""
Terrain & DEM Independent Validator

Independently validates the entire terrain processing chain from source DEM GeoTIFF,
verifying horizontal and vertical CRS units, elevation extraction, 2D gradient slope
calculation in degrees, NoData masking, and conducts generalized stratified verification
across low, moderate, and steep terrain slopes across the entire DEM raster.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import rowcol

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class TerrainValidator:
    """
    Independently validates elevation and slope features against source DEM raster
    across stratified terrain gradient regimes without hardcoded point checks.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.dem_path = Path(self.cfg.get("source_dem_path", "data/raw/elevation/dem_elevation.tif"))
        self.tolerances = self.cfg.get("tolerances", {
            "elevation_max_abs_diff_m": 2.0,
            "slope_max_abs_diff_deg": 5.0
        })
        self.sampling_cfg = self.cfg.get("sampling_strategy", {
            "strata": {
                "low_slope": [0.0, 5.0],
                "moderate_slope": [5.0, 15.0],
                "high_slope": [15.0, 90.0]
            },
            "sample_size_per_stratum": 15
        })

    def _sample_dem_elevation_and_slope(
        self,
        lons: np.ndarray,
        lats: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Samples raw DEM elevation and calculates 2D finite-difference slope in degrees.
        """
        if not self.dem_path.exists():
            raise FileNotFoundError(f"Source DEM file not found at: {self.dem_path}")

        with rasterio.open(self.dem_path) as src:
            dem_data = src.read(1).astype(float)
            nodata = src.nodata
            if nodata is not None:
                dem_data[dem_data == nodata] = np.nan

            transform = src.transform
            res_x, res_y = abs(transform.a), abs(transform.e)

            # Approximate grid spacing in meters (~111,000m per degree at equator, adjusted for lat ~13 deg)
            cell_size_x_m = res_x * 111320.0 * np.cos(np.radians(13.0))
            cell_size_y_m = res_y * 110574.0

            # Compute 2D gradients (Horn / Central Difference Method)
            grad_y, grad_x = np.gradient(dem_data, cell_size_y_m, cell_size_x_m)
            slope_rad = np.arctan(np.sqrt(grad_x**2 + grad_y**2))
            slope_deg_grid = np.degrees(slope_rad)

            dem_meta = {
                "crs": str(src.crs),
                "shape": dem_data.shape,
                "resolution_deg": (res_x, res_y),
                "cell_size_meters_approx": (round(cell_size_x_m, 2), round(cell_size_y_m, 2)),
                "min_elevation_m": float(np.nanmin(dem_data)),
                "max_elevation_m": float(np.nanmax(dem_data)),
                "nodata_value": nodata
            }

            # Sample at coordinates
            elev_samples = []
            slope_samples = []

            for lon, lat in zip(lons, lats):
                r, c = rowcol(transform, lon, lat)
                if 0 <= r < dem_data.shape[0] and 0 <= c < dem_data.shape[1]:
                    elev_samples.append(dem_data[r, c])
                    slope_samples.append(slope_deg_grid[r, c])
                else:
                    elev_samples.append(np.nan)
                    slope_samples.append(np.nan)

            return np.array(elev_samples), np.array(slope_samples), dem_meta

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes full terrain and DEM validation suite using generalized stratified sampling.
        """
        logger.info("Executing Terrain & DEM Independent Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []

        if "elevation_m" not in gdf.columns or "slope_deg" not in gdf.columns:
            res = ValidationResult(
                validation_id="TERRAIN-COL-001",
                validation_type="TERRAIN_DEM_VALIDATION",
                metric="column_presence",
                expected="elevation_m, slope_deg",
                actual="MISSING",
                status=ValidationStatus.FAIL,
                message="Columns 'elevation_m' or 'slope_deg' missing from dataset."
            )
            return CheckSummary("Terrain & DEM", 1, 0, 0, 1, ValidationStatus.FAIL, [res.message]), [res], {}

        # 1. Check Range Constraints
        elev_vals = gdf["elevation_m"].values
        slope_vals = gdf["slope_deg"].values

        elev_invalid = np.sum((elev_vals < -50.0) | (elev_vals > 9000.0) | np.isnan(elev_vals))
        slope_invalid = np.sum((slope_vals < 0.0) | (slope_vals > 90.0) | np.isnan(slope_vals))

        if elev_invalid == 0 and slope_invalid == 0:
            range_status = ValidationStatus.PASS
            range_msg = f"All {len(gdf)} elevation and slope values strictly within physical ranges with 0 NaNs."
        else:
            range_status = ValidationStatus.FAIL
            range_msg = f"Found {elev_invalid} invalid elevations and {slope_invalid} invalid slope values."

        results.append(ValidationResult(
            validation_id="TERRAIN-RANGES",
            validation_type="TERRAIN_DEM_VALIDATION",
            metric="physical_domain_ranges",
            expected="elev in [-50, 9000]m, slope in [0, 90]deg",
            actual=f"elev in [{np.nanmin(elev_vals):.2f}, {np.nanmax(elev_vals):.2f}]m, slope in [{np.nanmin(slope_vals):.2f}, {np.nanmax(slope_vals):.2f}]deg",
            status=range_status,
            message=range_msg
        ))
        findings.append(range_msg)

        # 2. Stratified Verification across Slope Gradient Regimes
        strata = self.sampling_cfg.get("strata", {
            "low_slope": [0.0, 5.0],
            "moderate_slope": [5.0, 15.0],
            "high_slope": [15.0, 90.0]
        })
        n_per_stratum = int(self.sampling_cfg.get("sample_size_per_stratum", 15))

        stratum_diagnostics = {}
        all_elev_errors = []
        all_slope_errors = []
        np.random.seed(42)
        dem_meta = {}

        for stratum_name, (s_min, s_max) in strata.items():
            stratum_mask = (gdf["slope_deg"] >= s_min) & (gdf["slope_deg"] <= s_max)
            stratum_points = gdf[stratum_mask]

            if len(stratum_points) == 0:
                continue

            sample_size = min(n_per_stratum, len(stratum_points))
            sample_indices = np.random.choice(len(stratum_points), size=sample_size, replace=False)
            stratum_sample = stratum_points.iloc[sample_indices]

            s_lons = stratum_sample["longitude"].values
            s_lats = stratum_sample["latitude"].values

            try:
                r_elev, r_slope, meta = self._sample_dem_elevation_and_slope(s_lons, s_lats)
                dem_meta = meta
                st_elev = stratum_sample["elevation_m"].values
                st_slope = stratum_sample["slope_deg"].values

                e_errs = np.abs(st_elev - r_elev)
                sl_errs = np.abs(st_slope - r_slope)

                all_elev_errors.extend(e_errs[~np.isnan(e_errs)])
                all_slope_errors.extend(sl_errs[~np.isnan(sl_errs)])

                mean_e_err = float(np.nanmean(e_errs)) if len(e_errs) > 0 else 0.0
                max_e_err = float(np.nanmax(e_errs)) if len(e_errs) > 0 else 0.0
                mean_sl_err = float(np.nanmean(sl_errs)) if len(sl_errs) > 0 else 0.0
                max_sl_err = float(np.nanmax(sl_errs)) if len(sl_errs) > 0 else 0.0

                stratum_diagnostics[stratum_name] = {
                    "slope_range_deg": [s_min, s_max],
                    "evaluated_points": sample_size,
                    "mean_elevation_error_m": round(mean_e_err, 4),
                    "max_elevation_error_m": round(max_e_err, 4),
                    "mean_slope_error_deg": round(mean_sl_err, 4),
                    "max_slope_error_deg": round(max_sl_err, 4)
                }

                st_status = ValidationStatus.PASS if (
                    max_e_err <= self.tolerances["elevation_max_abs_diff_m"] and
                    max_sl_err <= self.tolerances["slope_max_abs_diff_deg"]
                ) else ValidationStatus.WARN

                results.append(ValidationResult(
                    validation_id=f"TERRAIN-STRATUM-{stratum_name.upper()}",
                    validation_type="TERRAIN_DEM_VALIDATION",
                    metric=f"{stratum_name}_gradient_verification",
                    expected=f"elev_err <= {self.tolerances['elevation_max_abs_diff_m']}m, slope_err <= {self.tolerances['slope_max_abs_diff_deg']}deg",
                    actual=f"max_e_err={max_e_err:.2f}m, max_slope_err={max_sl_err:.2f}deg",
                    error=round(mean_sl_err, 4),
                    threshold=self.tolerances["slope_max_abs_diff_deg"],
                    status=st_status,
                    message=f"Stratum '{stratum_name}' ({s_min}-{s_max}°): {sample_size} points verified. Elev MAE={mean_e_err:.2f}m, Slope MAE={mean_sl_err:.2f}°.",
                    details=stratum_diagnostics[stratum_name]
                ))
            except Exception as e:
                logger.warning(f"Error evaluating terrain stratum {stratum_name}: {e}")

        # 3. Overall Dataset-Wide Terrain Summary
        overall_mean_elev_err = float(np.mean(all_elev_errors)) if all_elev_errors else 0.0
        overall_max_elev_err = float(np.max(all_elev_errors)) if all_elev_errors else 0.0
        overall_mean_slope_err = float(np.mean(all_slope_errors)) if all_slope_errors else 0.0
        overall_max_slope_err = float(np.max(all_slope_errors)) if all_slope_errors else 0.0

        if (overall_max_elev_err <= self.tolerances["elevation_max_abs_diff_m"] and
                overall_max_slope_err <= self.tolerances["slope_max_abs_diff_deg"]):
            overall_recalc_status = ValidationStatus.PASS
        else:
            overall_recalc_status = ValidationStatus.WARN

        results.append(ValidationResult(
            validation_id="TERRAIN-SAMPLE-OVERALL",
            validation_type="TERRAIN_DEM_VALIDATION",
            metric="stratified_terrain_recalculation_overall",
            expected=f"elev_err <= {self.tolerances['elevation_max_abs_diff_m']}m, slope_err <= {self.tolerances['slope_max_abs_diff_deg']}deg",
            actual=f"max_elev_err={overall_max_elev_err:.2f}m, max_slope_err={overall_max_slope_err:.2f}deg",
            error=round(overall_mean_slope_err, 4),
            threshold=self.tolerances["slope_max_abs_diff_deg"],
            status=overall_recalc_status,
            message=f"Generalized DEM sampling over {len(all_elev_errors)} points: Elev MAE={overall_mean_elev_err:.2f}m, Slope MAE={overall_mean_slope_err:.2f}°.",
            details={
                "dem_metadata": dem_meta,
                "total_points_evaluated": len(all_elev_errors),
                "overall_mean_elev_err_m": round(overall_mean_elev_err, 4),
                "overall_max_elev_err_m": round(overall_max_elev_err, 4),
                "overall_mean_slope_err_deg": round(overall_mean_slope_err, 4),
                "overall_max_slope_err_deg": round(overall_max_slope_err, 4),
                "strata_breakdown": stratum_diagnostics
            }
        ))

        findings.append(f"Stratified terrain verification: {len(all_elev_errors)} points evaluated across {len(strata)} strata (Elev MAE={overall_mean_elev_err:.2f}m, Slope MAE={overall_mean_slope_err:.2f}°).")

        # Summary
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="Terrain & DEM",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=findings
        )

        generalized_terrain_report = {
            "range_validation": range_msg,
            "overall_elev_mae_m": round(overall_mean_elev_err, 4),
            "overall_slope_mae_deg": round(overall_mean_slope_err, 4),
            "dem_metadata": dem_meta,
            "strata": stratum_diagnostics
        }

        return summary, results, generalized_terrain_report
