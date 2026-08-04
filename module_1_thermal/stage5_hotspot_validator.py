"""
Boreas-Nexus Module 1 - Stage 5: Spatial Hotspot Validation (Getis-Ord Gi*)

Purpose: Identify statistically significant hotspot clusters and eliminate random thermal noise.

Scientific Theory: An Urban Heat Hotspot is not a single isolated hot pixel.
It is a statistically significant spatial cluster of consistently high temperatures surrounded by
other high-temperature neighbors.

Method: Apply the Getis-Ord Gi* local spatial autocorrelation algorithm via PySAL (esda.getisord.G_Local).
Evaluate pixel i and its spatial neighbors j within a spatial weight matrix W.

Decision: Only clusters with statistically significant high Z-scores (Z > +1.96, p < 0.05) are validated
as true hotspots. Isolated noisy single hot pixels are discarded.

Scientific Question: "Which hot areas are statistically significant neighborhood-scale clusters rather than random pixel noise?"
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import geopandas as gpd
import numpy as np
from scipy import stats

from utils.logger import logger


class Stage5HotspotValidator:
    """
    Executes Getis-Ord Gi* local spatial autocorrelation analysis to identify
    statistically significant urban heat hotspot clusters (Z > +1.96, p < 0.05)
    and filter out isolated single-pixel thermal noise.
    """

    def __init__(
        self,
        input_nighttime_path: Path | str = Path("data/processed/module_1_stage4_nighttime.parquet"),
        output_dir: Path | str = Path("data/processed"),
        knn_k: int = 8
    ):
        self.input_nighttime_path = Path(input_nighttime_path)
        self.output_dir = Path(output_dir)
        self.knn_k = knn_k

    def load_stage4_data(self) -> gpd.GeoDataFrame:
        """Loads Stage 4 nighttime thermal dataset."""
        if self.input_nighttime_path.exists():
            logger.info(f"Loading Stage 4 dataset from Parquet: {self.input_nighttime_path}...")
            df = pd.read_parquet(self.input_nighttime_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
        else:
            geojson_path = self.input_nighttime_path.with_suffix(".geojson")
            if geojson_path.exists():
                logger.info(f"Loading Stage 4 dataset from GeoJSON: {geojson_path}...")
                gdf = gpd.read_file(geojson_path)
            else:
                raise FileNotFoundError(
                    f"Stage 4 dataset not found at {self.input_nighttime_path}. Run Stage 4 first."
                )

        return gdf

    def compute_getis_ord_gi(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Calculates Getis-Ord Gi* local spatial autocorrelation statistics for Daytime and Nighttime SUHII.
        """
        result_gdf = gdf.copy()
        n_samples = len(result_gdf)
        logger.info(f"Building KNN spatial weight matrix (k={self.knn_k}) for {n_samples} grid points...")

        # Extract coordinates for spatial weight matrix
        if "utm_x_m" in result_gdf.columns and "utm_y_m" in result_gdf.columns:
            coords = result_gdf[["utm_x_m", "utm_y_m"]].values
        else:
            coords = np.column_stack([result_gdf.geometry.x, result_gdf.geometry.y])

        # Compute vectorized Getis-Ord Gi*
        z_day, p_day = self._compute_vectorized_gi_star(coords, result_gdf.get("suhii_day_celsius", result_gdf["lst_day_celsius"]).values)
        z_night, p_night = self._compute_vectorized_gi_star(coords, result_gdf.get("suhii_night_celsius", result_gdf["lst_night_celsius"]).values)

        result_gdf["gi_zscore_day"] = z_day
        result_gdf["gi_pvalue_day"] = p_day
        result_gdf["gi_zscore_night"] = z_night
        result_gdf["gi_pvalue_night"] = p_night

        # Hotspot validation flags
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

        # Assign confidence classification
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
        """
        Computes Getis-Ord Gi* local spatial autocorrelation z-scores and p-values
        using fast spatial k-nearest neighbors.
        """
        from sklearn.neighbors import NearestNeighbors
        vals = values.astype(np.float64)
        n = len(vals)
        k_star = self.knn_k + 1  # includes self observation i

        # Fit nearest neighbors including self
        nbrs = NearestNeighbors(n_neighbors=k_star, algorithm="kd_tree").fit(coords)
        indices = nbrs.kneighbors(coords, return_distance=False)

        x_bar = vals.mean()
        s = vals.std(ddof=0)
        if s == 0:
            s = 1.0

        # Local sums over neighborhood
        local_sums = np.sum(vals[indices], axis=1)

        # Getis-Ord Gi* formula
        # Gi* = (Local_Sum - k_star * x_bar) / (S * sqrt((n * k_star - k_star^2) / (n - 1)))
        denom = s * np.sqrt((n * k_star - (k_star ** 2)) / (n - 1))
        gi_star_z = (local_sums - (k_star * x_bar)) / denom
        
        # 1-tailed p-value for positive hotspot z-scores
        p_values = 1.0 - stats.norm.cdf(gi_star_z)

        return np.nan_to_num(gi_star_z, nan=0.0), np.nan_to_num(p_values, nan=1.0)

    def validate_hotspots(self, gdf: gpd.GeoDataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates spatial hotspot cluster identification and noise filtering.

        Answers Scientific Question:
        "Which hot areas are statistically significant neighborhood-scale clusters rather than random pixel noise?"
        """
        n_total = len(gdf)
        n_validated = int(gdf["is_validated_hotspot"].sum())
        n_day_95 = int(gdf["is_hotspot_day_95"].sum())
        n_day_99 = int(gdf["is_hotspot_day_99"].sum())
        n_night_95 = int(gdf["is_hotspot_night_95"].sum())
        n_night_99 = int(gdf["is_hotspot_night_99"].sum())
        n_persistent_99 = int((gdf["is_hotspot_day_99"] & gdf["is_hotspot_night_99"]).sum())

        # Area calculation (1 point = 0.01 km^2 at 100m res)
        validated_area_km2 = round(n_validated * 0.01, 2)
        persistent_99_area_km2 = round(n_persistent_99 * 0.01, 2)

        # Average SUHII in validated hotspots
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
        """Executes Stage 5 pipeline and exports hotspot validation dataset."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - STAGE 5: SPATIAL HOTSPOT VALIDATION (GETIS-ORD Gi*)")
        logger.info("=================================================================")

        # Step 1: Load Stage 4 dataset
        gdf = self.load_stage4_data()

        # Step 2: Compute Getis-Ord Gi* local autocorrelation
        gdf = self.compute_getis_ord_gi(gdf)

        # Step 3: Validate hotspot clusters
        is_valid, metrics = self.validate_hotspots(gdf)
        if not is_valid:
            logger.error(f"Stage 5 validation failed! Metrics: {metrics}")
            raise ValueError("Stage 5 spatial hotspot validation failed.")

        # Step 4: Export outputs (Parquet for fast stage auditing)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        parquet_out = self.output_dir / "module_1_stage5_hotspots.parquet"

        logger.info(f"Saving hotspot dataset ({len(gdf)} points) to {parquet_out}...")
        df_export = pd.DataFrame(gdf.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)

        metrics["output_parquet"] = str(parquet_out)

        logger.info(
            f"Stage 5 complete! Answer: {metrics['status']} - Validated Hotspots: {metrics['total_validated_hotspot_pixels']} pts ({metrics['validated_hotspot_area_km2']} km2), Persistent 99% Hotspots: {metrics['persistent_99pct_hotspot_pixels']} pts ({metrics['persistent_99pct_hotspot_area_km2']} km2)"
        )
        logger.info("=================================================================")
        return metrics
