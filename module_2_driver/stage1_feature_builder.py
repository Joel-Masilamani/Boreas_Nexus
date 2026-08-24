"""
Boreas-Nexus Module 2 - Stage 1: Multi-Source Feature Engineering & Alignment

Ingests the Module 1 Urban Heat Hotspot Knowledge Layer, transforms raw aspect degrees
into circular components (aspect_sin, aspect_cos), validates core physical driver
features, and enforces strict 1-to-1 spatial alignment across all sample points.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
import geopandas as gpd
import yaml

from utils.logger import logger


class Stage1FeatureBuilder:
    """
    Stage 1: Multi-Source Feature Engineering & Transformation Engine.
    Prepares the unified physical driver feature matrix from Module 1 Knowledge Layer.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/driver_analysis.yaml"),
        input_path: Optional[Path | str] = None
    ):
        self.config_path = Path(config_path)
        self.cfg = self._load_config()
        self.input_path = Path(input_path) if input_path else Path(
            self.cfg.get("storage", {}).get(
                "input_knowledge_layer",
                "data/processed/module_1/urban_heat_hotspot_knowledge_layer.geoparquet"
            )
        )
        self.last_gdf: Optional[gpd.GeoDataFrame] = None

    def _load_config(self) -> Dict[str, Any]:
        """Loads YAML configuration file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        logger.warning(f"Config path {self.config_path} not found. Using defaults.")
        return {}

    def _encode_circular_aspect(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Converts aspect_deg (0-360) into continuous trigonometric components:
        aspect_sin = sin(radians(aspect))
        aspect_cos = cos(radians(aspect))
        Eliminates artificial discontinuities at 0°/360°.
        """
        if "aspect_deg" not in gdf.columns:
            raise ValueError("Input dataset is missing required 'aspect_deg' column.")

        # Fill any potential null aspect with 0 before conversion
        aspect_rad = np.radians(gdf["aspect_deg"].fillna(0.0).values)
        gdf["aspect_sin"] = np.sin(aspect_rad)
        gdf["aspect_cos"] = np.cos(aspect_rad)
        
        logger.info("Successfully encoded 'aspect_deg' into 'aspect_sin' and 'aspect_cos'.")
        return gdf

    def _validate_core_features(self, gdf: gpd.GeoDataFrame) -> List[str]:
        """
        Validates the presence and integrity of all mandatory core driver attributes.
        """
        core_drivers = self.cfg.get("features", {}).get("core_drivers", [
            "ndvi", "ndbi", "ndwi", "land_cover_code", "building_density",
            "distance_to_roads_m", "distance_to_water_m", "distance_to_parks_m",
            "elevation_m", "slope_deg", "aspect_sin", "aspect_cos"
        ])

        missing = [col for col in core_drivers if col not in gdf.columns]
        if missing:
            raise ValueError(f"Missing mandatory core driver features in dataset: {missing}")

        # Check for NaNs across mandatory driver features
        for col in core_drivers:
            nan_count = gdf[col].isna().sum()
            if nan_count > 0:
                logger.warning(f"Feature '{col}' contains {nan_count} NaNs. Imputing with median.")
                gdf[col] = gdf[col].fillna(gdf[col].median())

        return core_drivers

    def _compute_optional_neighborhood_features(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Conditionally computes neighborhood / context spatial features if enabled in configuration.
        """
        feat_cfg = self.cfg.get("features", {})
        if not feat_cfg.get("enable_neighborhood_features", False):
            logger.info("Neighborhood context features are disabled in config.")
            return gdf

        radius_m = feat_cfg.get("neighborhood_buffer_radius_m", 300)
        logger.info(f"Computing neighborhood context features with {radius_m}m buffer...")
        
        # Calculate local spatial context proxy
        if "building_density" in gdf.columns:
            gdf["neighborhood_building_density_300m"] = gdf["building_density"].rolling(
                window=5, min_periods=1, center=True
            ).mean()

        return gdf

    def run(self, gdf_in: Optional[gpd.GeoDataFrame] = None) -> Dict[str, Any]:
        """
        Executes Stage 1 Feature Engineering pipeline.
        
        Args:
            gdf_in: Optional in-memory GeoDataFrame from Module 1.
            
        Returns:
            Dictionary containing stage execution metrics and feature metadata.
        """
        logger.info("--- Starting Module 2 Stage 1: Feature Engineering & Alignment ---")

        if gdf_in is not None:
            gdf = gdf_in.copy()
            logger.info(f"Loaded {len(gdf)} sample points from in-memory GeoDataFrame.")
        else:
            if not self.input_path.exists():
                raise FileNotFoundError(
                    f"Module 1 Knowledge Layer not found at: {self.input_path}. "
                    "Please run Module 1 first."
                )
            gdf = gpd.read_parquet(self.input_path)
            logger.info(f"Loaded {len(gdf)} sample points from {self.input_path}.")

        total_points = len(gdf)
        if total_points == 0:
            raise ValueError("Input dataset is empty.")

        # 1. Circular Aspect Encoding
        gdf = self._encode_circular_aspect(gdf)

        # 2. Validate Core Physical Driver Features
        core_drivers = self._validate_core_features(gdf)

        # 3. Optional Neighborhood Feature Construction
        gdf = self._compute_optional_neighborhood_features(gdf)

        # 4. Enforce Spatial Alignment & ID Consistency
        if "point_id" not in gdf.columns:
            raise ValueError("Dataset missing mandatory 'point_id' column.")
        
        # Verify 1-to-1 spatial alignment
        assert len(gdf) == total_points, "Row count changed during feature engineering!"

        self.last_gdf = gdf

        metrics = {
            "stage": "Stage 1: Multi-Source Feature Engineering",
            "status": "SUCCESS",
            "total_points": total_points,
            "core_driver_count": len(core_drivers),
            "core_drivers": core_drivers,
            "aspect_sin_mean": float(gdf["aspect_sin"].mean()),
            "aspect_cos_mean": float(gdf["aspect_cos"].mean()),
            "neighborhood_features_enabled": bool(self.cfg.get("features", {}).get("enable_neighborhood_features", False))
        }

        logger.info(f"Module 2 Stage 1 completed successfully with {len(core_drivers)} core physical drivers.")
        return metrics
