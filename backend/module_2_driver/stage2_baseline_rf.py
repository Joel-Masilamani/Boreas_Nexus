"""
Boreas-Nexus Module 2 - Stage 2: Baseline Driver Modeling (Random Forest)

Trains baseline Random Forest models using spatial block cross-validation to prevent
spatial autocorrelation data leakage, computes global feature importances, and establishes
the performance benchmark for urban heat driver analysis.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import yaml

from utils.logger import logger


class Stage2BaselineRF:
    """
    Stage 2: Baseline Driver Modeling with Random Forest Regressor and Spatial Block CV.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/driver_analysis.yaml")
    ):
        self.config_path = Path(config_path)
        self.cfg = self._load_config()
        self.last_gdf: Optional[gpd.GeoDataFrame] = None
        self.rf_models: Dict[str, RandomForestRegressor] = {}
        self.cv_metrics: Dict[str, Dict[str, float]] = {}
        self.feature_importances: Dict[str, Dict[str, float]] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Loads YAML configuration file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _create_spatial_blocks(
        self,
        gdf: gpd.GeoDataFrame,
        block_size_m: float = 2000.0
    ) -> np.ndarray:
        """
        Assigns spatial block IDs to each point based on projected UTM coordinates.
        Ensures points in the same geographic block belong to the same fold group.
        """
        if "utm_x_m" in gdf.columns and "utm_y_m" in gdf.columns:
            x = gdf["utm_x_m"].values
            y = gdf["utm_y_m"].values
        else:
            # Fallback to geometry coordinates in degrees approximated to meters (~111km/deg)
            x = gdf.geometry.x.values * 111000.0
            y = gdf.geometry.y.values * 111000.0

        grid_x = np.floor(x / block_size_m).astype(int)
        grid_y = np.floor(y / block_size_m).astype(int)
        
        # Unique block integer ID
        block_ids = grid_x * 100000 + grid_y
        return block_ids

    def _evaluate_spatial_cv(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        n_splits: int,
        rf_params: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Executes Spatial Block GroupKFold Cross-Validation.
        """
        unique_groups = len(np.unique(groups))
        effective_splits = min(n_splits, unique_groups)
        
        if effective_splits < 2:
            logger.warning("Not enough spatial blocks for GroupKFold CV. Using standard evaluation.")
            rf = RandomForestRegressor(**rf_params)
            rf.fit(X, y)
            preds = rf.predict(X)
            return {
                "r2_mean": float(r2_score(y, preds)),
                "rmse_mean": float(np.sqrt(mean_squared_error(y, preds))),
                "mae_mean": float(mean_absolute_error(y, preds)),
                "n_splits_used": 1
            }

        gkf = GroupKFold(n_splits=effective_splits)
        r2_scores, rmse_scores, mae_scores = [], [], []

        for train_idx, val_idx in gkf.split(X, y, groups=groups):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            rf = RandomForestRegressor(**rf_params)
            rf.fit(X_train, y_train)
            val_preds = rf.predict(X_val)

            r2_scores.append(r2_score(y_val, val_preds))
            rmse_scores.append(np.sqrt(mean_squared_error(y_val, val_preds)))
            mae_scores.append(mean_absolute_error(y_val, val_preds))

        return {
            "r2_mean": float(np.mean(r2_scores)),
            "r2_std": float(np.std(r2_scores)),
            "rmse_mean": float(np.mean(rmse_scores)),
            "rmse_std": float(np.std(rmse_scores)),
            "mae_mean": float(np.mean(mae_scores)),
            "mae_std": float(np.std(mae_scores)),
            "n_splits_used": effective_splits
        }

    def run(self, gdf_in: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Executes Stage 2 Baseline Random Forest Driver Modeling.
        """
        logger.info("--- Starting Module 2 Stage 2: Baseline Driver Modeling (Random Forest) ---")

        if gdf_in is None or len(gdf_in) == 0:
            raise ValueError("Input GeoDataFrame to Stage 2 is None or empty.")

        gdf = gdf_in.copy()
        
        # 1. Prepare Feature Set
        core_drivers = self.cfg.get("features", {}).get("core_drivers", [
            "ndvi", "ndbi", "ndwi", "land_cover_code", "building_density",
            "distance_to_roads_m", "distance_to_water_m", "distance_to_parks_m",
            "elevation_m", "slope_deg", "aspect_sin", "aspect_cos"
        ])
        
        feature_cols = [c for c in core_drivers if c in gdf.columns]
        X = gdf[feature_cols].values

        # 2. Spatial Blocks for GroupKFold
        cv_cfg = self.cfg.get("spatial_cv", {})
        block_size = float(cv_cfg.get("block_size_meters", 2000.0))
        n_splits = int(cv_cfg.get("n_splits", 5))
        spatial_blocks = self._create_spatial_blocks(gdf, block_size_m=block_size)
        gdf["spatial_block_id"] = spatial_blocks

        # 3. Model Parameters
        rf_params = self.cfg.get("models", {}).get("baseline_random_forest", {
            "n_estimators": 100,
            "max_depth": 12,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
            "n_jobs": -1,
            "random_state": 42
        })

        targets = ["lst_day_celsius", "lst_night_celsius"]
        metrics_summary = {}

        for target in targets:
            if target not in gdf.columns:
                logger.warning(f"Target column '{target}' not found in dataset. Skipping.")
                continue

            y = gdf[target].values

            # Spatial Block Cross-Validation
            logger.info(f"Evaluating spatial block CV for target: {target}...")
            cv_res = self._evaluate_spatial_cv(
                X=X, y=y, groups=spatial_blocks, n_splits=n_splits, rf_params=rf_params
            )
            self.cv_metrics[target] = cv_res

            # Train Full Dataset Model
            logger.info(f"Training full-dataset baseline Random Forest for {target}...")
            full_rf = RandomForestRegressor(**rf_params)
            full_rf.fit(X, y)
            self.rf_models[target] = full_rf

            # Generate Predictions and Residuals
            pred_col = f"rf_pred_{target}"
            res_col = f"rf_residual_{target}"
            gdf[pred_col] = full_rf.predict(X)
            gdf[res_col] = gdf[target] - gdf[pred_col]

            # Feature Importances
            importances = dict(zip(feature_cols, [float(v) for v in full_rf.feature_importances_]))
            sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))
            self.feature_importances[target] = sorted_importances

            metrics_summary[target] = {
                "spatial_cv_r2": cv_res["r2_mean"],
                "spatial_cv_rmse": cv_res["rmse_mean"],
                "top_3_drivers": list(sorted_importances.keys())[:3]
            }

            logger.info(
                f"RF {target} -> Spatial CV R²: {cv_res['r2_mean']:.4f} | "
                f"RMSE: {cv_res['rmse_mean']:.3f}°C | Top Driver: {list(sorted_importances.keys())[0]}"
            )

        self.last_gdf = gdf

        stage_metrics = {
            "stage": "Stage 2: Baseline Driver Modeling (Random Forest)",
            "status": "SUCCESS",
            "feature_count": len(feature_cols),
            "features": feature_cols,
            "unique_spatial_blocks": int(len(np.unique(spatial_blocks))),
            "cv_metrics": self.cv_metrics,
            "feature_importances": self.feature_importances,
            "targets_evaluated": list(self.rf_models.keys())
        }

        logger.info("Module 2 Stage 2 executed successfully.")
        return stage_metrics
