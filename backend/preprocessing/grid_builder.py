"""
Boreas-Nexus Spatial Grid Builder Module

Generates a uniform spatial grid (regular point or polygon grid) across a city
boundary polygon at specified spatial resolution (e.g. 30m, 100m).
"""

from typing import Tuple
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon, box

from utils.logger import logger
from utils.helpers import extract_bounding_box


class GridBuilder:
    """
    Constructs regular spatial grid points and bounding cells over a target boundary polygon.
    """

    def __init__(self, target_crs: str = "EPSG:4326"):
        self.target_crs = target_crs

    def generate_grid_points(
        self,
        boundary_gdf: gpd.GeoDataFrame,
        resolution_meters: int = 100
    ) -> gpd.GeoDataFrame:
        """
        Generates a regular grid of sample points over the boundary polygon.

        Args:
            boundary_gdf: City boundary GeoDataFrame.
            resolution_meters: Approximate grid spacing in meters.

        Returns:
            GeoDataFrame containing grid point geometries with unique point IDs.
        """
        if boundary_gdf.empty:
            logger.warning("Empty boundary GeoDataFrame provided to GridBuilder.")
            return gpd.GeoDataFrame(columns=["point_id", "geometry"], crs=self.target_crs)

        bbox = extract_bounding_box(boundary_gdf)
        polygon = boundary_gdf.geometry.iloc[0]

        # Convert resolution in meters to approximate degrees (~111,000m per degree latitude)
        deg_step = resolution_meters / 111000.0

        x_coords = np.arange(bbox["minx"], bbox["maxx"], deg_step)
        y_coords = np.arange(bbox["miny"], bbox["maxy"], deg_step)

        grid_points = []
        point_id = 1

        for x in x_coords:
            for y in y_coords:
                pt = Point(x, y)
                if polygon.contains(pt) or polygon.intersects(pt):
                    grid_points.append({"point_id": f"pt_{point_id:06d}", "geometry": pt})
                    point_id += 1

        grid_gdf = gpd.GeoDataFrame(grid_points, crs=boundary_gdf.crs)

        if str(grid_gdf.crs).upper() != self.target_crs.upper():
            grid_gdf = grid_gdf.to_crs(self.target_crs)

        logger.info(
            f"Generated spatial grid: {len(grid_gdf)} points at {resolution_meters}m resolution "
            f"over city boundary."
        )
        return grid_gdf
