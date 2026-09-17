"""
Boreas-Nexus Utility Helpers Module

Provides retry logic with exponential backoff, SHA-256 checksum computation,
file size inspection, and geometry bounding box extraction utilities.
"""

import hashlib
import time
import functools
from pathlib import Path
from typing import Callable, Any, Tuple, Optional, Dict
import geopandas as gpd

from utils.logger import logger


def retry_with_backoff(
    retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[type, ...] = (Exception,)
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        retries: Maximum number of attempts.
        backoff_factor: Multiplicative factor for wait time between attempts.
        exceptions: Tuple of exception types to catch and retry.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            delay = 1.0
            while attempt <= retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == retries:
                        logger.error(
                            f"Function '{func.__name__}' failed after {retries} attempts. Error: {e}"
                        )
                        raise
                    logger.warning(
                        f"Function '{func.__name__}' attempt {attempt}/{retries} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
                    attempt += 1
        return wrapper
    return decorator


def calculate_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.

    Args:
        file_path: Absolute or relative Path to the file.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    if not file_path.exists():
        return ""

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_size_bytes(file_path: Path) -> int:
    """
    Returns the file size in bytes.
    """
    if not file_path.exists():
        return 0
    return file_path.stat().st_size


def extract_bounding_box(gdf: gpd.GeoDataFrame) -> Dict[str, float]:
    """
    Extracts bounding box coordinates [minx, miny, maxx, maxy] from a GeoDataFrame.

    Args:
        gdf: Input GeoDataFrame.

    Returns:
        Dictionary containing minx, miny, maxx, maxy bounds.
    """
    if gdf.empty:
        return {"minx": 0.0, "miny": 0.0, "maxx": 0.0, "maxy": 0.0}

    minx, miny, maxx, maxy = gdf.total_bounds
    return {
        "minx": float(minx),
        "miny": float(miny),
        "maxx": float(maxx),
        "maxy": float(maxy),
    }
