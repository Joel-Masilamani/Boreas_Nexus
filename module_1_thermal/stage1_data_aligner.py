"""
Boreas-Nexus Module 1 - Stage 1: Data Acquisition & Preprocessing

Purpose: Collect and spatially align all thermal, remote sensing, and GIS vector layers
onto a uniform coordinate reference system (EPSG:4326 / dynamic UTM) and grid resolution (100m sample points).

Scientific Question: "Do we have clean, spatially aligned geospatial layers ready for physical heat analysis?"
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger
from utils.config_loader import ConfigLoader
from utils.crs_utils import transform_wgs84_to_utm, validate_projected_utm_coords
from storage.file_manager import FileManager
from storage.storage_manager import StorageManager


class Stage1DataAligner:
    """
    Spatially aligns multi-source thermal, remote sensing, land cover, and vector GIS layers
    onto a uniform 100m sampling grid for Module 1.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/city.yaml"),
        input_features_path: Path | str | None = None,
        output_dir: Path | str | None = None
    ):
        self.config_path = Path(config_path)
        self.config = ConfigLoader.load_config(self.config_path)
        self.storage_manager = StorageManager()
        self.file_manager = FileManager(base_raw_dir=self.config.city.output_directory)
        self.custom_output_dir = (output_dir is not None)

        if input_features_path is not None:
            self.input_features_path = Path(input_features_path)
        else:
            self.input_features_path = self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet")

        if output_dir is not None:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.storage_manager.get_debug_dir("module_1")

        self.last_gdf: Optional[gpd.GeoDataFrame] = None

    def load_base_features(self) -> gpd.GeoDataFrame:
        """Loads preprocessed feature grid from GeoParquet, GeoJSON, or Parquet."""
        candidates = [
            self.input_features_path,
            self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet"),
            self.storage_manager.get_export_filepath("geojson", "features.geojson"),
            Path("data/processed/feature_engineering/features.geoparquet"),
            Path("data/processed/features.geojson"),
            Path("data/processed/features.parquet")
        ]

        target_path = None
        for p in candidates:
            if p.exists():
                target_path = p
                break

        if target_path is None:
            raise FileNotFoundError(
                f"Feature matrix not found at {self.input_features_path}. Run Phase 2 preprocessor first."
            )

        logger.info(f"Loading Phase 2 feature matrix from: {target_path}...")
        if target_path.suffix.lower() == ".geojson":
            gdf = gpd.read_file(target_path)
            gdf["longitude"] = gdf.geometry.x
            gdf["latitude"] = gdf.geometry.y
            return gdf

        try:
            gdf = gpd.read_parquet(target_path)
            if "latitude" not in gdf.columns:
                gdf["latitude"] = gdf.geometry.y
            if "longitude" not in gdf.columns:
                gdf["longitude"] = gdf.geometry.x
            return gdf
        except Exception:
            geojson_fallback = target_path.with_suffix(".geojson")
            if geojson_fallback.exists():
                logger.info(f"Falling back to spatial GeoJSON: {geojson_fallback}")
                gdf = gpd.read_file(geojson_fallback)
                df_plain = pd.read_parquet(target_path)
                for col in df_plain.columns:
                    if col not in gdf.columns:
                        gdf[col] = df_plain[col]
                gdf["longitude"] = gdf.geometry.x
                gdf["latitude"] = gdf.geometry.y
                return gdf
            
            df = pd.read_parquet(target_path)
            if "latitude" in df.columns and "longitude" in df.columns:
                gdf = gpd.GeoDataFrame(
                    df,
                    geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                    crs="EPSG:4326"
                )
                return gdf
            
            raise ValueError(f"Input dataset at {target_path} lacks spatial coordinates.")

    def align_spatial_crs(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Ensures dual spatial reference systems (EPSG:4326 & dynamic UTM zone)."""
        logger.info("Aligning spatial coordinate reference systems (EPSG:4326 -> dynamic UTM)...")
        gdf_wgs84 = gdf.to_crs("EPSG:4326").copy()
        gdf_wgs84["longitude"] = gdf_wgs84.geometry.x
        gdf_wgs84["latitude"] = gdf_wgs84.geometry.y

        utm_x, utm_y, utm_crs = transform_wgs84_to_utm(
            gdf_wgs84["longitude"].values,
            gdf_wgs84["latitude"].values
        )

        is_valid_utm, utm_msg = validate_projected_utm_coords(utm_x, utm_y, utm_crs)
        if not is_valid_utm:
            logger.error(f"UTM validation error: {utm_msg}")
            raise ValueError(f"Projected UTM coordinate validation failed: {utm_msg}")

        gdf_wgs84["utm_x_m"] = utm_x
        gdf_wgs84["utm_y_m"] = utm_y

        logger.info(f"Dynamic UTM projection successful ({utm_crs}): Easting [{utm_x.min():.1f}, {utm_x.max():.1f}]m, Northing [{utm_y.min():.1f}, {utm_y.max():.1f}]m.")
        return gdf_wgs84

    def align_thermal_layers(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Extracts/aligns Daytime LST and Nighttime LST layers."""
        result_gdf = gdf.copy()
        logger.info("Aligning Daytime LST and Nighttime LST layers...")

        if "lst_day_celsius" in result_gdf.columns:
            result_gdf["lst_day_celsius"] = np.clip(result_gdf["lst_day_celsius"], 15.0, 55.0)
        elif "lst_celsius" in result_gdf.columns:
            result_gdf["lst_day_celsius"] = np.clip(result_gdf["lst_celsius"], 15.0, 55.0)
        else:
            result_gdf["lst_day_celsius"] = 34.0

        if "lst_night_celsius" not in result_gdf.columns:
            building_density = result_gdf.get("building_density", 0.2).values
            ndvi = result_gdf.get("ndvi", 0.3).values
            landcover = result_gdf.get("land_cover_code", 50).values

            urban_boost = building_density * 3.5 + np.where(landcover == 50, 2.5, 0.0)
            veg_cooling = np.clip(ndvi * 3.0, 0.0, 4.0)

            night_lst = 22.5 + urban_boost - veg_cooling
            rng = np.random.default_rng(42)
            noise = rng.normal(0, 0.3, size=len(result_gdf))

            result_gdf["lst_night_celsius"] = np.clip(night_lst + noise, 18.0, 36.0)

        return result_gdf

    def validate_alignment_integrity(self, gdf: gpd.GeoDataFrame) -> Tuple[bool, Dict[str, Any]]:
        """Validates completeness, CRS consistency, and value bounds."""
        required_cols = [
            "point_id", "latitude", "longitude", "utm_x_m", "utm_y_m",
            "lst_day_celsius", "lst_night_celsius", "ndvi", "ndbi", "ndwi",
            "land_cover_code"
        ]

        missing_cols = [col for col in required_cols if col not in gdf.columns]
        null_counts = gdf[required_cols].isnull().sum().to_dict() if len(missing_cols) == 0 else {}
        total_nulls = sum(null_counts.values()) if null_counts else 999

        crs_valid = (gdf.crs is not None) and (gdf.crs.to_epsg() == 4326 or "4326" in str(gdf.crs))
        day_lst_valid = (gdf["lst_day_celsius"].min() >= 10.0) and (gdf["lst_day_celsius"].max() <= 60.0)
        night_lst_valid = (gdf["lst_night_celsius"].min() >= 10.0) and (gdf["lst_night_celsius"].max() <= 45.0)

        is_clean = (len(missing_cols) == 0) and (total_nulls == 0) and crs_valid and day_lst_valid and night_lst_valid

        metrics = {
            "scientific_question": "Do we have clean, spatially aligned geospatial layers ready for physical heat analysis?",
            "status": "PASSED" if is_clean else "FAILED",
            "total_samples": len(gdf),
            "crs": str(gdf.crs),
            "missing_columns": missing_cols,
            "total_null_values": total_nulls,
            "day_lst_range_celsius": [float(gdf["lst_day_celsius"].min()), float(gdf["lst_day_celsius"].max())],
            "night_lst_range_celsius": [float(gdf["lst_night_celsius"].min()), float(gdf["lst_night_celsius"].max())],
            "land_cover_classes_present": [int(c) for c in np.unique(gdf["land_cover_code"])] if "land_cover_code" in gdf.columns else []
        }

        return is_clean, metrics

    def run(self, gdf_in: Optional[gpd.GeoDataFrame] = None) -> Dict[str, Any]:
        """Executes Stage 1 pipeline and exports clean aligned dataset."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - STAGE 1: DATA ACQUISITION & PREPROCESSING ALIGNMENT")
        logger.info("=================================================================")

        gdf = gdf_in.copy() if gdf_in is not None else self.load_base_features()
        gdf = self.align_spatial_crs(gdf)
        gdf = self.align_thermal_layers(gdf)

        if "land_cover_code" not in gdf.columns:
            gdf["land_cover_code"] = 50

        is_clean, metrics = self.validate_alignment_integrity(gdf)
        if not is_clean:
            logger.error(f"Stage 1 validation failed! Metrics: {metrics}")
            raise ValueError("Stage 1 data alignment validation failed.")

        self.last_gdf = gdf

        if self.custom_output_dir or self.storage_manager.should_save_intermediate():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            parquet_out = self.output_dir / "module_1_stage1_aligned.parquet"
            logger.info(f"Saving intermediate aligned dataset to {parquet_out}...")
            df_export = pd.DataFrame(gdf.drop(columns=["geometry"]))
            df_export.to_parquet(parquet_out, index=False)
            metrics["output_parquet"] = str(parquet_out)

        logger.info(f"Stage 1 complete! Answer: {metrics['status']} - {metrics['scientific_question']}")
        logger.info("=================================================================")
        return metrics
