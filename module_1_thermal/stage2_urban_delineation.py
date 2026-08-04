"""
Boreas-Nexus Module 1 - Stage 2: Urban–Non-Urban Delineation

Purpose: Separate urban surfaces (concrete, asphalt, buildings) from surrounding
rural/natural landscapes (agriculture, forest, unbuilt soil).

Scientific Theory: UHI Intensity = T_urban - T_rural
Before any UHI analysis can occur, the city must be partitioned into an Urban Mask and a Rural Mask.

Scientific Question: "What pixels are urban and what pixels establish the rural baseline?"
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger
from utils.config_loader import ConfigLoader


class Stage2UrbanDelineator:
    """
    Delineates study area into Urban, Rural, and Water spatial masks using ESA WorldCover 10m
    land classification codes and spectral vegetation / built-up indices.
    """

    def __init__(
        self,
        input_aligned_path: Path | str = Path("data/processed/module_1_stage1_aligned.parquet"),
        output_dir: Path | str = Path("data/processed")
    ):
        self.input_aligned_path = Path(input_aligned_path)
        self.output_dir = Path(output_dir)

    def load_stage1_data(self) -> gpd.GeoDataFrame:
        """Loads Stage 1 aligned geospatial dataset."""
        if self.input_aligned_path.exists():
            logger.info(f"Loading Stage 1 aligned data from Parquet: {self.input_aligned_path}...")
            df = pd.read_parquet(self.input_aligned_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
        else:
            geojson_path = self.input_aligned_path.with_suffix(".geojson")
            if geojson_path.exists():
                logger.info(f"Loading Stage 1 aligned data from GeoJSON: {geojson_path}...")
                gdf = gpd.read_file(geojson_path)
            else:
                raise FileNotFoundError(
                    f"Stage 1 aligned dataset not found at {self.input_aligned_path}. Run Stage 1 aligner first."
                )

        return gdf

    def delineate_masks(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Calculates boolean masks for Urban, Rural, and Water surfaces.

        Classes in ESA WorldCover:
        - 10: Trees / Forest
        - 20: Shrubland
        - 30: Grassland
        - 40: Cropland / Agriculture
        - 50: Built-up / Urban
        - 60: Bare / Sparse vegetation
        - 80: Open Water
        - 90: Wetlands
        - 95: Mangroves
        """
        result_gdf = gdf.copy()
        logger.info("Delineating Urban vs Rural baseline surface masks...")

        lc = result_gdf.get("land_cover_code", pd.Series(50, index=result_gdf.index)).values
        ndvi = result_gdf.get("ndvi", pd.Series(0.3, index=result_gdf.index)).values
        ndbi = result_gdf.get("ndbi", pd.Series(0.1, index=result_gdf.index)).values
        ndwi = result_gdf.get("ndwi", pd.Series(-0.1, index=result_gdf.index)).values
        building_density = result_gdf.get("building_density", pd.Series(0.0, index=result_gdf.index)).values

        # 1. Water Mask: Open water or high NDWI
        is_water = (lc == 80) | (ndwi > 0.15)

        # 2. Urban Mask: Built-up class 50 or high NDBI/building density (and not water)
        is_urban = ((lc == 50) | (ndbi > 0.15) | (building_density > 0.20)) & (~is_water)

        # 3. Rural Mask: Natural vegetation / cropland / bare soil (and not urban / not water)
        rural_lc_set = {10, 20, 30, 40, 60, 90, 95}
        is_rural_lc = np.isin(lc, list(rural_lc_set))
        is_rural = (is_rural_lc | (ndvi >= 0.25)) & (~is_urban) & (~is_water)

        # Assign explicit surface class labels
        surface_class = np.full(len(result_gdf), "Other Unbuilt", dtype=object)
        surface_class[is_urban] = "Urban"
        surface_class[is_rural] = "Rural Baseline"
        surface_class[is_water] = "Water"

        result_gdf["is_urban"] = is_urban
        result_gdf["is_rural"] = is_rural
        result_gdf["is_water"] = is_water
        result_gdf["surface_class"] = surface_class

        return result_gdf

    def validate_delineation(self, gdf: gpd.GeoDataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates urban and rural baseline partitioning.

        Answers Scientific Question:
        "What pixels are urban and what pixels establish the rural baseline?"
        """
        n_total = len(gdf)
        n_urban = int(gdf["is_urban"].sum())
        n_rural = int(gdf["is_rural"].sum())
        n_water = int(gdf["is_water"].sum())

        # Area calculation at 100m grid resolution (1 cell = 0.01 km^2)
        urban_area_km2 = n_urban * 0.01
        rural_area_km2 = n_rural * 0.01

        urban_mean_day_lst = float(gdf[gdf["is_urban"]]["lst_day_celsius"].mean())
        rural_mean_day_lst = float(gdf[gdf["is_rural"]]["lst_day_celsius"].mean())

        urban_mean_night_lst = float(gdf[gdf["is_urban"]]["lst_night_celsius"].mean())
        rural_mean_night_lst = float(gdf[gdf["is_rural"]]["lst_night_celsius"].mean())

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

    def run(self) -> Dict[str, Any]:
        """Executes Stage 2 pipeline and exports delineated dataset."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - STAGE 2: URBAN–NON-URBAN DELINEATION")
        logger.info("=================================================================")

        # Step 1: Load Stage 1 dataset
        gdf = self.load_stage1_data()

        # Step 2: Delineate masks
        gdf = self.delineate_masks(gdf)

        # Step 3: Validate delineation
        is_valid, metrics = self.validate_delineation(gdf)
        if not is_valid:
            logger.error(f"Stage 2 validation failed! Metrics: {metrics}")
            raise ValueError("Stage 2 urban delineation failed.")

        # Step 4: Export outputs (Parquet for fast stage auditing)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        parquet_out = self.output_dir / "module_1_stage2_delineated.parquet"

        logger.info(f"Saving delineated dataset ({len(gdf)} points) to {parquet_out}...")
        df_export = pd.DataFrame(gdf.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)

        metrics["output_parquet"] = str(parquet_out)

        logger.info(f"Stage 2 complete! Answer: {metrics['status']} - Urban: {metrics['urban_pixel_count']} pts ({metrics['urban_area_km2']} km2), Rural Baseline: {metrics['rural_pixel_count']} pts ({metrics['rural_area_km2']} km2)")
        logger.info("=================================================================")
        return metrics
