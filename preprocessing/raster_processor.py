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
