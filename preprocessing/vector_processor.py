"""
Boreas-Nexus Vector Processor Module

Provides spatial preprocessing functions for vector datasets: geometry validation/repair,
CRS reprojection, boundary clipping, and spatial attribute cleaning.
"""

import geopandas as gpd
from shapely.validation import make_valid
from utils.logger import logger


class VectorProcessor:
    """
    Utility class for validating, repairing, reprojecting, and clipping vector layers.
    """

    @staticmethod
    def reproject(gdf: gpd.GeoDataFrame, target_crs: str) -> gpd.GeoDataFrame:
        """
        Reprojects a GeoDataFrame to target CRS.
        """
        if gdf.empty or gdf.crs is None:
            return gdf
        if str(gdf.crs).upper() != str(target_crs).upper():
            logger.debug(f"Reprojecting GeoDataFrame from {gdf.crs} to {target_crs}")
            return gdf.to_crs(target_crs)
        return gdf

    @staticmethod
    def validate_and_repair_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Fixes invalid geometries in a GeoDataFrame using shapely make_valid.
        """
        if gdf.empty:
            return gdf

        invalid_mask = ~gdf.is_valid
        invalid_count = invalid_mask.sum()

        if invalid_count > 0:
            logger.info(f"Repairing {invalid_count} invalid geometries in GeoDataFrame...")
            gdf = gdf.copy()
            gdf["geometry"] = gdf["geometry"].apply(lambda geom: make_valid(geom) if geom is not None else None)

        # Drop null geometries
        gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
        return gdf

    @staticmethod
    def clip_to_boundary(gdf: gpd.GeoDataFrame, boundary_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Clips vector layer geometries to boundary polygon.
        """
        if gdf.empty or boundary_gdf.empty:
            return gdf

        # Ensure matching CRS
        if gdf.crs != boundary_gdf.crs:
            gdf = VectorProcessor.reproject(gdf, str(boundary_gdf.crs))

        logger.debug(f"Clipping GeoDataFrame ({len(gdf)} features) to boundary...")
        try:
            clipped_gdf = gpd.clip(gdf, boundary_gdf)
            return clipped_gdf
        except Exception as e:
            logger.warning(f"Spatial clip operation encountered error: {e}. Returning original GeoDataFrame.")
            return gdf
