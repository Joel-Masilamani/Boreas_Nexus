"""
Boreas-Nexus Boundary Service Module

Downloads administrative city boundary using OSMnx, validates CRS projection,
and exports the boundary as GeoJSON and Shapefile.
"""

from pathlib import Path
from typing import Tuple
import geopandas as gpd
import osmnx as osm

from utils.logger import logger
from utils.config_loader import Config
from utils.helpers import retry_with_backoff, extract_bounding_box
from storage.file_manager import FileManager
from ingestion.metadata_service import MetadataService


class BoundaryService:
    """
    Downloads and manages administrative city boundaries via OpenStreetMap / OSMnx.
    """

    def __init__(
        self,
        config: Config,
        file_manager: FileManager,
        metadata_service: MetadataService
    ):
        self.config = config
        self.city_cfg = config.city
        self.file_manager = file_manager
        self.metadata_service = metadata_service

    @retry_with_backoff(retries=3, backoff_factor=2.0)
    def _fetch_boundary_osmnx(self, query: str) -> gpd.GeoDataFrame:
        """
        Queries OSMnx for administrative boundary geodataframe.
        """
        logger.info(f"Querying OSMnx for boundary: '{query}'")
        gdf = osm.geocode_to_gdf(query)
        if gdf.empty:
            raise ValueError(f"OSMnx returned an empty boundary for query: '{query}'")
        return gdf

    def fetch_and_save_boundary(self) -> Tuple[gpd.GeoDataFrame, Path, Path]:
        """
        Fetches administrative boundary for the configured city, reprojects to configured CRS,
        and saves GeoJSON and Shapefile outputs.

        Returns:
            Tuple of (GeoDataFrame, geojson_path, shapefile_path)
        """
        query_str = self.city_cfg.query_name
        geojson_path = self.file_manager.get_boundary_path("boundary.geojson")
        shapefile_path = self.file_manager.get_boundary_path("boundary.shp")

        if geojson_path.exists() and geojson_path.stat().st_size > 0 and shapefile_path.exists():
            logger.info(f"Boundary file already exists at {geojson_path}. Loading existing boundary.")
            gdf = gpd.read_file(geojson_path)
            bbox = extract_bounding_box(gdf)
            self.metadata_service.create_and_store_metadata(
                dataset_name="city_boundary",
                source="OpenStreetMap via OSMnx",
                provider="OSMnx",
                storage_path=geojson_path,
                projection=self.city_cfg.crs,
                bounding_box=bbox,
                resolution="Vector Polygon",
                license_info="ODbL (Open Database License)",
                version="1.0",
                status="SUCCESS"
            )
            return gdf, geojson_path, shapefile_path

        try:
            gdf = self._fetch_boundary_osmnx(query_str)
        except Exception as e:
            logger.warning(f"Failed to fetch boundary using query '{query_str}': {e}. Retrying with city name only...")
            gdf = self._fetch_boundary_osmnx(self.city_cfg.name)

        # Enforce CRS
        target_crs = self.city_cfg.crs
        if gdf.crs is None:
            gdf.set_crs(target_crs, inplace=True)
        elif str(gdf.crs).upper() != target_crs.upper():
            logger.info(f"Reprojecting boundary from {gdf.crs} to {target_crs}")
            gdf = gdf.to_crs(target_crs)

        # Save GeoJSON
        logger.info(f"Saving boundary GeoJSON to {geojson_path}")
        gdf.to_file(geojson_path, driver="GeoJSON")

        # Save Shapefile directory
        logger.info(f"Saving boundary Shapefile to {shapefile_path}")
        gdf.to_file(shapefile_path, driver="ESRI Shapefile")

        # Record Metadata
        bbox = extract_bounding_box(gdf)
        self.metadata_service.create_and_store_metadata(
            dataset_name="city_boundary",
            source="OpenStreetMap via OSMnx",
            provider="OSMnx",
            storage_path=geojson_path,
            projection=target_crs,
            bounding_box=bbox,
            resolution="Vector Polygon",
            license_info="ODbL (Open Database License)",
            version="1.0",
            status="SUCCESS"
        )

        return gdf, geojson_path, shapefile_path
