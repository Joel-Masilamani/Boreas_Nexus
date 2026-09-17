"""
Boreas-Nexus Land Cover Service Module

Ingests ESA WorldCover 10m land cover classification rasters via Planetary Computer STAC API.
Maps land cover classes: Tree cover (10), Shrubland (20), Grassland (30), Cropland (40),
Built-up (50), Bare / sparse vegetation (60), Water bodies (80), Mangroves (95).
"""

from pathlib import Path
from typing import Dict, Any, Optional
import geopandas as gpd

from utils.logger import logger
from utils.config_loader import Config
from utils.helpers import extract_bounding_box
from storage.file_manager import FileManager
from ingestion.metadata_service import MetadataService
from ingestion.stac_fetcher import fetch_esa_worldcover_raster


class LandCoverService:
    """Orchestrates land cover dataset ingestion."""

    def __init__(
        self,
        config: Config,
        file_manager: FileManager,
        metadata_service: MetadataService
    ):
        self.config = config
        self.file_manager = file_manager
        self.metadata_service = metadata_service

    def execute_landcover_ingestion(self, boundary_gdf: gpd.GeoDataFrame) -> Path:
        output_dir = Path(self.config.city.output_directory) / "landcover"
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / "landcover_worldcover.tif"

        logger.info("Executing Land Cover ingestion via ESA WorldCover 10m STAC provider...")
        saved_path = fetch_esa_worldcover_raster(boundary_gdf, target_path)

        bbox = extract_bounding_box(boundary_gdf)
        self.metadata_service.create_and_store_metadata(
            dataset_name="esa_worldcover_10m",
            source="ESA WorldCover 10m v200",
            provider="esa_planetary_computer",
            storage_path=saved_path,
            projection=self.config.city.crs,
            bounding_box=bbox,
            resolution="10m Land Cover Classification",
            license_info="CC-BY 4.0",
            version="2020/2021",
            status="SUCCESS"
        )
        return saved_path
