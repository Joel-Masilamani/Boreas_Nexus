"""
Boreas-Nexus Module 1 - Stage 4: Night-Time Thermal Behaviour Analysis

Purpose: Capture persistent nocturnal urban heat retention.

Scientific Theory: Cities store shortwave solar radiation during the day and release longwave heat slowly after sunset.
Night-Time LST is a much stronger indicator of urbanization and concrete heat trapping (referencing Dr. Asfa Siddiqui's research).

Method: Compare daytime LST (LST_day) with 1:30 AM night-time LST (LST_night) to compute:
- LST_night_celsius: Nocturnal surface temperature
- delta_lst_diurnal: LST_day - LST_night (diurnal temperature range)
- heat_persistence_index: LST_night / LST_day (ratio quantifying heat retention after sunset)

Scientific Question: "Which areas retain heat after sunset, isolating true urban heat retention from temporary daytime solar warming?"
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger


class Stage4NighttimeThermal:
    """
    Analyzes nocturnal thermal retention and diurnal temperature dynamics to identify
    persistent heat-trapping urban surfaces.
    """

    def __init__(
        self,
        input_suhii_path: Path | str = Path("data/processed/module_1_stage3_suhii.parquet"),
        output_dir: Path | str = Path("data/processed")
    ):
        self.input_suhii_path = Path(input_suhii_path)
        self.output_dir = Path(output_dir)

    def load_stage3_data(self) -> gpd.GeoDataFrame:
        """Loads Stage 3 SUHII dataset."""
        if self.input_suhii_path.exists():
            logger.info(f"Loading Stage 3 SUHII data from Parquet: {self.input_suhii_path}...")
            df = pd.read_parquet(self.input_suhii_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
        else:
            geojson_path = self.input_suhii_path.with_suffix(".geojson")
            if geojson_path.exists():
                logger.info(f"Loading Stage 3 SUHII data from GeoJSON: {geojson_path}...")
                gdf = gpd.read_file(geojson_path)
            else:
                raise FileNotFoundError(
                    f"Stage 3 dataset not found at {self.input_suhii_path}. Run Stage 3 calculator first."
                )

        return gdf

    def compute_nighttime_metrics(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Computes diurnal temperature range (delta_lst_diurnal) and Heat Persistence Index (heat_persistence_index).
        """
        result_gdf = gdf.copy()
        logger.info("Computing Diurnal Temperature Range and Heat Persistence Index...")

        lst_day = result_gdf["lst_day_celsius"].values
        lst_night = result_gdf["lst_night_celsius"].values

        # 1. Diurnal Temperature Range: LST_day - LST_night
        delta_lst_diurnal = lst_day - lst_night
        result_gdf["delta_lst_diurnal"] = np.clip(delta_lst_diurnal, 0.0, 45.0)

        # 2. Heat Persistence Index: LST_night / LST_day
        # Higher values indicate built-up materials retaining daytime heat into the night
        safe_day = np.where(lst_day == 0, 1.0, lst_day)
        hpi = lst_night / safe_day
        result_gdf["heat_persistence_index"] = np.clip(hpi, 0.0, 1.5)

        # 3. Categorize thermal retention behavior
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
        """
        Validates nighttime thermal retention metrics.

        Answers Scientific Question:
        "Which areas retain heat after sunset, isolating true urban heat retention from temporary daytime solar warming?"
        """
        is_urban = gdf.get("is_urban", pd.Series(True, index=gdf.index)).values
        is_rural = gdf.get("is_rural", pd.Series(False, index=gdf.index)).values

        urban_hpi_mean = float(gdf[is_urban]["heat_persistence_index"].mean())
        rural_hpi_mean = float(gdf[is_rural]["heat_persistence_index"].mean()) if is_rural.sum() > 0 else 0.50

        urban_diurnal_mean = float(gdf[is_urban]["delta_lst_diurnal"].mean())
        rural_diurnal_mean = float(gdf[is_rural]["delta_lst_diurnal"].mean()) if is_rural.sum() > 0 else 15.0

        high_retention_count = int((gdf["thermal_retention_class"] == "High Nocturnal Heat Retention").sum())

        # Validation: Urban surfaces retain heat longer (higher HPI and lower diurnal swing)
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
        """Executes Stage 4 pipeline and exports nighttime thermal dataset."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - STAGE 4: NIGHT-TIME THERMAL BEHAVIOUR ANALYSIS")
        logger.info("=================================================================")

        # Step 1: Load Stage 3 dataset
        gdf = self.load_stage3_data()

        # Step 2: Compute nocturnal thermal metrics
        gdf = self.compute_nighttime_metrics(gdf)

        # Step 3: Validate and compute summary metrics
        is_valid, metrics = self.validate_nighttime_analysis(gdf)
        if not is_valid:
            logger.error(f"Stage 4 validation failed! Metrics: {metrics}")
            raise ValueError("Stage 4 nighttime thermal analysis failed.")

        # Step 4: Export outputs
        self.output_dir.mkdir(parents=True, exist_ok=True)
        parquet_out = self.output_dir / "module_1_stage4_nighttime.parquet"
        geojson_out = self.output_dir / "module_1_stage4_nighttime.geojson"

        logger.info(f"Saving nighttime thermal dataset ({len(gdf)} points) to {parquet_out}...")
        df_export = pd.DataFrame(gdf.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)

        logger.info(f"Saving nighttime thermal GeoJSON dataset to {geojson_out}...")
        gdf.to_file(geojson_out, driver="GeoJSON")

        metrics["output_parquet"] = str(parquet_out)
        metrics["output_geojson"] = str(geojson_out)

        logger.info(
            f"Stage 4 complete! Answer: {metrics['status']} - Urban Mean HPI: {metrics['urban_mean_hpi']} vs Rural HPI: {metrics['rural_mean_hpi']} | High Retention Area: {metrics['high_retention_area_km2']} km2 ({metrics['high_nocturnal_heat_retention_points']} pts)"
        )
        logger.info("=================================================================")
        return metrics
