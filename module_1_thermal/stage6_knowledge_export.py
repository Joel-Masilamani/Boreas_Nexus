"""
Boreas-Nexus Module 1 - Stage 6: Urban Heat Hotspot Knowledge Layer Export

Purpose: Merge all validated outputs into a unified geospatial knowledge layer.

Schema:
Urban Mask + SUHII + Night-Time Heat Persistence + Getis-Ord Gi* Clusters -> Urban Heat Hotspot Knowledge Layer

Next Module Integration: This layer is exported to Parquet/GeoJSON and consumed by
Module 2 (Urban Heat Driver Intelligence Engine) to attribute physical heat to urban drivers.
"""

from pathlib import Path
from typing import Dict, Any
import json
import pandas as pd
import geopandas as gpd

from utils.logger import logger
from utils.config_loader import ConfigLoader


class Stage6KnowledgeExporter:
    """
    Exports the final unified Urban Heat Hotspot Knowledge Layer and Module 1 metadata manifest.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/city.yaml"),
        input_hotspot_path: Path | str = Path("data/processed/module_1_stage5_hotspots.parquet"),
        output_dir: Path | str = Path("data/processed"),
        metadata_dir: Path | str = Path("data/metadata")
    ):
        self.config_path = Path(config_path)
        self.config = ConfigLoader.load_config(self.config_path)
        self.input_hotspot_path = Path(input_hotspot_path)
        self.output_dir = Path(output_dir)
        self.metadata_dir = Path(metadata_dir)

    def load_stage5_data(self) -> gpd.GeoDataFrame:
        """Loads Stage 5 hotspot dataset."""
        if self.input_hotspot_path.exists():
            logger.info(f"Loading Stage 5 hotspot data from Parquet: {self.input_hotspot_path}...")
            df = pd.read_parquet(self.input_hotspot_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
        else:
            geojson_path = self.input_hotspot_path.with_suffix(".geojson")
            if geojson_path.exists():
                logger.info(f"Loading Stage 5 hotspot data from GeoJSON: {geojson_path}...")
                gdf = gpd.read_file(geojson_path)
            else:
                raise FileNotFoundError(
                    f"Stage 5 dataset not found at {self.input_hotspot_path}. Run Stage 5 first."
                )

        return gdf

    def build_knowledge_layer(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Consolidates and orders all attributes for the Knowledge Layer.
        """
        result_gdf = gdf.copy()
        logger.info("Structuring final Urban Heat Hotspot Knowledge Layer...")

        primary_cols = [
            "point_id", "latitude", "longitude", "utm_x_m", "utm_y_m",
            "surface_class", "is_urban", "is_rural", "is_water", "land_cover_code",
            "lst_day_celsius", "lst_night_celsius", "suhii_day_celsius", "suhii_night_celsius",
            "delta_lst_diurnal", "heat_persistence_index", "thermal_retention_class",
            "gi_zscore_day", "gi_pvalue_day", "gi_zscore_night", "gi_pvalue_night",
            "is_hotspot_day_95", "is_hotspot_day_99", "is_hotspot_night_95", "is_hotspot_night_99",
            "is_validated_hotspot", "hotspot_classification"
        ]

        # Add additional domain attributes if available
        additional_cols = [
            col for col in result_gdf.columns
            if col not in primary_cols and col != "geometry"
        ]

        final_cols = primary_cols + additional_cols + ["geometry"]
        ordered_cols = [c for c in final_cols if c in result_gdf.columns]

        return result_gdf[ordered_cols]

    def create_manifest(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Generates Module 1 scientific metadata manifest."""
        n_total = len(gdf)
        n_urban = int(gdf["is_urban"].sum()) if "is_urban" in gdf.columns else 0
        n_rural = int(gdf["is_rural"].sum()) if "is_rural" in gdf.columns else 0
        n_validated = int(gdf["is_validated_hotspot"].sum()) if "is_validated_hotspot" in gdf.columns else 0
        n_persistent_99 = int((gdf["is_hotspot_day_99"] & gdf["is_hotspot_night_99"]).sum()) if ("is_hotspot_day_99" in gdf.columns and "is_hotspot_night_99" in gdf.columns) else 0

        manifest = {
            "city_name": self.config.city.name,
            "module_id": "module_1_thermal",
            "module_name": "Module 1: Physical Urban Heat & Hotspot Intelligence Engine",
            "status": "SUCCESS",
            "total_sample_points": n_total,
            "urban_area_km2": round(n_urban * 0.01, 2),
            "rural_baseline_area_km2": round(n_rural * 0.01, 2),
            "validated_hotspot_area_km2": round(n_validated * 0.01, 2),
            "persistent_99pct_hotspot_area_km2": round(n_persistent_99 * 0.01, 2),
            "urban_mean_day_suhii_celsius": round(float(gdf[gdf["is_urban"]]["suhii_day_celsius"].mean()), 2) if n_urban > 0 else 0.0,
            "urban_mean_night_suhii_celsius": round(float(gdf[gdf["is_urban"]]["suhii_night_celsius"].mean()), 2) if n_urban > 0 else 0.0,
            "knowledge_layer_parquet": str(self.output_dir / "urban_heat_hotspot_knowledge_layer.parquet"),
            "knowledge_layer_geojson": str(self.output_dir / "urban_heat_hotspot_knowledge_layer.geojson"),
            "consumed_by_next_module": "Module 2: Urban Heat Driver Intelligence Engine"
        }

        return manifest

    def run(self) -> Dict[str, Any]:
        """Executes Stage 6 pipeline and exports the final Knowledge Layer."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - STAGE 6: URBAN HEAT HOTSPOT KNOWLEDGE LAYER EXPORT")
        logger.info("=================================================================")

        # Step 1: Load Stage 5 dataset
        gdf = self.load_stage5_data()

        # Step 2: Consolidate Knowledge Layer
        knowledge_gdf = self.build_knowledge_layer(gdf)

        # Step 3: Export Parquet & GeoJSON
        self.output_dir.mkdir(parents=True, exist_ok=True)
        parquet_out = self.output_dir / "urban_heat_hotspot_knowledge_layer.parquet"
        geojson_out = self.output_dir / "urban_heat_hotspot_knowledge_layer.geojson"

        logger.info(f"Saving final Knowledge Layer ({len(knowledge_gdf)} points) to Parquet: {parquet_out}...")
        df_export = pd.DataFrame(knowledge_gdf.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)

        logger.info(f"Saving final Knowledge Layer GeoJSON: {geojson_out}...")
        knowledge_gdf.to_file(geojson_out, driver="GeoJSON")

        # Step 4: Export Manifest
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        manifest = self.create_manifest(knowledge_gdf)
        manifest_path = self.metadata_dir / "module_1_manifest.json"

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Saved Module 1 manifest to {manifest_path}")

        logger.info("=================================================================")
        logger.info(f"MODULE 1 COMPLETE! Urban Heat Hotspot Knowledge Layer ready.")
        logger.info("=================================================================")
        return manifest
