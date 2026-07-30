"""
Boreas-Nexus Preprocessor Pipeline Module

Orchestrates Phase 2 Preprocessing:
1. Loads raw boundary, vector, elevation, and satellite datasets from data/raw/
2. Builds uniform spatial grid over target city boundary polygon
3. Executes feature extraction (proximity, spectral indices, DEM parameters)
4. Saves processed feature matrix to data/processed/features.parquet & features.geojson
"""

from pathlib import Path
from typing import Dict, Any, Optional
import geopandas as gpd
import pandas as pd

from utils.logger import logger
from utils.config_loader import Config, ConfigLoader
from storage.file_manager import FileManager
from preprocessing.grid_builder import GridBuilder
from preprocessing.feature_extractor import FeatureExtractor
from preprocessing.vector_processor import VectorProcessor


class PreprocessorPipeline:
    """
    Class-based preprocessor orchestrator for Phase 2 Feature Engineering.
    """

    def __init__(self, config_path: Path | str = Path("config/city.yaml")):
        self.config = ConfigLoader.load_config(config_path)
        self.file_manager = FileManager(
            base_raw_dir=self.config.city.output_directory
        )
        self.grid_builder = GridBuilder(target_crs=self.config.preprocessing.target_crs)
        self.feature_extractor = FeatureExtractor(target_crs=self.config.preprocessing.target_crs)

    def load_raw_boundary(self) -> gpd.GeoDataFrame:
        """Loads city boundary GeoJSON from raw data folder."""
        boundary_file = self.file_manager.get_boundary_path("boundary.geojson")
        if not boundary_file.exists():
            raise FileNotFoundError(f"Boundary file not found at {boundary_file}. Execute main.py first.")
        
        logger.info(f"Loading raw boundary dataset from {boundary_file}...")
        return gpd.read_file(boundary_file)

    def load_raw_vector_layers(self) -> Dict[str, gpd.GeoDataFrame]:
        """Loads available vector GeoJSON layers from raw data folder."""
        layers: Dict[str, gpd.GeoDataFrame] = {}
        for layer_name in self.config.ingestion.vector.layers:
            layer_path = self.file_manager.get_vector_path(f"{layer_name}.geojson")
            if layer_path.exists() and layer_path.stat().st_size > 0:
                logger.info(f"Loading raw vector layer '{layer_name}' from {layer_path}...")
                try:
                    layers[layer_name] = gpd.read_file(layer_path)
                except Exception as e:
                    logger.warning(f"Could not load vector layer '{layer_name}': {e}")
        return layers

    def run(self) -> Dict[str, Any]:
        """
        Executes Phase 2 Preprocessing Pipeline.

        Returns:
            Dictionary containing preprocessing summary metrics.
        """
        logger.info("=================================================================")
        logger.info(f"STARTING PHASE 2 PREPROCESSING FOR CITY: {self.config.city.name}")
        logger.info("=================================================================")

        # Step 1: Load boundary
        boundary_gdf = self.load_raw_boundary()

        # Step 2: Generate spatial grid
        res_m = self.config.preprocessing.grid_resolution_meters
        grid_gdf = self.grid_builder.generate_grid_points(boundary_gdf, resolution_meters=res_m)

        # Step 3: Load vector layers
        vector_layers = self.load_raw_vector_layers()

        # Step 4: Extract proximity features
        grid_gdf = self.feature_extractor.extract_proximity_features(grid_gdf, vector_layers)

        # Step 5: Extract spectral features
        satellite_dir = self.file_manager.satellite_dir
        grid_gdf = self.feature_extractor.extract_spectral_features(grid_gdf, satellite_dir)

        # Step 6: Extract DEM terrain features
        elevation_file = self.file_manager.get_elevation_path("dem_elevation.tif")
        grid_gdf = self.feature_extractor.extract_dem_features(grid_gdf, elevation_file)

        # Step 7: Export processed dataset
        processed_dir = self.config.preprocessing.output_directory
        processed_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = processed_dir / "features.parquet"
        geojson_path = processed_dir / "features.geojson"

        logger.info(f"Saving processed feature dataset ({len(grid_gdf)} samples) to {parquet_path}")
        df = pd.DataFrame(grid_gdf.drop(columns=["geometry"]))
        try:
            df.to_parquet(parquet_path, index=False)
        except Exception as e:
            logger.warning(f"Could not save Parquet directly ({e}). Saving CSV fallback.")
            csv_path = processed_dir / "features.csv"
            df.to_csv(csv_path, index=False)

        logger.info(f"Saving processed spatial GeoJSON dataset to {geojson_path}")
        grid_gdf.to_file(geojson_path, driver="GeoJSON")

        summary = {
            "city": self.config.city.name,
            "status": "SUCCESS",
            "grid_resolution_meters": res_m,
            "sample_count": len(grid_gdf),
            "parquet_output": str(parquet_path),
            "geojson_output": str(geojson_path),
            "feature_columns": list(grid_gdf.columns)
        }

        logger.info("=================================================================")
        logger.info(f"PHASE 2 PREPROCESSING FINISHED WITH STATUS: SUCCESS")
        logger.info("=================================================================")
        return summary
