"""
Boreas-Nexus Coordinate Reference System (CRS) Utilities

Authoritative dynamic UTM zone resolution, PyProj-based coordinate transformations,
and rigorous UTM range validation.
"""

from typing import Tuple
import numpy as np
import pyproj


def get_utm_epsg_for_lon_lat(lon: float, lat: float) -> int:
    """
    Determines the EPSG code for the appropriate UTM zone based on longitude and latitude.
    
    Formula: zone = floor((lon + 180) / 6) + 1
    Northern hemisphere: EPSG:32601 - 32660
    Southern hemisphere: EPSG:32701 - 32760
    """
    zone = int(np.floor((float(lon) + 180.0) / 6.0)) + 1
    zone = max(1, min(60, zone))
    if lat >= 0:
        return 32600 + zone
    return 32700 + zone


def get_utm_crs_for_lon_lat(lon: float, lat: float) -> str:
    """Returns UTM CRS string (e.g. 'EPSG:32644')."""
    return f"EPSG:{get_utm_epsg_for_lon_lat(lon, lat)}"


def transform_wgs84_to_utm(
    lons: np.ndarray | list | float,
    lats: np.ndarray | list | float,
    target_utm_crs: str | None = None
) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Transforms WGS84 (EPSG:4326) coordinates to projected UTM coordinates in meters.
    
    Uses pyproj.Transformer with always_xy=True to guarantee (lon, lat) -> (easting, northing).
    If target_utm_crs is not specified, dynamically computes the UTM zone from the median coordinates.
    
    Returns:
        (utm_x_m, utm_y_m, utm_crs_str)
    """
    lons_arr = np.atleast_1d(np.asarray(lons, dtype=np.float64))
    lats_arr = np.atleast_1d(np.asarray(lats, dtype=np.float64))

    if target_utm_crs is None:
        med_lon = float(np.nanmedian(lons_arr))
        med_lat = float(np.nanmedian(lats_arr))
        target_utm_crs = get_utm_crs_for_lon_lat(med_lon, med_lat)

    transformer = pyproj.Transformer.from_crs("EPSG:4326", target_utm_crs, always_xy=True)
    utm_x, utm_y = transformer.transform(lons_arr, lats_arr)

    return utm_x, utm_y, target_utm_crs


def validate_projected_utm_coords(
    utm_x: np.ndarray | list,
    utm_y: np.ndarray | list,
    utm_crs: str | None = None
) -> Tuple[bool, str]:
    """
    Validates that UTM easting and northing coordinates represent genuine projected meter values.
    
    Checks:
    - Easting (utm_x_m): 100,000m <= x <= 900,000m
    - Northing (utm_y_m): 0m <= y <= 10,000,000m
    - No artificial degree-multiplying artifacts (e.g. 80.27 * 100000 = 8027000)
    """
    xs = np.asarray(utm_x, dtype=np.float64)
    ys = np.asarray(utm_y, dtype=np.float64)

    if len(xs) == 0 or len(ys) == 0:
        return False, "Empty coordinate arrays provided."

    if np.isnan(xs).any() or np.isnan(ys).any():
        return False, "NaN values found in UTM coordinates."

    min_x, max_x = float(np.min(xs)), float(np.max(xs))
    min_y, max_y = float(np.min(ys)), float(np.max(ys))

    # Check for artificial multiplier artifacts
    if max_x > 1_000_000.0 or min_x < 50_000.0:
        return False, f"Invalid UTM easting range [{min_x:.1f}, {max_x:.1f}] m (expected ~100,000 - 900,000 m)."

    if min_y < 0.0 or max_y > 10_000_000.0:
        return False, f"Invalid UTM northing range [{min_y:.1f}, {max_y:.1f}] m (expected ~0 - 10,000,000 m)."

    return True, "Valid UTM coordinates."
