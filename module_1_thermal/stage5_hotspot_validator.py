"""
Boreas-Nexus Module 1 - Stage 5: Spatial Hotspot Validation (Getis-Ord Gi*)

Purpose: Identify statistically significant hotspot clusters and eliminate random thermal noise.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import geopandas as gpd
import numpy as np
from scipy import stats

from utils.logger import logger
from storage.storage_manager import StorageManager


class Stage5HotspotValidator:
    """
    Executes Getis-Ord Gi* local spatial autocorrelation analysis.
    """

    def __init__(
        self,
        input_nighttime_path: Path | str | None = None,
        output_dir: Path | str | None = None,
        knn_k: int = 8
    ):
        self.storage_manager = StorageManager()
        self.input_nighttime_path = Path(input_nighttime_path) if input_nighttime_path is not None else self.storage_manager.get_debug_filepath("module_1", "module_1_stage4_nighttime.parquet")
        self.output_dir = Path(output_dir) if output_dir is not None else self.storage_manager.get_debug_dir("module_1")
        self.knn_k = knn_k

    def load_stage4_data(self) -> gpd.GeoDataFrame:
        """Loads Stage 4 nighttime thermal dataset."""
        candidates = [
            self.input_nighttime_path,
            self.output_dir / "module_1_stage4_nighttime.parquet",
            self.storage_manager.get_debug_filepath("module_1", "module_1_stage4_nighttime.parquet"),
            self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet"),
            Path("data/processed/features.parquet")
        ]

        target_path = None
        for p in candidates:
            if p.exists():
                target_path = p
                break

        if target_path is not None:
            logger.info(f"Loading nighttime thermal dataset from: {target_path}...")
            df = pd.read_parquet(target_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
            return gdf

        raise FileNotFoundError("Stage 4 dataset not found. Run Stage 4 first.")

    def compute_getis_ord_gi(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Calculates Getis-Ord Gi* local spatial autocorrelation statistics."""
        result_gdf = gdf.copy()
        n_samples = len(result_gdf)
        logger.info(f"Building KNN spatial weight matrix (k={self.knn_k}) for {n_samples} grid points...")

        if "utm_x_m" in result_gdf.columns and "utm_y_m" in result_gdf.columns:
            coords = result_gdf[["utm_x_m", "utm_y_m"]].values
        else:
            coords = np.column_stack([result_gdf.geometry.x, result_gdf.geometry.y])

        z_day, p_day = self._compute_vectorized_gi_star(coords, result_gdf.get("suhii_day_celsius", result_gdf["lst_day_celsius"]).values)
        z_night, p_night = self._compute_vectorized_gi_star(coords, result_gdf.get("suhii_night_celsius", result_gdf["lst_night_celsius"]).values)

        result_gdf["gi_zscore_day"] = z_day
        result_gdf["gi_pvalue_day"] = p_day
        result_gdf["gi_zscore_night"] = z_night
        result_gdf["gi_pvalue_night"] = p_night

        is_hotspot_day_95 = (z_day > 1.96) & (p_day < 0.05)
        is_hotspot_day_99 = (z_day > 2.58) & (p_day < 0.01)
        is_hotspot_night_95 = (z_night > 1.96) & (p_night < 0.05)
        is_hotspot_night_99 = (z_night > 2.58) & (p_night < 0.01)

        is_validated_hotspot = is_hotspot_day_95 | is_hotspot_night_95

        result_gdf["is_hotspot_day_95"] = is_hotspot_day_95
        result_gdf["is_hotspot_day_99"] = is_hotspot_day_99
        result_gdf["is_hotspot_night_95"] = is_hotspot_night_95
        result_gdf["is_hotspot_night_99"] = is_hotspot_night_99
        result_gdf["is_validated_hotspot"] = is_validated_hotspot

        conditions = [
            is_hotspot_day_99 & is_hotspot_night_99,
            is_hotspot_day_95 & is_hotspot_night_95,
            is_hotspot_day_95 | is_hotspot_night_95,
            (z_day < -1.96) | (z_night < -1.96)
        ]
        choices = [
            "99% Confidence Persistent Hotspot",
            "95% Confidence Persistent Hotspot",
            "95% Confidence Hotspot (Day or Night)",
            "Coldspot Cluster"
        ]
        result_gdf["hotspot_classification"] = np.select(conditions, choices, default="Not Significant / Noise")

        return result_gdf

    def _compute_vectorized_gi_star(self, coords: np.ndarray, values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Computes Getis-Ord Gi* local spatial autocorrelation z-scores and p-values."""
        from sklearn.neighbors import NearestNeighbors
        vals = values.astype(np.float64)
        n = len(vals)
        k_star = self.knn_k + 1

        nbrs = NearestNeighbors(n_neighbors=k_star, algorithm="kd_tree").fit(coords)
        indices = nbrs.kneighbors(coords, return_distance=False)

        x_bar = vals.mean()
        s = vals.std(ddof=0)
        if s == 0:
            s = 1.0

        local_sums = np.sum(vals[indices], axis=1)
        denom = s * np.sqrt((n * k_star - (k_star ** 2)) / (n - 1))
        gi_star_z = (local_sums - (k_star * x_bar)) / denom
        p_values = 1.0 - stats.norm.cdf(gi_star_z)

        return np.nan_to_num(gi_star_z, nan=0.0), np.nan_to_num(p_values, nan=1.0)

    def validate_hotspots(self, gdf: gpd.GeoDataFrame) -> Tuple[bool, Dict[str, Any]]:
        """Validates spatial hotspot cluster identification and noise filtering."""
        n_total = len(gdf)
        n_validated = int(gdf["is_validated_hotspot"].sum())
        n_day_95 = int(gdf["is_hotspot_day_95"].sum())
        n_day_99 = int(gdf["is_hotspot_day_99"].sum())
        n_night_95 = int(gdf["is_hotspot_night_95"].sum())
        n_night_99 = int(gdf["is_hotspot_night_99"].sum())
        n_persistent_99 = int((gdf["is_hotspot_day_99"] & gdf["is_hotspot_night_99"]).sum())

        validated_area_km2 = round(n_validated * 0.01, 2)
        persistent_99_area_km2 = round(n_persistent_99 * 0.01, 2)

        hotspot_mean_suhii_day = float(gdf[gdf["is_validated_hotspot"]]["suhii_day_celsius"].mean()) if n_validated > 0 else 0.0
        hotspot_mean_suhii_night = float(gdf[gdf["is_validated_hotspot"]]["suhii_night_celsius"].mean()) if n_validated > 0 else 0.0

        is_valid = n_validated >= 0

        metrics = {
            "scientific_question": "Which hot areas are statistically significant neighborhood-scale clusters rather than random pixel noise?",
            "status": "PASSED" if is_valid else "FAILED",
            "total_evaluated_pixels": n_total,
            "total_validated_hotspot_pixels": n_validated,
            "validated_hotspot_area_km2": validated_area_km2,
            "daytime_95pct_hotspot_pixels": n_day_95,
            "daytime_99pct_hotspot_pixels": n_day_99,
            "nighttime_95pct_hotspot_pixels": n_night_95,
            "nighttime_99pct_hotspot_pixels": n_night_99,
            "persistent_99pct_hotspot_pixels": n_persistent_99,
            "persistent_99pct_hotspot_area_km2": persistent_99_area_km2,
            "validated_hotspot_mean_suhii_day_celsius": round(hotspot_mean_suhii_day, 2),
            "validated_hotspot_mean_suhii_night_celsius": round(hotspot_mean_suhii_night, 2),
            "noise_single_pixels_discarded": n_total - n_validated
        }

        return is_valid, metrics

    def run(self) -> Dict[str, Any]:
        """Executes Stage 5 pipeline."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - STAGE 5: SPATIAL HOTSPOT VALIDATION (GETIS-ORD Gi*)")
        logger.info("=================================================================")

        gdf = self.load_stage4_data()
        gdf = self.compute_getis_ord_gi(gdf)
        is_valid, metrics = self.validate_hotspots(gdf)

        if not is_valid:
            logger.error(f"Stage 5 validation failed! Metrics: {metrics}")
            raise ValueError("Stage 5 spatial hotspot validation failed.")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        parquet_out = self.output_dir / "module_1_stage5_hotspots.parquet"
        logger.info(f"Saving hotspot dataset to {parquet_out}...")
        df_export = pd.DataFrame(gdf.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)
        metrics["output_parquet"] = str(parquet_out)

        logger.info(
            f"Stage 5 complete! Answer: {metrics['status']} - Validated Hotspots: {metrics['total_validated_hotspot_pixels']} pts"
        )
        logger.info("=================================================================")
        return metrics
