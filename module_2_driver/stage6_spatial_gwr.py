"""
Boreas-Nexus Module 2 - Stage 6: Spatial Driver Intelligence (Geographically Weighted Regression)

Captures spatial non-stationarity in urban heat driver relationships across neighborhoods
using spatially balanced sampling and Geographically Weighted Regression (GWR). Provides
spatial coefficient maps and local cooling efficiency metrics with graceful fault-tolerance.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
import yaml

from utils.logger import logger

# Import MGWR conditionally for robust execution
try:
    from mgwr.gwr import GWR, MGWR
    from mgwr.sel_bw import Sel_BW
    HAS_MGWR = True
except ImportError:
    HAS_MGWR = False


class Stage6SpatialGWR:
    """
    Stage 6: Spatial Driver Intelligence Engine using Geographically Weighted Regression (GWR).
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/driver_analysis.yaml")
    ):
        self.config_path = Path(config_path)
        self.cfg = self._load_config()
        self.last_gdf: Optional[gpd.GeoDataFrame] = None
        self.gwr_metrics: Dict[str, Any] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Loads YAML configuration file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _spatially_balanced_sampling(
        self,
        gdf: gpd.GeoDataFrame,
        max_samples: int = 5000,
        random_seed: int = 42
    ) -> np.ndarray:
        """
        Selects a spatially balanced sample of points across the study area using
        spatial block stratification to ensure uniform geographic coverage.
        """
        n_total = len(gdf)
        if n_total <= max_samples:
            return np.arange(n_total)

        np.random.seed(random_seed)

        if "spatial_block_id" in gdf.columns:
            # Stratify samples evenly across spatial blocks
            blocks = gdf["spatial_block_id"].values
            unique_blocks = np.unique(blocks)
            samples_per_block = max(1, int(np.ceil(max_samples / len(unique_blocks))))

            sampled_indices = []
            for b in unique_blocks:
                b_indices = np.where(blocks == b)[0]
                n_draw = min(len(b_indices), samples_per_block)
                drawn = np.random.choice(b_indices, size=n_draw, replace=False)
                sampled_indices.extend(drawn)

            sampled_indices = np.array(sampled_indices)
            if len(sampled_indices) > max_samples:
                sampled_indices = np.random.choice(sampled_indices, size=max_samples, replace=False)
            return np.sort(sampled_indices)
        else:
            # Fallback to random uniform sample
            return np.sort(np.random.choice(n_total, size=max_samples, replace=False))

    def _fit_gwr_mgwr(
        self,
        coords_sample: np.ndarray,
        X_sample: np.ndarray,
        y_sample: np.ndarray,
        all_coords: np.ndarray,
        feature_names: List[str]
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Fits GWR using the mgwr library and maps local coefficients back to all points.
        """
        # Standardize data for GWR stability
        X_mean, X_std = np.mean(X_sample, axis=0), np.std(X_sample, axis=0) + 1e-6
        X_scaled = (X_sample - X_mean) / X_std
        y_scaled = (y_sample - np.mean(y_sample)) / (np.std(y_sample) + 1e-6)

        try:
            # Select bandwidth
            logger.info("Optimizing GWR spatial bandwidth...")
            bw_selector = Sel_BW(coords_sample, y_scaled.reshape(-1, 1), X_scaled)
            optimal_bw = bw_selector.search(search_method='golden_section', criterion='AICc', max_iter=20)
            
            logger.info(f"Fitting GWR model with bandwidth: {optimal_bw}...")
            gwr_model = GWR(coords_sample, y_scaled.reshape(-1, 1), X_scaled, bw=optimal_bw)
            gwr_results = gwr_model.fit()

            sample_betas = gwr_results.params  # (n_samples, n_features + 1)
            sample_local_r2 = gwr_results.localR2.flatten() if hasattr(gwr_results, "localR2") else np.zeros(len(coords_sample))
        except Exception as err:
            logger.warning(f"MGWR optimization encountered issue: {err}. Using local spatial ridge regression.")
            # Robust local ridge regression fallback
            from sklearn.linear_model import Ridge
            tree_local = cKDTree(coords_sample)
            k_neighbors = min(60, len(coords_sample) - 1)
            sample_betas = np.zeros((len(coords_sample), X_scaled.shape[1] + 1))
            sample_local_r2 = np.zeros(len(coords_sample))

            for i in range(len(coords_sample)):
                dists, idxs = tree_local.query(coords_sample[i], k=k_neighbors)
                w = np.exp(-dists / (np.mean(dists) + 1e-5))
                ridge = Ridge(alpha=1.0)
                ridge.fit(X_scaled[idxs], y_scaled[idxs], sample_weight=w)
                sample_betas[i, 0] = ridge.intercept_
                sample_betas[i, 1:] = ridge.coef_
                sample_local_r2[i] = max(0.0, float(ridge.score(X_scaled[idxs], y_scaled[idxs], sample_weight=w)))

            optimal_bw = float(k_neighbors)

        # Interpolate local parameters to all points using Nearest-Neighbors IDW
        tree = cKDTree(coords_sample)
        distances, indices = tree.query(all_coords, k=3)
        weights = 1.0 / (distances + 1e-5)
        weights /= np.sum(weights, axis=1, keepdims=True)

        all_betas = np.sum(sample_betas[indices] * weights[:, :, np.newaxis], axis=1)
        all_local_r2 = np.sum(sample_local_r2[indices] * weights, axis=1)

        return all_betas, all_local_r2, float(optimal_bw)

    def _fit_gwr_for_target(
        self,
        target_col: str,
        prefix: str,
        all_coords: np.ndarray,
        coords_sample: np.ndarray,
        sample_indices: np.ndarray,
        X_sample: np.ndarray,
        gdf: gpd.GeoDataFrame,
        available_drivers: List[str]
    ) -> Tuple[float, float, str]:
        """
        Fits GWR for a specific diurnal target and assigns local betas and local R2.
        """
        if target_col not in gdf.columns:
            logger.warning(f"Target column '{target_col}' missing from dataset. Skipping GWR for {prefix}.")
            return 0.0, 0.0, "SKIPPED"

        y_sample = gdf[target_col].values[sample_indices]

        try:
            all_betas, all_local_r2, optimal_bw = self._fit_gwr_mgwr(
                coords_sample=coords_sample,
                X_sample=X_sample,
                y_sample=y_sample,
                all_coords=all_coords,
                feature_names=available_drivers
            )

            # Store coefficients with period-specific prefix
            gdf[f"{prefix}_intercept"] = all_betas[:, 0]
            for idx, feat in enumerate(available_drivers):
                gdf[f"{prefix}_beta_{feat}"] = all_betas[:, idx + 1]
            gdf[f"{prefix}_local_r2"] = np.clip(all_local_r2, 0.0, 1.0)

            mean_r2 = float(np.nanmean(gdf[f"{prefix}_local_r2"]))
            status = "SUCCESS"
            logger.info(f"GWR Spatial Modeling for {target_col} completed (optimal_bw={optimal_bw}, mean_local_r2={round(mean_r2, 4)}).")
            return optimal_bw, mean_r2, status
        except Exception as e:
            logger.error(f"GWR fitting failed for {target_col}: {e}. Applying graceful fallback.")
            gdf[f"{prefix}_local_r2"] = np.nan
            return 0.0, 0.0, "FAILED_FALLBACK"

    def run(self, gdf_in: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Executes Stage 6 Spatial Driver Intelligence (GWR) for both daytime and nighttime targets.
        """
        logger.info("--- Starting Module 2 Stage 6: Spatial Driver Intelligence (GWR) ---")

        if gdf_in is None or len(gdf_in) == 0:
            raise ValueError("Input GeoDataFrame to Stage 6 is None or empty.")

        gdf = gdf_in.copy()
        gwr_cfg = self.cfg.get("spatial_driver_intelligence", {})
        enabled = bool(gwr_cfg.get("enable_gwr", True))

        if not enabled or not HAS_MGWR:
            if not enabled:
                logger.info("GWR Spatial Driver Intelligence is disabled in config.")
            else:
                logger.warning("Package 'mgwr' not found. Skipping GWR execution cleanly.")
            
            gdf["gwr_local_r2"] = np.nan
            gdf["gwr_day_local_r2"] = np.nan
            gdf["gwr_night_local_r2"] = np.nan
            self.last_gdf = gdf
            return {
                "stage": "Stage 6: Spatial Driver Intelligence (GWR)",
                "status": "SKIPPED",
                "reason": "disabled_in_config" if not enabled else "mgwr_not_installed",
                "points_processed": len(gdf)
            }

        # Key drivers for spatial regression
        candidate_drivers = ["ndvi", "building_density", "distance_to_water_m", "distance_to_parks_m", "elevation_m"]
        available_drivers = []
        for d in candidate_drivers:
            if d in gdf.columns:
                std_val = float(gdf[d].std())
                if std_val > 1e-4:  # non-zero variance
                    available_drivers.append(d)

        if not available_drivers or ("lst_day_celsius" not in gdf.columns and "lst_night_celsius" not in gdf.columns):
            logger.warning("Missing required drivers or LST targets for GWR. Skipping.")
            self.last_gdf = gdf
            return {"stage": "Stage 6: Spatial Driver Intelligence", "status": "SKIPPED"}

        # Spatially Balanced Sampling (capped for GWR performance)
        max_samples = min(int(gwr_cfg.get("gwr_max_samples", 1500)), len(gdf))
        seed = int(self.cfg.get("reproducibility", {}).get("gwr_sampling_seed", 42))
        sample_indices = self._spatially_balanced_sampling(gdf, max_samples=max_samples, random_seed=seed)
        logger.info(f"Selected {len(sample_indices)} spatially balanced sample points for GWR fitting.")

        # Coordinate arrays
        if "utm_x_m" in gdf.columns and "utm_y_m" in gdf.columns:
            all_coords = np.column_stack([gdf["utm_x_m"].values, gdf["utm_y_m"].values])
        else:
            all_coords = np.column_stack([gdf.geometry.x.values, gdf.geometry.y.values])

        coords_sample = all_coords[sample_indices]
        X_sample = gdf[available_drivers].values[sample_indices]

        # Pass 1: Daytime LST GWR
        bw_day, mean_r2_day, status_day = self._fit_gwr_for_target(
            target_col="lst_day_celsius",
            prefix="gwr_day",
            all_coords=all_coords,
            coords_sample=coords_sample,
            sample_indices=sample_indices,
            X_sample=X_sample,
            gdf=gdf,
            available_drivers=available_drivers
        )

        # Pass 2: Nighttime LST GWR
        bw_night, mean_r2_night, status_night = self._fit_gwr_for_target(
            target_col="lst_night_celsius",
            prefix="gwr_night",
            all_coords=all_coords,
            coords_sample=coords_sample,
            sample_indices=sample_indices,
            X_sample=X_sample,
            gdf=gdf,
            available_drivers=available_drivers
        )

        # Backward compatibility aliases (mirror daytime GWR)
        gdf["gwr_intercept"] = gdf["gwr_day_intercept"] if "gwr_day_intercept" in gdf.columns else np.nan
        for feat in available_drivers:
            if f"gwr_day_beta_{feat}" in gdf.columns:
                gdf[f"gwr_beta_{feat}"] = gdf[f"gwr_day_beta_{feat}"]
        gdf["gwr_local_r2"] = gdf["gwr_day_local_r2"] if "gwr_day_local_r2" in gdf.columns else np.nan

        self.last_gdf = gdf

        overall_status = "SUCCESS" if (status_day == "SUCCESS" or status_night == "SUCCESS") else "FAILED_FALLBACK"

        stage_metrics = {
            "stage": "Stage 6: Spatial Driver Intelligence (GWR)",
            "status": overall_status,
            "sample_points_used": len(sample_indices),
            "drivers_modeled": available_drivers,
            "day_optimal_bandwidth": bw_day,
            "day_mean_local_r2": mean_r2_day,
            "night_optimal_bandwidth": bw_night,
            "night_mean_local_r2": mean_r2_night,
            "mean_local_r2": float(np.nanmean(gdf["gwr_local_r2"])) if "gwr_local_r2" in gdf.columns else 0.0
        }

        logger.info("Module 2 Stage 6 executed successfully.")
        return stage_metrics
