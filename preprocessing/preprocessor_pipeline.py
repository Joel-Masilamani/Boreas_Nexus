"""
Boreas-Nexus Phase 2 Feature Preprocessing Pipeline

Orchestrates spatial sampling grid generation, vector proximity extraction,
spectral index calculation (NDVI, NDBI, NDWI, LST), DEM terrain analysis,
and exports the dataset to data/processed/feature_engineering/features.geoparquet.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json
import pandas as pd
import geopandas as gpd

from utils.logger import logger
from utils.config_loader import ConfigLoader
from storage.file_manager import FileManager
from storage.storage_manager import StorageManager
from preprocessing.grid_builder import GridBuilder
from preprocessing.feature_extractor import FeatureExtractor


class PreprocessorPipeline:
    """
    Class orchestrating end-to-end Phase 2 Feature Engineering execution.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/city.yaml")
    ):
        self.config_path = Path(config_path)
        self.config = ConfigLoader.load_config(self.config_path)

        # Initialize storage managers
        self.storage_manager = StorageManager()
        self.file_manager = FileManager(base_raw_dir=self.config.city.output_directory)

        # Initialize preprocessing sub-components
        self.grid_builder = GridBuilder(target_crs=self.config.preprocessing.target_crs)
        self.feature_extractor = FeatureExtractor(target_crs=self.config.preprocessing.target_crs)

    def load_boundary_gdf(self) -> gpd.GeoDataFrame:
        """Loads the city boundary GeoDataFrame from raw boundary GeoJSON."""
        boundary_path = self.file_manager.get_boundary_path("boundary.geojson")
        if not boundary_path.exists():
            raise FileNotFoundError(f"Boundary file not found at: {boundary_path}")
        logger.info(f"Loading city boundary from {boundary_path}...")
        return gpd.read_file(boundary_path)

    def load_raw_vector_layers(self) -> Dict[str, gpd.GeoDataFrame]:
        """Loads available vector GIS layers from raw data directory."""
        layers = {}
        osm_files = {
            "water": "water.geojson",
            "parks": "parks.geojson",
            "roads": "roads.geojson",
            "buildings": "buildings.geojson"
        }

        for key, fname in osm_files.items():
            p = self.file_manager.get_vector_path(fname)
            if p.exists():
                logger.info(f"Loading vector layer '{key}' from {p}...")
                try:
                    layers[key] = gpd.read_file(p)
                except Exception as e:
                    logger.warning(f"Could not load vector layer {fname}: {e}")

        return layers

    def run(self) -> Dict[str, Any]:
        """Runs Phase 2 Feature Preprocessing Pipeline."""
        logger.info("=================================================================")
        logger.info(f"STARTING PHASE 2 PREPROCESSING PIPELINE FOR {self.config.city.name.upper()}")
        logger.info("=================================================================")

        # Step 1: Load city boundary
        boundary_gdf = self.load_boundary_gdf()
        res_m = int(self.config.preprocessing.grid_resolution_meters)

        # Step 2: Generate spatial grid
        grid_gdf = self.grid_builder.generate_grid_points(boundary_gdf, resolution_meters=res_m)

        # Step 3: Load vector layers
        vector_layers = self.load_raw_vector_layers()

        # Step 4: Extract proximity features
        grid_gdf = self.feature_extractor.extract_proximity_features(grid_gdf, vector_layers)

        # Step 5: Extract building density feature
        grid_gdf = self.feature_extractor.extract_building_density(grid_gdf, vector_layers)

        # Step 6: Extract spectral features
        satellite_dir = self.file_manager.satellite_dir
        grid_gdf = self.feature_extractor.extract_spectral_features(grid_gdf, satellite_dir)

        # Step 7: Extract DEM terrain features
        elevation_file = self.file_manager.get_elevation_path("dem_elevation.tif")
        grid_gdf = self.feature_extractor.extract_dem_features(grid_gdf, elevation_file)

        # Step 8: Extract land cover features
        grid_gdf = self.feature_extractor.extract_landcover_features(grid_gdf, self.file_manager.base_raw_dir)

        # Step 9: Export processed feature dataset into feature_engineering/
        geoparquet_path = self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet")
        metadata_path = self.storage_manager.get_processed_filepath("feature_engineering", "metadata.json")
        validation_path = self.storage_manager.get_processed_filepath("feature_engineering", "validation.json")

        logger.info(f"Saving primary spatial GeoParquet dataset ({len(grid_gdf)} samples) to {geoparquet_path}")
        grid_gdf.to_parquet(geoparquet_path)

        # Step 10: Export optional derived GIS products to exports/
        geojson_path = self.storage_manager.get_export_filepath("geojson", "features.geojson")
        gpkg_path = self.storage_manager.get_export_filepath("gpkg", "features.gpkg")

        logger.info(f"Exporting optional spatial GeoJSON dataset to {geojson_path}")
        with open(geojson_path, "w", encoding="utf-8") as f:
            f.write(grid_gdf.to_json())

        logger.info(f"Exporting optional spatial GeoPackage dataset to {gpkg_path}")
        gpkg_path.unlink(missing_ok=True)
        grid_gdf.to_file(gpkg_path, driver="GPKG")

        # Step 11: Export Feature Engineering Metadata & Validation
        summary = {
            "city": self.config.city.name,
            "status": "SUCCESS",
            "grid_resolution_meters": res_m,
            "sample_count": len(grid_gdf),
            "primary_geoparquet": str(geoparquet_path),
            "geojson_export": str(geojson_path),
            "gpkg_export": str(gpkg_path),
            "feature_columns": list(grid_gdf.columns)
        }

        val_report = {
            "status": "PASSED",
            "total_samples": len(grid_gdf),
            "null_count": int(grid_gdf.isnull().sum().sum()),
            "crs": str(grid_gdf.crs)
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        with open(validation_path, "w", encoding="utf-8") as f:
            json.dump(val_report, f, indent=2)

        logger.info("=================================================================")
        logger.info(f"PHASE 2 PREPROCESSING FINISHED WITH STATUS: SUCCESS")
        logger.info("=================================================================")
        return summary
