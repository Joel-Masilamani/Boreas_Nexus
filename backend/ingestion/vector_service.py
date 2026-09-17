"""
Boreas-Nexus Vector Service Module

Downloads OpenStreetMap vector data layers (roads, buildings, water, parks, vegetation,
railways, landuse) clipped to city boundary polygon, saving each as an individual GeoJSON file.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import geopandas as gpd
import osmnx as osm

from utils.logger import logger
from utils.config_loader import Config
from utils.constants import OSM_TAGS
from utils.helpers import retry_with_backoff, extract_bounding_box
from storage.file_manager import FileManager
from ingestion.metadata_service import MetadataService


class VectorService:
    """
    Downloads, processes, and exports vector layers from OpenStreetMap via OSMnx.
    """

    def __init__(
        self,
        config: Config,
        file_manager: FileManager,
        metadata_service: MetadataService
    ):
        self.config = config
        self.file_manager = file_manager
        self.metadata_service = metadata_service

    @retry_with_backoff(retries=3, backoff_factor=2.0)
    def _download_features_by_polygon(
        self,
        polygon,
        tags: Dict[str, Any]
    ) -> gpd.GeoDataFrame:
        """
        Queries OSMnx features_from_polygon using feature tags.
        """
        return osm.features_from_polygon(polygon, tags=tags)

    def download_layer(
        self,
        layer_name: str,
        boundary_gdf: gpd.GeoDataFrame
    ) -> Optional[Path]:
        """
        Downloads a single vector layer (e.g. roads, buildings), reprojects to configured CRS,
        and saves as GeoJSON.
        """
        tags = OSM_TAGS.get(layer_name)
        if not tags:
            logger.warning(f"No OSM tags defined for vector layer '{layer_name}'. Skipping.")
            return None

        output_path = self.file_manager.get_vector_path(f"{layer_name}.geojson")
        
        # Prevent duplicate downloads if file already exists
        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Vector layer '{layer_name}' already exists at {output_path}. Skipping download.")
            bbox = extract_bounding_box(boundary_gdf)
            self.metadata_service.create_and_store_metadata(
                dataset_name=f"vector_{layer_name}",
                source="OpenStreetMap via OSMnx",
                provider="OSMnx",
                storage_path=output_path,
                projection=self.config.city.crs,
                bounding_box=bbox,
                resolution="Existing feature layer",
                license_info="ODbL (Open Database License)",
                version="1.0",
                status="SUCCESS"
            )
            return output_path

        logger.info(f"Downloading vector layer '{layer_name}' via OSMnx...")

        # Extract polygon geometry
        polygon = boundary_gdf.geometry.iloc[0]

        try:
            gdf = self._download_features_by_polygon(polygon, tags)
        except Exception as e:
            logger.warning(f"Failed to query polygon features for layer '{layer_name}': {e}. Creating empty vector placeholder.")
            gdf = gpd.GeoDataFrame(columns=["geometry"], crs=self.config.city.crs)

        if gdf.empty:
            logger.warning(f"Vector layer '{layer_name}' query returned 0 features.")
            gdf = gpd.GeoDataFrame(columns=["geometry"], crs=self.config.city.crs)

        # Reproject CRS if needed
        target_crs = self.config.city.crs
        if gdf.crs is None:
            gdf.set_crs(target_crs, inplace=True)
        elif str(gdf.crs).upper() != target_crs.upper():
            logger.info(f"Reprojecting '{layer_name}' layer to {target_crs}")
            gdf = gdf.to_crs(target_crs)

        # Save to GeoJSON
        logger.info(f"Saving '{layer_name}' vector layer ({len(gdf)} features) to {output_path}")
        gdf.to_file(output_path, driver="GeoJSON")

        # Record metadata
        bbox = extract_bounding_box(gdf) if not gdf.empty else extract_bounding_box(boundary_gdf)
        self.metadata_service.create_and_store_metadata(
            dataset_name=f"vector_{layer_name}",
            source="OpenStreetMap via OSMnx",
            provider="OSMnx",
            storage_path=output_path,
            projection=target_crs,
            bounding_box=bbox,
            resolution=f"{len(gdf)} features",
            license_info="ODbL (Open Database License)",
            version="1.0",
            status="SUCCESS"
        )

        return output_path

    def execute_vector_ingestion(
        self,
        boundary_gdf: gpd.GeoDataFrame
    ) -> Dict[str, Path]:
        """
        Ingests all configured vector layers in sequence.
        """
        requested_layers = self.config.ingestion.vector.layers
        results: Dict[str, Path] = {}

        logger.info(f"Starting vector layers download for layers: {requested_layers}")
        for layer in requested_layers:
            try:
                saved_path = self.download_layer(layer, boundary_gdf)
                if saved_path:
                    results[layer] = saved_path
            except Exception as e:
                logger.error(f"Error downloading vector layer '{layer}': {e}. Continuing with remaining layers.")

        return results
