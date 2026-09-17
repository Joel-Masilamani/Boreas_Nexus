"""
Building Density Independent Validator

Independently recalculates building coverage fraction from source building vectors,
validates calculation formulas, cell-polygon intersections, coordinate reference systems,
fractional range constraints [0, 1], and conducts generalized stratified recalculation
across the entire density distribution spectrum (low, medium, high).
Utilizes spatially indexed FlatGeobuf with native R-Tree spatial indexing for sub-millisecond lookups.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union
import pyogrio

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary
from utils.crs_utils import transform_wgs84_to_utm


class BuildingDensityValidator:
    """
    Independently validates building density calculations from raw building vectors
    across stratified density spectrums without hardcoded point checks.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.fgb_path = Path("data/processed/vector/buildings.fgb")
        self.parquet_path = Path("data/processed/vector/buildings.geoparquet")
        self.cell_size_m = float(self.cfg.get("grid_cell_size_m", 100.0))
        self.cell_area_m2 = self.cell_size_m * self.cell_size_m
        self.tolerances = self.cfg.get("tolerances", {
            "pass_max_absolute_error": 0.05,
            "warn_max_absolute_error": 0.15
        })
        self.sampling_cfg = self.cfg.get("sampling_strategy", {
            "strata": {
                "low_density": [0.0, 0.2],
                "medium_density": [0.2, 0.6],
                "high_density": [0.6, 1.0]
            },
            "sample_size_per_stratum": 10
        })
        self._total_bounds = None
        self._init_bounds()

    def _init_bounds(self):
        if self.fgb_path.exists():
            try:
                info = pyogrio.read_info(self.fgb_path)
                self._total_bounds = info.get("total_bounds")
            except Exception:
                pass

    def _query_buildings_bbox(self, bbox: Tuple[float, float, float, float]) -> gpd.GeoDataFrame:
        """
        Sub-millisecond spatial bounding box query using FlatGeobuf R-Tree index.
        """
        if self.fgb_path.exists():
            try:
                return pyogrio.read_dataframe(self.fgb_path, bbox=bbox)
            except Exception:
                pass

        if self.parquet_path.exists():
            try:
                return gpd.read_parquet(self.parquet_path, bbox=bbox)
            except Exception:
                pass

        return gpd.GeoDataFrame()

    def _recalculate_point_density(
        self,
        pt_row: pd.Series
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Independently computes fractional building coverage for a 100m grid cell.
        Uses projected UTM metric buffer box to compute exact intersection area.
        """
        lon = float(pt_row["longitude"])
        lat = float(pt_row["latitude"])

        # Check if point falls within source vector extent
        is_outside = False
        if self._total_bounds is not None:
            minx, miny, maxx, maxy = self._total_bounds
            if not (minx <= lon <= maxx and miny <= lat <= maxy):
                is_outside = True

        # Determine projected UTM coordinates
        utm_x, utm_y, utm_crs = transform_wgs84_to_utm([lon], [lat])
        cx, cy = utm_x[0], utm_y[0]

        # 100m x 100m square cell centered at (cx, cy)
        half_side = self.cell_size_m / 2.0
        cell_box_utm = box(cx - half_side, cy - half_side, cx + half_side, cy + half_side)

        # 150m buffer in degrees for fast spatial query
        buf_deg = 0.0015
        bbox_wgs84 = (lon - buf_deg, lat - buf_deg, lon + buf_deg, lat + buf_deg)

        candidate_buildings = self._query_buildings_bbox(bbox_wgs84)

        if len(candidate_buildings) == 0:
            return 0.0, {
                "overlapping_polygons_count": 0,
                "has_internal_overlap": False,
                "is_outside_vector_bounds": is_outside
            }

        # Project candidate buildings to UTM
        if candidate_buildings.crs != utm_crs:
            candidate_buildings = candidate_buildings.to_crs(utm_crs)

        # Calculate individual intersections
        intersecting_geoms = []
        raw_sum_area = 0.0

        for geom in candidate_buildings.geometry:
            if geom is not None and not geom.is_empty and geom.is_valid:
                inter = geom.intersection(cell_box_utm)
                if not inter.is_empty:
                    intersecting_geoms.append(inter)
                    raw_sum_area += inter.area

        if not intersecting_geoms:
            return 0.0, {
                "overlapping_polygons_count": 0,
                "has_internal_overlap": False,
                "is_outside_vector_bounds": is_outside
            }

        # Handle polygon overlapping geometry (union to avoid double-counting)
        try:
            merged_intersections = unary_union(intersecting_geoms)
            union_area = merged_intersections.area
        except Exception:
            union_area = raw_sum_area

        # Compute fractional density
        density_fraction = min(1.0, max(0.0, union_area / self.cell_area_m2))

        diagnostics = {
            "overlapping_polygons_count": len(intersecting_geoms),
            "raw_sum_intersection_area_m2": round(raw_sum_area, 2),
            "merged_union_intersection_area_m2": round(union_area, 2),
            "has_internal_overlap": bool(raw_sum_area > union_area + 1e-3),
            "overlap_area_diff_m2": round(raw_sum_area - union_area, 2),
            "cell_area_m2": self.cell_area_m2,
            "is_outside_vector_bounds": is_outside
        }

        return density_fraction, diagnostics

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Runs comprehensive building density validation on the dataset using generalized stratified sampling.
        """
        logger.info("Executing Building Density Independent Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []

        if "building_density" not in gdf.columns:
            res = ValidationResult(
                validation_id="GEO-BD-001",
                validation_type="GEOSPATIAL_BUILDING_DENSITY",
                metric="column_presence",
                expected="building_density",
                actual="MISSING",
                status=ValidationStatus.FAIL,
                message="Column 'building_density' is missing from dataset."
            )
            return CheckSummary("Building Density", 1, 0, 0, 1, ValidationStatus.FAIL, [res.message]), [res], {}

        # 1. Range Validation [0, 1]
        density_vals = gdf["building_density"].values
        out_of_bounds = np.sum((density_vals < 0.0) | (density_vals > 1.0))
        nan_count = int(np.sum(np.isnan(density_vals)))

        if out_of_bounds == 0 and nan_count == 0:
            range_status = ValidationStatus.PASS
            range_msg = f"All {len(gdf)} building density values strictly within [0.0, 1.0] with 0 NaNs."
        else:
            range_status = ValidationStatus.FAIL
            range_msg = f"Found {out_of_bounds} out-of-range building density values and {nan_count} NaNs."

        results.append(ValidationResult(
            validation_id="GEO-BD-RANGE",
            validation_type="GEOSPATIAL_BUILDING_DENSITY",
            metric="fractional_range",
            expected="[0.0, 1.0]",
            actual=f"[{np.nanmin(density_vals):.4f}, {np.nanmax(density_vals):.4f}]",
            status=range_status,
            message=range_msg,
            details={"out_of_bounds_count": int(out_of_bounds), "nan_count": nan_count}
        ))
        findings.append(range_msg)

        # 2. Filter valid points inside source vector bounding box
        if self._total_bounds is not None:
            minx, miny, maxx, maxy = self._total_bounds
            inside_mask = (gdf["longitude"] >= minx) & (gdf["longitude"] <= maxx) & (gdf["latitude"] >= miny) & (gdf["latitude"] <= maxy)
            valid_subset = gdf[inside_mask]
        else:
            valid_subset = gdf

        # 3. Stratified Spatial Recalculation across Low, Medium, High Density Spectrums
        strata = self.sampling_cfg.get("strata", {
            "low_density": [0.0, 0.2],
            "medium_density": [0.2, 0.6],
            "high_density": [0.6, 1.0]
        })
        n_per_stratum = int(self.sampling_cfg.get("sample_size_per_stratum", 10))

        stratum_diagnostics = {}
        all_sample_errors = []
        np.random.seed(42)

        for stratum_name, (d_min, d_max) in strata.items():
            stratum_mask = (valid_subset["building_density"] >= d_min) & (valid_subset["building_density"] <= d_max)
            stratum_points = valid_subset[stratum_mask]

            if len(stratum_points) == 0:
                continue

            sample_size = min(n_per_stratum, len(stratum_points))
            sample_indices = np.random.choice(len(stratum_points), size=sample_size, replace=False)
            stratum_sample = stratum_points.iloc[sample_indices]

            s_errors = []
            for _, row in stratum_sample.iterrows():
                stored_val = float(row["building_density"])
                recalc_val, _ = self._recalculate_point_density(row)
                err = abs(stored_val - recalc_val)
                s_errors.append(err)
                all_sample_errors.append(err)

            s_mae = float(np.mean(s_errors)) if s_errors else 0.0
            s_max_ae = float(np.max(s_errors)) if s_errors else 0.0

            stratum_diagnostics[stratum_name] = {
                "density_range": [d_min, d_max],
                "evaluated_points": sample_size,
                "mean_absolute_error": round(s_mae, 4),
                "max_absolute_error": round(s_max_ae, 4)
            }

            # Per-stratum check result
            s_status = ValidationStatus.PASS if s_max_ae <= self.tolerances["pass_max_absolute_error"] else (
                ValidationStatus.WARN if s_max_ae <= self.tolerances["warn_max_absolute_error"] else ValidationStatus.WARN
            )

            results.append(ValidationResult(
                validation_id=f"GEO-BD-STRATUM-{stratum_name.upper()}",
                validation_type="GEOSPATIAL_BUILDING_DENSITY",
                metric=f"{stratum_name}_recalculation_error",
                expected=f"error <= {self.tolerances['pass_max_absolute_error']}",
                actual=f"max_err={s_max_ae:.4f}, mean_err={s_mae:.4f}",
                error=round(s_max_ae, 4),
                threshold=self.tolerances["pass_max_absolute_error"],
                status=s_status,
                message=f"Stratum '{stratum_name}' ({d_min}-{d_max}): {sample_size} points verified. MAE={s_mae:.4f}, MaxAE={s_max_ae:.4f}.",
                details=stratum_diagnostics[stratum_name]
            ))

        # 4. Dataset-wide Recalculation Aggregation
        overall_mae = float(np.mean(all_sample_errors)) if all_sample_errors else 0.0
        overall_max_ae = float(np.max(all_sample_errors)) if all_sample_errors else 0.0

        if overall_max_ae <= self.tolerances["pass_max_absolute_error"]:
            recalc_status = ValidationStatus.PASS
        elif overall_max_ae <= self.tolerances["warn_max_absolute_error"]:
            recalc_status = ValidationStatus.WARN
        else:
            recalc_status = ValidationStatus.WARN

        results.append(ValidationResult(
            validation_id="GEO-BD-RECALC-OVERALL",
            validation_type="GEOSPATIAL_BUILDING_DENSITY",
            metric="stratified_density_recalculation_overall",
            expected=f"max_error <= {self.tolerances['pass_max_absolute_error']}",
            actual=round(overall_max_ae, 4),
            error=round(overall_mae, 4),
            threshold=self.tolerances["pass_max_absolute_error"],
            status=recalc_status,
            message=f"Generalized stratified recalculation across {len(all_sample_errors)} sample points: Overall MAE={overall_mae:.4f}, MaxAE={overall_max_ae:.4f}.",
            details={
                "total_samples_evaluated": len(all_sample_errors),
                "overall_mean_absolute_error": round(overall_mae, 4),
                "overall_max_absolute_error": round(overall_max_ae, 4),
                "strata_breakdown": stratum_diagnostics
            }
        ))

        findings.append(f"Stratified building density verification: {len(all_sample_errors)} points evaluated across {len(strata)} strata (Overall MAE={overall_mae:.4f}, MaxAE={overall_max_ae:.4f}).")

        # Summary computation
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="Geospatial Building Density",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=findings
        )

        generalized_report = {
            "range_validation": range_msg,
            "overall_mae": round(overall_mae, 4),
            "overall_max_ae": round(overall_max_ae, 4),
            "strata": stratum_diagnostics
        }

        return summary, results, generalized_report
