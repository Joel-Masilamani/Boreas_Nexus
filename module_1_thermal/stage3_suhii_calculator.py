"""
Boreas-Nexus Module 1 - Stage 3: Surface Urban Heat Island (SUHII) Computation

Purpose: Establish the city's baseline physical Urban Heat Island intensity.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger
from storage.storage_manager import StorageManager


class Stage3SUHIICalculator:
    """
    Computes per-pixel Surface Urban Heat Island Intensity (SUHII) thermal anomalies.
    """

    def __init__(
        self,
        input_delineated_path: Path | str | None = None,
        output_dir: Path | str | None = None
    ):
        self.storage_manager = StorageManager()
        self.input_delineated_path = Path(input_delineated_path) if input_delineated_path is not None else self.storage_manager.get_debug_filepath("module_1", "module_1_stage2_delineated.parquet")
        self.output_dir = Path(output_dir) if output_dir is not None else self.storage_manager.get_debug_dir("module_1")

    def load_stage2_data(self) -> gpd.GeoDataFrame:
        """Loads Stage 2 delineated geospatial dataset."""
        candidates = [
            self.input_delineated_path,
            self.output_dir / "module_1_stage2_delineated.parquet",
            self.storage_manager.get_debug_filepath("module_1", "module_1_stage2_delineated.parquet"),
            self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet"),
            Path("data/processed/features.parquet")
        ]

        target_path = None
        for p in candidates:
            if p.exists():
                target_path = p
                break

        if target_path is not None:
            logger.info(f"Loading delineated data from: {target_path}...")
            df = pd.read_parquet(target_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
            return gdf

        raise FileNotFoundError("Stage 2 dataset not found. Run Stage 2 delineator first.")

    def compute_suhii(self, gdf: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, Dict[str, float]]:
        """Computes per-pixel SUHII anomalies."""
        result_gdf = gdf.copy()
        logger.info("Computing per-pixel Daytime and Nighttime SUHII anomalies...")

        is_rural = result_gdf.get("is_rural", pd.Series(False, index=result_gdf.index)).values
        rural_sub = result_gdf[is_rural]

        if len(rural_sub) == 0:
            logger.warning("No rural pixels found for baseline subtraction! Using domain mean.")
            rural_mean_day = result_gdf["lst_day_celsius"].mean()
            rural_mean_night = result_gdf["lst_night_celsius"].mean()
        else:
            rural_mean_day = float(rural_sub["lst_day_celsius"].mean())
            rural_mean_night = float(rural_sub["lst_night_celsius"].mean())

        result_gdf["suhii_day_celsius"] = result_gdf["lst_day_celsius"] - rural_mean_day
        result_gdf["suhii_night_celsius"] = result_gdf["lst_night_celsius"] - rural_mean_night

        baselines = {
            "rural_mean_day_celsius": round(rural_mean_day, 2),
            "rural_mean_night_celsius": round(rural_mean_night, 2)
        }

        return result_gdf, baselines

    def validate_suhii(
        self,
        gdf: gpd.GeoDataFrame,
        baselines: Dict[str, float]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validates SUHII anomalies."""
        is_urban = gdf.get("is_urban", pd.Series(True, index=gdf.index)).values
        urban_gdf = gdf[is_urban]

        urban_mean_suhii_day = float(urban_gdf["suhii_day_celsius"].mean())
        urban_max_suhii_day = float(urban_gdf["suhii_day_celsius"].max())
        urban_mean_suhii_night = float(urban_gdf["suhii_night_celsius"].mean())
        urban_max_suhii_night = float(urban_gdf["suhii_night_celsius"].max())

        has_physical_uhi = (urban_mean_suhii_day > 0) or (urban_mean_suhii_night > 0)

        metrics = {
            "scientific_question": "Does this city exhibit a physical Urban Heat Island, and how many degrees hotter are specific urban neighborhoods compared to rural areas?",
            "status": "PASSED" if has_physical_uhi else "PASSED_WITH_NO_ANOMALY",
            "physical_uhi_exhibited": has_physical_uhi,
            "rural_mean_day_celsius": baselines["rural_mean_day_celsius"],
            "rural_mean_night_celsius": baselines["rural_mean_night_celsius"],
            "city_baseline_urban_suhii_day_celsius": round(urban_mean_suhii_day, 2),
            "city_max_urban_suhii_day_celsius": round(urban_max_suhii_day, 2),
            "city_baseline_urban_suhii_night_celsius": round(urban_mean_suhii_night, 2),
            "city_max_urban_suhii_night_celsius": round(urban_max_suhii_night, 2),
            "suhii_day_p95_celsius": round(float(np.percentile(urban_gdf["suhii_day_celsius"], 95)), 2),
            "suhii_night_p95_celsius": round(float(np.percentile(urban_gdf["suhii_night_celsius"], 95)), 2)
        }

        return True, metrics

    def run(self) -> Dict[str, Any]:
        """Executes Stage 3 pipeline."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - STAGE 3: SURFACE URBAN HEAT ISLAND (SUHII) COMPUTATION")
        logger.info("=================================================================")

        gdf = self.load_stage2_data()
        gdf, baselines = self.compute_suhii(gdf)
        _, metrics = self.validate_suhii(gdf, baselines)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        parquet_out = self.output_dir / "module_1_stage3_suhii.parquet"
        logger.info(f"Saving SUHII dataset to {parquet_out}...")
        df_export = pd.DataFrame(gdf.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)
        metrics["output_parquet"] = str(parquet_out)

        logger.info(
            f"Stage 3 complete! Answer: {metrics['status']} - Day Urban SUHII: +{metrics['city_baseline_urban_suhii_day_celsius']}°C"
        )
        logger.info("=================================================================")
        return metrics
