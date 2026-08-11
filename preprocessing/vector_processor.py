"""
Boreas-Nexus Vector Processor Module

Provides spatial preprocessing functions for vector datasets: geometry validation/repair,
CRS reprojection, boundary clipping, and high-performance STRtree spatial distance calculations.
"""

from typing import Any
import geopandas as gpd
import pandas as pd
import shapely
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

    @staticmethod
    def compute_distance_to_features(point_gdf: gpd.GeoDataFrame, target_features_gdf: gpd.GeoDataFrame) -> pd.Series:
        """
        Computes minimum Euclidean distance from each point in point_gdf to the nearest geometry
        in target_features_gdf using vectorized Shapely STRtree spatial indexing.
        """
        if point_gdf.empty or target_features_gdf.empty:
            return pd.Series(0.0, index=point_gdf.index)

        # Reproject target features to point CRS if needed
        if target_features_gdf.crs != point_gdf.crs:
            target_features_gdf = VectorProcessor.reproject(target_features_gdf, str(point_gdf.crs))

        # Filter out empty or null geometries from target
        valid_targets = target_features_gdf[target_features_gdf.geometry.notnull() & ~target_features_gdf.geometry.is_empty]
        if valid_targets.empty:
            return pd.Series(0.0, index=point_gdf.index)

        geoms_target = valid_targets.geometry.values
        geoms_point = point_gdf.geometry.values

        # Build high-performance STRtree spatial index
        tree = shapely.STRtree(geoms_target)
        nearest_indices = tree.nearest(geoms_point)
        distances = shapely.distance(geoms_point, geoms_target[nearest_indices])

        return pd.Series(distances, index=point_gdf.index)
