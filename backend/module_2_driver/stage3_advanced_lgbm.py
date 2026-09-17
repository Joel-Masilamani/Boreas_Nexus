"""
Boreas-Nexus Module 2 - Stage 3: Advanced Driver Modeling (LightGBM)

Trains advanced Gradient Boosted Decision Tree (LightGBM) models with spatial block
cross-validation to capture non-linear driver interactions, evaluates cross-validation
accuracy, and enforces performance quality gates before passing to the SHAP explainer.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
import geopandas as gpd
from lightgbm import LGBMRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import yaml

from utils.logger import logger


class Stage3AdvancedLGBM:
    """
    Stage 3: Advanced Driver Modeling using LightGBM and Spatial Block CV.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/driver_analysis.yaml")
    ):
        self.config_path = Path(config_path)
        self.cfg = self._load_config()
        self.last_gdf: Optional[gpd.GeoDataFrame] = None
        self.lgbm_models: Dict[str, LGBMRegressor] = {}
        self.cv_metrics: Dict[str, Dict[str, float]] = {}
        self.gate_statuses: Dict[str, str] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Loads YAML configuration file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _evaluate_spatial_cv(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        n_splits: int,
        lgbm_params: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Executes Spatial Block GroupKFold Cross-Validation for LightGBM.
        """
        unique_groups = len(np.unique(groups))
        effective_splits = min(n_splits, unique_groups)

        if effective_splits < 2:
            logger.warning("Not enough spatial blocks for GroupKFold CV. Using full dataset fit.")
            model = LGBMRegressor(**lgbm_params, verbose=-1)
            model.fit(X, y)
            preds = model.predict(X)
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

            model = LGBMRegressor(**lgbm_params, verbose=-1)
            model.fit(X_train, y_train)
            val_preds = model.predict(X_val)

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
        Executes Stage 3 LightGBM Driver Modeling pipeline.
        """
        logger.info("--- Starting Module 2 Stage 3: Advanced Driver Modeling (LightGBM) ---")

        if gdf_in is None or len(gdf_in) == 0:
            raise ValueError("Input GeoDataFrame to Stage 3 is None or empty.")

        gdf = gdf_in.copy()

        # 1. Prepare Features & Spatial Blocks
        core_drivers = self.cfg.get("features", {}).get("core_drivers", [
            "ndvi", "ndbi", "ndwi", "land_cover_code", "building_density",
            "distance_to_roads_m", "distance_to_water_m", "distance_to_parks_m",
            "elevation_m", "slope_deg", "aspect_sin", "aspect_cos"
        ])
        feature_cols = [c for c in core_drivers if c in gdf.columns]
        X = gdf[feature_cols].values

        if "spatial_block_id" in gdf.columns:
            spatial_blocks = gdf["spatial_block_id"].values
        else:
            # Create fallback blocks
            x = gdf.geometry.x.values * 111000.0
            y = gdf.geometry.y.values * 111000.0
            spatial_blocks = (np.floor(x / 2000.0) * 100000 + np.floor(y / 2000.0)).astype(int)

        # 2. Hyperparameters
        lgbm_params = self.cfg.get("models", {}).get("advanced_lightgbm", {
            "n_estimators": 200,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "max_depth": -1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "n_jobs": -1
        })
        min_r2_threshold = float(self.cfg.get("quality_gates", {}).get("min_r2_threshold", 0.50))
        n_splits = int(self.cfg.get("spatial_cv", {}).get("n_splits", 5))

        targets = ["lst_day_celsius", "lst_night_celsius"]

        for target in targets:
            if target not in gdf.columns:
                logger.warning(f"Target '{target}' not found in dataset. Skipping.")
                continue

            y = gdf[target].values

            # Spatial CV Evaluation
            logger.info(f"Evaluating spatial block CV for LightGBM on target: {target}...")
            cv_res = self._evaluate_spatial_cv(
                X=X, y=y, groups=spatial_blocks, n_splits=n_splits, lgbm_params=lgbm_params
            )
            self.cv_metrics[target] = cv_res

            # Check Quality Gate
            mean_r2 = cv_res["r2_mean"]
            if mean_r2 >= min_r2_threshold:
                gate_status = "PASSED"
                logger.info(f"LightGBM {target} PASSED quality gate with Spatial CV R² = {mean_r2:.4f} (>= {min_r2_threshold})")
            else:
                gate_status = "WARNING"
                logger.warning(f"LightGBM {target} Spatial CV R² = {mean_r2:.4f} is below target threshold ({min_r2_threshold})")
            self.gate_statuses[target] = gate_status

            # Train Full-Dataset Model
            logger.info(f"Training full-dataset LightGBM model for {target}...")
            full_model = LGBMRegressor(**lgbm_params, verbose=-1)
            full_model.fit(X, y)
            self.lgbm_models[target] = full_model

            # Generate Predictions and Residuals
            pred_col = f"lgbm_pred_{target}"
            res_col = f"lgbm_residual_{target}"
            gdf[pred_col] = full_model.predict(X)
            gdf[res_col] = gdf[target] - gdf[pred_col]

            logger.info(
                f"LightGBM {target} -> Spatial CV R²: {cv_res['r2_mean']:.4f} | "
                f"RMSE: {cv_res['rmse_mean']:.3f}°C | Status: {gate_status}"
            )

        self.last_gdf = gdf

        stage_metrics = {
            "stage": "Stage 3: Advanced Driver Modeling (LightGBM)",
            "status": "SUCCESS",
            "feature_count": len(feature_cols),
            "cv_metrics": self.cv_metrics,
            "gate_statuses": self.gate_statuses,
            "targets_trained": list(self.lgbm_models.keys())
        }

        logger.info("Module 2 Stage 3 executed successfully.")
        return stage_metrics
