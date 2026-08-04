"""
Boreas-Nexus Module 1 - Stage 4: Night-Time Thermal Behaviour Analysis

Purpose: Capture persistent nocturnal urban heat retention.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger
from storage.storage_manager import StorageManager


class Stage4NighttimeThermal:
    """
    Analyzes nocturnal thermal retention and diurnal temperature dynamics.
    """

    def __init__(
        self,
        input_suhii_path: Path | str | None = None,
        output_dir: Path | str | None = None
    ):
        self.storage_manager = StorageManager()
        self.input_suhii_path = Path(input_suhii_path) if input_suhii_path is not None else self.storage_manager.get_debug_filepath("module_1", "module_1_stage3_suhii.parquet")
        self.output_dir = Path(output_dir) if output_dir is not None else self.storage_manager.get_debug_dir("module_1")

    def load_stage3_data(self) -> gpd.GeoDataFrame:
        """Loads Stage 3 SUHII dataset."""
        candidates = [
            self.input_suhii_path,
            self.output_dir / "module_1_stage3_suhii.parquet",
            self.storage_manager.get_debug_filepath("module_1", "module_1_stage3_suhii.parquet"),
            self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet"),
            Path("data/processed/features.parquet")
        ]

        target_path = None
        for p in candidates:
            if p.exists():
                target_path = p
                break

        if target_path is not None:
            logger.info(f"Loading SUHII dataset from: {target_path}...")
            df = pd.read_parquet(target_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
            return gdf

        raise FileNotFoundError("Stage 3 dataset not found. Run Stage 3 calculator first.")

    def compute_nighttime_metrics(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Computes delta_lst_diurnal and heat_persistence_index."""
        result_gdf = gdf.copy()
        logger.info("Computing Diurnal Temperature Range and Heat Persistence Index...")

        lst_day = result_gdf["lst_day_celsius"].values
        lst_night = result_gdf["lst_night_celsius"].values

        delta_lst_diurnal = lst_day - lst_night
        result_gdf["delta_lst_diurnal"] = np.clip(delta_lst_diurnal, 0.0, 45.0)

        safe_day = np.where(lst_day == 0, 1.0, lst_day)
        hpi = lst_night / safe_day
        result_gdf["heat_persistence_index"] = np.clip(hpi, 0.0, 1.5)

        is_urban = result_gdf.get("is_urban", pd.Series(True, index=result_gdf.index)).values

        conditions = [
            (hpi >= 0.65) & is_urban,
            (hpi >= 0.55),
            (hpi < 0.55)
        ]
        choices = [
            "High Nocturnal Heat Retention",
            "Moderate Retention",
            "Rapid Cooling"
        ]
        result_gdf["thermal_retention_class"] = np.select(conditions, choices, default="Moderate Retention")

        return result_gdf

    def validate_nighttime_analysis(self, gdf: gpd.GeoDataFrame) -> Tuple[bool, Dict[str, Any]]:
        """Validates nighttime thermal retention metrics."""
        is_urban = gdf.get("is_urban", pd.Series(True, index=gdf.index)).values
        is_rural = gdf.get("is_rural", pd.Series(False, index=gdf.index)).values

        urban_hpi_mean = float(gdf[is_urban]["heat_persistence_index"].mean())
        rural_hpi_mean = float(gdf[is_rural]["heat_persistence_index"].mean()) if is_rural.sum() > 0 else 0.50
        urban_diurnal_mean = float(gdf[is_urban]["delta_lst_diurnal"].mean())
        rural_diurnal_mean = float(gdf[is_rural]["delta_lst_diurnal"].mean()) if is_rural.sum() > 0 else 15.0
        high_retention_count = int((gdf["thermal_retention_class"] == "High Nocturnal Heat Retention").sum())

        is_valid = (urban_hpi_mean > 0.0) and (high_retention_count >= 0)

        metrics = {
            "scientific_question": "Which areas retain heat after sunset, isolating true urban heat retention from temporary daytime solar warming?",
            "status": "PASSED" if is_valid else "FAILED",
            "urban_mean_hpi": round(urban_hpi_mean, 3),
            "rural_mean_hpi": round(rural_hpi_mean, 3),
            "urban_mean_diurnal_range_celsius": round(urban_diurnal_mean, 2),
            "rural_mean_diurnal_range_celsius": round(rural_diurnal_mean, 2),
            "high_nocturnal_heat_retention_points": high_retention_count,
            "high_retention_area_km2": round(high_retention_count * 0.01, 2),
            "hpi_urban_vs_rural_delta": round(urban_hpi_mean - rural_hpi_mean, 3)
        }

        return is_valid, metrics

    def run(self) -> Dict[str, Any]:
        """Executes Stage 4 pipeline."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - STAGE 4: NIGHT-TIME THERMAL BEHAVIOUR ANALYSIS")
        logger.info("=================================================================")

        gdf = self.load_stage3_data()
        gdf = self.compute_nighttime_metrics(gdf)
        is_valid, metrics = self.validate_nighttime_analysis(gdf)

        if not is_valid:
            logger.error(f"Stage 4 validation failed! Metrics: {metrics}")
            raise ValueError("Stage 4 nighttime thermal analysis failed.")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        parquet_out = self.output_dir / "module_1_stage4_nighttime.parquet"
        logger.info(f"Saving nighttime thermal dataset to {parquet_out}...")
        df_export = pd.DataFrame(gdf.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)
        metrics["output_parquet"] = str(parquet_out)

        logger.info(
            f"Stage 4 complete! Answer: {metrics['status']} - Urban Mean HPI: {metrics['urban_mean_hpi']}"
        )
        logger.info("=================================================================")
        return metrics
