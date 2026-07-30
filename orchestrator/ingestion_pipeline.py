"""
Boreas-Nexus Ingestion Pipeline Orchestrator Module

Class-based orchestrator managing the automated execution flow:
Load Config -> Setup Folders -> Download Boundary -> Satellite -> Vector -> Weather -> Elevation -> Validate -> Generate Metadata.
Continues execution isolated if non-fatal step errors occur.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import time

from utils.logger import logger, setup_logger
from utils.config_loader import ConfigLoader, Config
from storage.file_manager import FileManager
from storage.metadata_store import MetadataStore
from ingestion.metadata_service import MetadataService
from ingestion.boundary_service import BoundaryService
from ingestion.satellite_service import SatelliteService
from ingestion.vector_service import VectorService
from ingestion.weather_service import WeatherService
from ingestion.elevation_service import ElevationService
from preprocessing.validator import DatasetValidator


class IngestionPipeline:
    """
    Class-based Orchestrator for Phase 1 Ingestion Pipeline.
    """

    def __init__(self, config_path: Path | str = Path("config/city.yaml")):
        self.config_path = Path(config_path)
        self.config: Config = ConfigLoader.load_config(self.config_path)
        
        # Initialize storage services
        self.file_manager = FileManager(base_raw_dir=self.config.city.output_directory)
        self.metadata_store = MetadataStore(metadata_path=self.file_manager.get_metadata_path("metadata.json"))
        self.metadata_service = MetadataService(self.file_manager, self.metadata_store)

        # Initialize ingestion services
        self.boundary_service = BoundaryService(self.config, self.file_manager, self.metadata_service)
        self.satellite_service = SatelliteService(self.config, self.file_manager, self.metadata_service)
        self.vector_service = VectorService(self.config, self.file_manager, self.metadata_service)
        self.weather_service = WeatherService(self.config, self.file_manager, self.metadata_service)
        self.elevation_service = ElevationService(self.config, self.file_manager, self.metadata_service)

        # Validator
        self.validator = DatasetValidator(self.config, self.metadata_store)

    def run(self) -> Dict[str, Any]:
        """
        Executes the entire data collection and ingestion pipeline.

        Returns:
            Dictionary containing execution summary status.
        """
        start_time = time.time()
        city_name = self.config.city.name
        logger.info(f"=================================================================")
        logger.info(f"STARTING BOREAS-NEXUS DATA INGESTION PIPELINE FOR CITY: {city_name}")
        logger.info(f"=================================================================")

        summary: Dict[str, Any] = {
            "city": city_name,
            "status": "RUNNING",
            "boundary": None,
            "satellite_files": [],
            "vector_layers": {},
            "weather_file": None,
            "elevation_file": None,
            "validation_report": None,
            "errors": []
        }

        # Step 1 & 2: Folder creation is handled during initialization
        logger.info("Step 1: Configuration loaded and output folder structure prepared.")

        # Step 3: Download Boundary
        logger.info("Step 2: Ingesting City Boundary...")
        try:
            boundary_gdf, geojson_path, shp_path = self.boundary_service.fetch_and_save_boundary()
            summary["boundary"] = str(geojson_path)
            logger.info(f"Boundary download complete: {geojson_path}")
        except Exception as e:
            err_msg = f"Boundary Service Exception: {e}"
            logger.error(err_msg)
            summary["errors"].append(err_msg)
            raise RuntimeError(f"Fatal: Boundary download failed. Cannot proceed without spatial boundary. {e}") from e

        # Step 4: Download Satellite Data
        logger.info("Step 3: Ingesting Satellite Remote Sensing Imagery...")
        try:
            sat_paths = self.satellite_service.execute_downloads(boundary_gdf)
            summary["satellite_files"] = [str(p) for p in sat_paths]
        except Exception as e:
            err_msg = f"Satellite Service Error: {e}"
            logger.error(err_msg)
            summary["errors"].append(err_msg)

        # Step 5: Download Vector Layers
        logger.info("Step 4: Ingesting Vector Spatial Feature Layers (OSMnx)...")
        try:
            vec_map = self.vector_service.execute_vector_ingestion(boundary_gdf)
            summary["vector_layers"] = {k: str(v) for k, v in vec_map.items()}
        except Exception as e:
            err_msg = f"Vector Service Error: {e}"
            logger.error(err_msg)
            summary["errors"].append(err_msg)

        # Step 6: Download Weather Data
        logger.info("Step 5: Ingesting Meteorological Weather Dataset...")
        try:
            weather_path = self.weather_service.execute_weather_ingestion(boundary_gdf)
            summary["weather_file"] = str(weather_path)
        except Exception as e:
            err_msg = f"Weather Service Error: {e}"
            logger.error(err_msg)
            summary["errors"].append(err_msg)

        # Step 7: Download Elevation Data
        logger.info("Step 6: Ingesting Elevation DEM Dataset...")
        try:
            dem_path = self.elevation_service.execute_elevation_ingestion(boundary_gdf)
            summary["elevation_file"] = str(dem_path)
        except Exception as e:
            err_msg = f"Elevation Service Error: {e}"
            logger.error(err_msg)
            summary["errors"].append(err_msg)

        # Step 8: Validate Datasets
        logger.info("Step 7: Executing Dataset Validation Suite...")
        try:
            val_report = self.validator.run_full_validation(self.config.city.output_directory)
            summary["validation_report"] = val_report
        except Exception as e:
            err_msg = f"Validation Error: {e}"
            logger.error(err_msg)
            summary["errors"].append(err_msg)

        elapsed = time.time() - start_time
        summary["execution_time_seconds"] = round(elapsed, 2)
        summary["status"] = "SUCCESS" if len(summary["errors"]) == 0 else "COMPLETED_WITH_ERRORS"

        logger.info(f"=================================================================")
        logger.info(f"PIPELINE INGESTION FINISHED IN {elapsed:.2f}s WITH STATUS: {summary['status']}")
        logger.info(f"=================================================================")
        return summary
