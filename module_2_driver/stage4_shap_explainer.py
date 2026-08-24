"""
Boreas-Nexus Module 2 - Stage 4: Explainable AI Driver Attribution (SHAP)

Computes exact local Shapley Additive Explanations (SHAP) for every spatial grid cell
and hotspot cluster using TreeExplainer on trained LightGBM models. Validates the additive
reconstruction property and identifies primary, secondary, and tertiary drivers of urban heat.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
import geopandas as gpd
import shap
import yaml

from utils.logger import logger


class Stage4ShapExplainer:
    """
    Stage 4: Explainable AI Driver Attribution Engine using TreeExplainer and LightGBM.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/driver_analysis.yaml")
    ):
        self.config_path = Path(config_path)
        self.cfg = self._load_config()
        self.last_gdf: Optional[gpd.GeoDataFrame] = None
        self.shap_values: Dict[str, np.ndarray] = {}
        self.expected_values: Dict[str, float] = {}
        self.reconstruction_errors: Dict[str, Dict[str, float]] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Loads YAML configuration file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def run(
        self,
        gdf_in: gpd.GeoDataFrame,
        lgbm_models: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes Stage 4 SHAP Driver Attribution.
        
        Args:
            gdf_in: GeoDataFrame containing features and predictions from Stage 3.
            lgbm_models: Dict mapping target name to trained LGBMRegressor instance.
        """
        logger.info("--- Starting Module 2 Stage 4: Explainable AI Driver Attribution (SHAP) ---")

        if gdf_in is None or len(gdf_in) == 0:
            raise ValueError("Input GeoDataFrame to Stage 4 is None or empty.")
        if not lgbm_models:
            raise ValueError("No trained LightGBM models provided to Stage 4.")

        gdf = gdf_in.copy()

        core_drivers = self.cfg.get("features", {}).get("core_drivers", [
            "ndvi", "ndbi", "ndwi", "land_cover_code", "building_density",
            "distance_to_roads_m", "distance_to_water_m", "distance_to_parks_m",
            "elevation_m", "slope_deg", "aspect_sin", "aspect_cos"
        ])
        feature_cols = [c for c in core_drivers if c in gdf.columns]
        X = gdf[feature_cols].values
        max_error_allowed = float(self.cfg.get("quality_gates", {}).get("max_shap_reconstruction_error", 1e-4))

        targets = ["lst_day_celsius", "lst_night_celsius"]

        for target in targets:
            if target not in lgbm_models:
                logger.warning(f"No trained model for target '{target}'. Skipping SHAP computation.")
                continue

            model = lgbm_models[target]
            prefix = "day" if "day" in target else "night"
            logger.info(f"Computing TreeExplainer SHAP values for target: {target} ({prefix})...")

            # Initialize TreeExplainer
            explainer = shap.TreeExplainer(model)
            shap_vals = explainer.shap_values(X)
            
            # Handle potential multi-output or list structure
            if isinstance(shap_vals, list):
                shap_vals = shap_vals[0]
            
            expected_val = float(explainer.expected_value if np.isscalar(explainer.expected_value) else explainer.expected_value[0])
            self.shap_values[target] = shap_vals
            self.expected_values[target] = expected_val

            # Add SHAP columns for each feature
            for idx, col in enumerate(feature_cols):
                gdf[f"shap_{prefix}_{col}"] = shap_vals[:, idx]

            gdf[f"shap_base_value_{prefix}"] = expected_val

            # Mathematical Validation: Additive Reconstruction Check
            # model_prediction ≈ expected_value + sum(shap_values)
            pred_col = f"lgbm_pred_{target}"
            if pred_col in gdf.columns:
                reconstructed = expected_val + np.sum(shap_vals, axis=1)
                abs_diff = np.abs(gdf[pred_col].values - reconstructed)
                max_diff = float(np.max(abs_diff))
                mean_diff = float(np.mean(abs_diff))

                self.reconstruction_errors[target] = {
                    "max_absolute_error": max_diff,
                    "mean_absolute_error": mean_diff,
                    "validation_passed": bool(max_diff <= max_error_allowed)
                }

                gdf[f"shap_reconstruction_error_{prefix}"] = abs_diff
                logger.info(
                    f"SHAP {prefix} Reconstruction Check -> Max Error: {max_diff:.2e}, "
                    f"Mean Error: {mean_diff:.2e} (Passed: {max_diff <= max_error_allowed})"
                )

            # Extract Dominant Drivers (Primary, Secondary, Tertiary) per point
            # Rank features by absolute SHAP contribution
            abs_shap = np.abs(shap_vals)
            top_indices = np.argsort(-abs_shap, axis=1)

            feature_arr = np.array(feature_cols)
            gdf[f"primary_driver_{prefix}"] = feature_arr[top_indices[:, 0]]
            gdf[f"secondary_driver_{prefix}"] = feature_arr[top_indices[:, 1]]
            gdf[f"tertiary_driver_{prefix}"] = feature_arr[top_indices[:, 2]]

        self.last_gdf = gdf

        stage_metrics = {
            "stage": "Stage 4: Explainable AI Driver Attribution (SHAP)",
            "status": "SUCCESS",
            "feature_count": len(feature_cols),
            "expected_values": self.expected_values,
            "reconstruction_errors": self.reconstruction_errors,
            "targets_explained": list(self.shap_values.keys())
        }

        logger.info("Module 2 Stage 4 executed successfully.")
        return stage_metrics
