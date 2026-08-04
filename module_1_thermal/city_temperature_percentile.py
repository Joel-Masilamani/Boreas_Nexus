"""
Boreas-Nexus Module 1 - City Temperature Percentile (Part 3 Extension)

Purpose: Compute per-pixel relative thermal percentile ranking across valid land surfaces
within the study area, ignoring water bodies and NoData values.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.stats import rankdata

from utils.logger import logger
from storage.storage_manager import StorageManager


class CityTemperaturePercentileCalculator:
    """
    Calculates relative daytime temperature percentiles and ranks across valid city land pixels.
    """

    def __init__(
        self,
        input_path: Path | str | None = None,
        output_dir: Path | str | None = None
    ):
        self.storage_manager = StorageManager()
        self.input_path = Path(input_path) if input_path is not None else self.storage_manager.get_debug_filepath("module_1", "module_1_stage5_labeled.parquet")
        self.output_dir = Path(output_dir) if output_dir is not None else self.storage_manager.get_debug_dir("module_1")

    def load_input_data(self) -> gpd.GeoDataFrame:
        """Loads intermediate point dataset."""
        candidates = [
            self.input_path,
            self.output_dir / "module_1_stage5_labeled.parquet",
            self.storage_manager.get_debug_filepath("module_1", "module_1_stage5_labeled.parquet"),
            self.storage_manager.get_debug_filepath("module_1", "module_1_stage5_hotspots.parquet"),
            self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet"),
            Path("data/processed/features.parquet")
        ]

        target_path = None
        for p in candidates:
            if p.exists():
                target_path = p
                break

        if target_path is not None:
            logger.info(f"Loading input dataset from: {target_path}...")
            df = pd.read_parquet(target_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
            return gdf

        raise FileNotFoundError(f"Input dataset not found at {self.input_path}.")

    def compute_percentiles(
        self,
        gdf: gpd.GeoDataFrame,
        mask_water: bool = True,
        mask_non_urban: bool = False
    ) -> gpd.GeoDataFrame:
        """Computes city_temperature_percentile, temperature_rank, and temperature_total_pixels."""
        result_gdf = gdf.copy()
        logger.info("Computing City Temperature Percentiles across study area...")

        lst_day = result_gdf["lst_day_celsius"].values
        valid_mask = ~np.isnan(lst_day)

        if mask_water and "is_water" in result_gdf.columns:
            valid_mask = valid_mask & (~result_gdf["is_water"].values.astype(bool))

        if mask_non_urban and "is_urban" in result_gdf.columns:
            valid_mask = valid_mask & (result_gdf["is_urban"].values.astype(bool))

        valid_lst = lst_day[valid_mask]
        n_valid = len(valid_lst)
        logger.info(f"Evaluated {n_valid} valid land pixels out of {len(result_gdf)} total sample points.")

        percentiles = np.full(len(result_gdf), np.nan)
        ranks = np.full(len(result_gdf), np.nan)
        totals = np.full(len(result_gdf), n_valid, dtype=int)

        if n_valid > 0:
            rank_vals = rankdata(valid_lst, method="min")
            if n_valid > 1:
                pct_vals = ((rankdata(valid_lst, method="average") - 1.0) / (n_valid - 1.0)) * 100.0
            else:
                pct_vals = np.full(n_valid, 100.0)

            percentiles[valid_mask] = np.round(np.clip(pct_vals, 0.0, 100.0), 2)
            ranks[valid_mask] = rank_vals.astype(int)

        result_gdf["city_temperature_percentile"] = percentiles
        result_gdf["temperature_rank"] = ranks
        result_gdf["temperature_total_pixels"] = totals

        return result_gdf

    def run(self) -> Dict[str, Any]:
        """Executes City Temperature Percentile Calculator."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - EXTENSION 3: CITY TEMPERATURE PERCENTILE")
        logger.info("=================================================================")

        gdf = self.load_input_data()
        gdf_pct = self.compute_percentiles(gdf)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        parquet_out = self.output_dir / "module_1_stage5_pct.parquet"
        logger.info(f"Saving percentile dataset to {parquet_out}...")
        df_export = pd.DataFrame(gdf_pct.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)

        metrics = {
            "status": "SUCCESS",
            "evaluated_land_pixels": int((gdf_pct["city_temperature_percentile"].notnull()).sum()),
            "total_pixels": len(gdf_pct),
            "max_percentile": float(np.nanmax(gdf_pct["city_temperature_percentile"])) if (gdf_pct["city_temperature_percentile"].notnull()).any() else 0.0,
            "min_percentile": float(np.nanmin(gdf_pct["city_temperature_percentile"])) if (gdf_pct["city_temperature_percentile"].notnull()).any() else 0.0,
            "output_parquet": str(parquet_out)
        }

        logger.info(f"City Temperature Percentile complete! Evaluated {metrics['evaluated_land_pixels']} pixels.")
        logger.info("=================================================================")
        return metrics
