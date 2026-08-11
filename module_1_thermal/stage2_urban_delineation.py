"""
Boreas-Nexus Module 1 - Stage 2: Urban–Non-Urban Delineation

Purpose: Separate urban surfaces from surrounding rural baseline landscapes.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger
from storage.storage_manager import StorageManager


class Stage2UrbanDelineator:
    """
    Delineates study area into Urban, Rural, and Water spatial masks using land cover codes.
    """

    def __init__(
        self,
        input_aligned_path: Path | str | None = None,
        output_dir: Path | str | None = None
    ):
        self.storage_manager = StorageManager()
        self.custom_output_dir = (output_dir is not None)
        self.input_aligned_path = Path(input_aligned_path) if input_aligned_path is not None else self.storage_manager.get_debug_filepath("module_1", "module_1_stage1_aligned.parquet")
        self.output_dir = Path(output_dir) if output_dir is not None else self.storage_manager.get_debug_dir("module_1")
        self.last_gdf: Optional[gpd.GeoDataFrame] = None

    def load_stage1_data(self) -> gpd.GeoDataFrame:
        """Loads Stage 1 aligned geospatial dataset."""
        candidates = [
            self.input_aligned_path,
            self.output_dir / "module_1_stage1_aligned.parquet",
            self.storage_manager.get_debug_filepath("module_1", "module_1_stage1_aligned.parquet"),
            self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet"),
            Path("data/processed/features.parquet")
        ]

        target_path = None
        for p in candidates:
            if p.exists():
                target_path = p
                break

        if target_path is not None:
            logger.info(f"Loading aligned data from: {target_path}...")
            df = pd.read_parquet(target_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
            return gdf
        
        raise FileNotFoundError("Stage 1 dataset not found. Run Stage 1 aligner first.")

    def delineate_masks(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Calculates boolean masks for Urban, Rural, and Water surfaces."""
        result_gdf = gdf.copy()
        logger.info("Delineating Urban vs Rural baseline surface masks...")

        lc = result_gdf.get("land_cover_code", pd.Series(50, index=result_gdf.index)).values
        ndvi = result_gdf.get("ndvi", pd.Series(0.3, index=result_gdf.index)).values
        ndbi = result_gdf.get("ndbi", pd.Series(0.1, index=result_gdf.index)).values
        ndwi = result_gdf.get("ndwi", pd.Series(-0.1, index=result_gdf.index)).values
        building_density = result_gdf.get("building_density", pd.Series(0.0, index=result_gdf.index)).values

        is_water = (lc == 80) | (ndwi > 0.15)
        is_urban = ((lc == 50) | (ndbi > 0.15) | (building_density > 0.20)) & (~is_water)

        rural_lc_set = {10, 20, 30, 40, 60, 90, 95}
        is_rural_lc = np.isin(lc, list(rural_lc_set))
        is_rural = (is_rural_lc | (ndvi >= 0.25)) & (~is_urban) & (~is_water)

        result_gdf["is_urban"] = is_urban.astype(bool)
        result_gdf["is_rural"] = is_rural.astype(bool)
        result_gdf["is_water"] = is_water.astype(bool)

        # Remove redundant surface_class if present
        if "surface_class" in result_gdf.columns:
            result_gdf = result_gdf.drop(columns=["surface_class"])

        return result_gdf

    def validate_delineation(self, gdf: gpd.GeoDataFrame) -> Tuple[bool, Dict[str, Any]]:
        """Validates urban and rural baseline partitioning."""
        n_total = len(gdf)
        n_urban = int(gdf["is_urban"].sum())
        n_rural = int(gdf["is_rural"].sum())
        n_water = int(gdf["is_water"].sum())

        urban_area_km2 = n_urban * 0.01
        rural_area_km2 = n_rural * 0.01

        urban_mean_day_lst = float(gdf[gdf["is_urban"]]["lst_day_celsius"].mean()) if n_urban > 0 else 0.0
        rural_mean_day_lst = float(gdf[gdf["is_rural"]]["lst_day_celsius"].mean()) if n_rural > 0 else 0.0
        urban_mean_night_lst = float(gdf[gdf["is_urban"]]["lst_night_celsius"].mean()) if n_urban > 0 else 0.0
        rural_mean_night_lst = float(gdf[gdf["is_rural"]]["lst_night_celsius"].mean()) if n_rural > 0 else 0.0

        is_valid = (n_urban > 0) and (n_rural >= 10)

        metrics = {
            "scientific_question": "What pixels are urban and what pixels establish the rural baseline?",
            "status": "PASSED" if is_valid else "FAILED",
            "total_pixels": n_total,
            "urban_pixel_count": n_urban,
            "rural_pixel_count": n_rural,
            "water_pixel_count": n_water,
            "urban_area_km2": round(urban_area_km2, 2),
            "rural_area_km2": round(rural_area_km2, 2),
            "urban_mean_day_lst_celsius": round(urban_mean_day_lst, 2),
            "rural_mean_day_lst_celsius": round(rural_mean_day_lst, 2),
            "urban_mean_night_lst_celsius": round(urban_mean_night_lst, 2),
            "rural_mean_night_lst_celsius": round(rural_mean_night_lst, 2),
            "raw_day_uhi_delta_celsius": round(urban_mean_day_lst - rural_mean_day_lst, 2),
            "raw_night_uhi_delta_celsius": round(urban_mean_night_lst - rural_mean_night_lst, 2)
        }

        return is_valid, metrics

    def run(self, gdf_in: Optional[gpd.GeoDataFrame] = None) -> Dict[str, Any]:
        """Executes Stage 2 pipeline."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - STAGE 2: URBAN–NON-URBAN DELINEATION")
        logger.info("=================================================================")

        gdf = gdf_in.copy() if gdf_in is not None else self.load_stage1_data()
        gdf = self.delineate_masks(gdf)

        is_valid, metrics = self.validate_delineation(gdf)
        if not is_valid:
            logger.error(f"Stage 2 validation failed! Metrics: {metrics}")
            raise ValueError("Stage 2 urban delineation failed.")

        self.last_gdf = gdf

        if self.custom_output_dir or self.storage_manager.should_save_intermediate():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            parquet_out = self.output_dir / "module_1_stage2_delineated.parquet"
            logger.info(f"Saving intermediate delineated dataset to {parquet_out}...")
            df_export = pd.DataFrame(gdf.drop(columns=["geometry"]))
            df_export.to_parquet(parquet_out, index=False)
            metrics["output_parquet"] = str(parquet_out)

        logger.info(f"Stage 2 complete! Answer: {metrics['status']} - Urban: {metrics['urban_pixel_count']} pts ({metrics['urban_area_km2']} km2)")
        logger.info("=================================================================")
        return metrics
