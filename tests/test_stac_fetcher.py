"""
Unit tests for STAC fetcher module.
"""

import pytest
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Polygon
from ingestion.stac_fetcher import (
    _create_fallback_multiband_raster,
    _create_fallback_thermal_raster,
    _create_fallback_dem_raster,
    _create_fallback_landcover_raster
)


@pytest.fixture
def sample_boundary():
    poly = Polygon([(80.20, 13.00), (80.25, 13.00), (80.25, 13.05), (80.20, 13.05)])
    return gpd.GeoDataFrame([{"geometry": poly}], crs="EPSG:4326")


def test_fallback_multiband_raster(tmp_path):
    target = tmp_path / "sentinel.tif"
    bbox = {"minx": 80.20, "miny": 13.00, "maxx": 80.25, "maxy": 13.05}
    _create_fallback_multiband_raster(target, bbox, num_bands=4)

    assert target.exists()
    assert target.stat().st_size > 1000


def test_fallback_thermal_raster(tmp_path):
    target = tmp_path / "lst.tif"
    bbox = {"minx": 80.20, "miny": 13.00, "maxx": 80.25, "maxy": 13.05}
    _create_fallback_thermal_raster(target, bbox)

    assert target.exists()
    assert target.stat().st_size > 1000
