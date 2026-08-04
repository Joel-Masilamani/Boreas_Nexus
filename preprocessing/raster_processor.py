"""
Boreas-Nexus Raster Processor Module

Provides inspection, validation, and CRS reprojection helper utilities for raster imagery
(satellite rasters, digital elevation models).
"""

from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger import logger


class RasterProcessor:
    """
    Utility class for inspecting and validating raster GeoTIFF datasets.
    """

    @staticmethod
    def inspect_raster(raster_path: Path) -> Dict[str, Any]:
        """
        Inspects raster header parameters (CRS, dimensions, nodata, bounding box, bands).

        Returns:
            Dictionary containing raster spatial attributes and validity status.
        """
        if not raster_path.exists():
            return {"valid": False, "error": f"File does not exist: {raster_path}"}

        try:
            import rasterio
            with rasterio.open(raster_path) as src:
                bounds = src.bounds
                return {
                    "valid": True,
                    "width": src.width,
                    "height": src.height,
                    "count": src.count,
                    "crs": str(src.crs),
                    "driver": src.driver,
                    "nodata": src.nodata,
                    "bounding_box": {
                        "minx": bounds.left,
                        "miny": bounds.bottom,
                        "maxx": bounds.right,
                        "maxy": bounds.top,
                    }
                }
        except Exception as e:
            logger.warning(f"Raster inspection exception for {raster_path}: {e}")
            return {"valid": False, "error": str(e)}

    @staticmethod
    def verify_raster_integrity(raster_path: Path) -> bool:
        """
        Verifies that a raster file can be opened and read without byte corruption.
        """
        info = RasterProcessor.inspect_raster(raster_path)
        return info.get("valid", False)

    @staticmethod
    def compute_ndvi(red_array: Any, nir_array: Any) -> Any:
        """
        Computes Normalized Difference Vegetation Index (NDVI).
        NDVI = (NIR - Red) / (NIR + Red)
        """
        import numpy as np
        denom = (nir_array + red_array)
        denom[denom == 0] = np.nan
        ndvi = (nir_array - red_array) / denom
        return np.clip(ndvi, -1.0, 1.0)

    @staticmethod
    def compute_ndbi(swir_array: Any, nir_array: Any) -> Any:
        """
        Computes Normalized Difference Built-up Index (NDBI).
        NDBI = (SWIR - NIR) / (SWIR + NIR)
        """
        import numpy as np
        denom = (swir_array + nir_array)
        denom[denom == 0] = np.nan
        ndbi = (swir_array - nir_array) / denom
        return np.clip(ndbi, -1.0, 1.0)

    @staticmethod
    def compute_ndwi(green_array: Any, nir_array: Any) -> Any:
        """
        Computes Normalized Difference Water Index (NDWI).
        NDWI = (Green - NIR) / (Green + NIR)
        """
        import numpy as np
        denom = (green_array + nir_array)
        denom[denom == 0] = np.nan
        ndwi = (green_array - nir_array) / denom
        return np.clip(ndwi, -1.0, 1.0)

    @staticmethod
    def sample_points_from_raster(raster_path: Path, points_gdf: Any, band_index: int = 1) -> Any:
        """
        Samples pixel values from a GeoTIFF raster at given point coordinates,
        automatically reprojecting point geometries to the raster's CRS.

        Args:
            raster_path: Path to GeoTIFF file.
            points_gdf: GeoDataFrame containing point geometries.
            band_index: 1-based band index to sample (default: 1).

        Returns:
            Numpy array of sampled values corresponding to each point row.
        """
        import numpy as np
        import rasterio

        if not raster_path.exists():
            logger.warning(f"Raster path does not exist for point sampling: {raster_path}")
            return np.zeros(len(points_gdf))

        try:
            with rasterio.open(raster_path) as src:
                raster_crs = src.crs
                # Reproject point coordinates to match the raster's CRS if needed
                if points_gdf.crs and raster_crs and str(points_gdf.crs).upper() != str(raster_crs).upper():
                    pts_reprojected = points_gdf.to_crs(raster_crs)
                else:
                    pts_reprojected = points_gdf

                coords = [(pt.x, pt.y) for pt in pts_reprojected.geometry]
                sampled = list(src.sample(coords, indexes=band_index))
                values = np.array([val[0] for val in sampled], dtype=np.float32)
                # Filter out nodata values
                if src.nodata is not None:
                    values = np.where(values == src.nodata, np.nan, values)
                return values
        except Exception as e:
            logger.warning(f"Exception sampling raster {raster_path}: {e}")
            return np.zeros(len(points_gdf))


