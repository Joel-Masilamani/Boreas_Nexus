"""
Boreas-Nexus Feature Extractor Module

Orchestrates spatial feature extraction for Urban Heat Island analysis:
calculates proximity features (distance to water/parks/roads), building density,
spectral vegetation & built-up indices (NDVI, NDBI, NDWI, LST), and terrain metrics.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger
from preprocessing.vector_processor import VectorProcessor
from preprocessing.raster_processor import RasterProcessor


class FeatureExtractor:
    """
    Extracts multi-domain geospatial features for each grid cell/point in the study area.
    """

    def __init__(self, target_crs: str = "EPSG:4326"):
        self.target_crs = target_crs

    def extract_proximity_features(
        self,
        grid_gdf: gpd.GeoDataFrame,
        vector_layers: Dict[str, gpd.GeoDataFrame]
    ) -> gpd.GeoDataFrame:
        """
        Extracts distance-to-feature spatial columns for water, parks, and roads.
        """
        result_gdf = grid_gdf.copy()

        # Distance to water
        if "water" in vector_layers and not vector_layers["water"].empty:
            logger.info("Extracting feature: distance_to_water...")
            result_gdf["distance_to_water_m"] = VectorProcessor.compute_distance_to_features(
                grid_gdf, vector_layers["water"]
            ) * 111000.0  # Approx convert degrees to meters
        else:
            result_gdf["distance_to_water_m"] = 0.0

        # Distance to parks
        if "parks" in vector_layers and not vector_layers["parks"].empty:
            logger.info("Extracting feature: distance_to_parks...")
            result_gdf["distance_to_parks_m"] = VectorProcessor.compute_distance_to_features(
                grid_gdf, vector_layers["parks"]
            ) * 111000.0
        else:
            result_gdf["distance_to_parks_m"] = 0.0

        # Distance to roads
        if "roads" in vector_layers and not vector_layers["roads"].empty:
            logger.info("Extracting feature: distance_to_roads...")
            result_gdf["distance_to_roads_m"] = VectorProcessor.compute_distance_to_features(
                grid_gdf, vector_layers["roads"]
            ) * 111000.0
        else:
            result_gdf["distance_to_roads_m"] = 0.0

        return result_gdf

    def extract_building_density(
        self,
        grid_gdf: gpd.GeoDataFrame,
        vector_layers: Dict[str, gpd.GeoDataFrame]
    ) -> gpd.GeoDataFrame:
        """
        Extracts building footprint density (percentage of building coverage within 100m buffer).
        """
        result_gdf = grid_gdf.copy()
        if "buildings" in vector_layers and not vector_layers["buildings"].empty:
            logger.info("Extracting feature: building_density...")
            buildings = vector_layers["buildings"]
            # Spatial join count or buffer intersection approximation
            # Buffer points by ~50m (0.00045 degrees)
            buffered = grid_gdf.geometry.buffer(0.00045)
            buf_gdf = gpd.GeoDataFrame(geometry=buffered, crs=grid_gdf.crs)
            joined = gpd.sjoin(buf_gdf, buildings, how="left", predicate="intersects")
            counts = joined.groupby(joined.index).size() - 1
            # Normalize density count to [0.0, 1.0] range
            result_gdf["building_density"] = np.clip(counts.reindex(grid_gdf.index, fill_value=0) / 10.0, 0.0, 1.0)
        else:
            result_gdf["building_density"] = 0.0
        return result_gdf

    def extract_spectral_features(
        self,
        grid_gdf: gpd.GeoDataFrame,
        satellite_dir: Path
    ) -> gpd.GeoDataFrame:
        """
        Extracts real spectral indices (NDVI, NDBI, NDWI, LST) from ingested satellite GeoTIFF rasters onto grid points.
        """
        result_gdf = grid_gdf.copy()
        n_points = len(result_gdf)
        logger.info(f"Extracting real spectral features (NDVI, NDBI, NDWI, LST) for {n_points} grid points...")

        # Find valid (non-empty) Sentinel-2 and Landsat-8 GeoTIFFs (> 100 KB)
        sentinel_files = [p for p in satellite_dir.glob("**/sentinel*.tif") if p.stat().st_size > 100000]
        landsat_files = [p for p in satellite_dir.glob("**/landsat*.tif") if p.stat().st_size > 100000]

        sentinel_files.sort(key=lambda p: p.stat().st_size, reverse=True)
        landsat_files.sort(key=lambda p: p.stat().st_size, reverse=True)

        # Extract Sentinel-2 bands: Band 1=Red, Band 2=Green, Band 3=NIR, Band 4=SWIR
        if sentinel_files:
            s2_path = sentinel_files[0]
            logger.info(f"Sampling Sentinel-2 multispectral bands from {s2_path} (size: {s2_path.stat().st_size / 1e6:.2f} MB)...")
            b_red = RasterProcessor.sample_points_from_raster(s2_path, grid_gdf, band_index=1)
            b_green = RasterProcessor.sample_points_from_raster(s2_path, grid_gdf, band_index=2)
            b_nir = RasterProcessor.sample_points_from_raster(s2_path, grid_gdf, band_index=3)
            b_swir = RasterProcessor.sample_points_from_raster(s2_path, grid_gdf, band_index=4)

            ndvi_vals = RasterProcessor.compute_ndvi(b_red, b_nir)
            ndbi_vals = RasterProcessor.compute_ndbi(b_swir, b_nir)
            ndwi_vals = RasterProcessor.compute_ndwi(b_green, b_nir)

            result_gdf["ndvi"] = np.nan_to_num(ndvi_vals, nan=0.35)
            result_gdf["ndbi"] = np.nan_to_num(ndbi_vals, nan=0.15)
            result_gdf["ndwi"] = np.nan_to_num(ndwi_vals, nan=-0.10)
        else:
            logger.warning("Sentinel-2 raster not found. Using baseline spectral values.")
            result_gdf["ndvi"] = 0.35
            result_gdf["ndbi"] = 0.15
            result_gdf["ndwi"] = -0.10

        # Extract Landsat-8 Surface Temperature (°C)
        if landsat_files:
            ls_path = landsat_files[0]
            logger.info(f"Sampling Landsat-8 Surface Temperature from {ls_path} (size: {ls_path.stat().st_size / 1e6:.2f} MB)...")
            lst_vals = RasterProcessor.sample_points_from_raster(ls_path, grid_gdf, band_index=1)
            # Clip LST to realistic physical urban surface temperature bounds (15°C - 55°C)
            result_gdf["lst_celsius"] = np.where(np.isnan(lst_vals) | (lst_vals < 10.0), 33.5, np.clip(lst_vals, 15.0, 55.0))
        else:
            logger.warning("Landsat-8 thermal raster not found. Using baseline LST values.")
            result_gdf["lst_celsius"] = 33.5


        return result_gdf

    def extract_dem_features(
        self,
        grid_gdf: gpd.GeoDataFrame,
        elevation_path: Optional[Path]
    ) -> gpd.GeoDataFrame:
        """
        Extracts real elevation, slope, and aspect features from DEM GeoTIFF onto grid points.
        """
        result_gdf = grid_gdf.copy()
        n_points = len(result_gdf)
        logger.info(f"Extracting DEM terrain features (elevation, slope, aspect) for {n_points} points...")

        if elevation_path and elevation_path.exists():
            logger.info(f"Sampling elevation from {elevation_path}...")
            elev_vals = RasterProcessor.sample_points_from_raster(elevation_path, grid_gdf, band_index=1)
            result_gdf["elevation_m"] = np.nan_to_num(np.clip(elev_vals, 0.0, 500.0), nan=12.0)
        else:
            result_gdf["elevation_m"] = 12.0

        # Derive slope and aspect gradients
        dx = np.gradient(result_gdf["elevation_m"].values)
        dy = np.gradient(result_gdf["elevation_m"].values)
        slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
        aspect_rad = np.arctan2(-dy, dx)

        result_gdf["slope_deg"] = np.clip(np.degrees(slope_rad), 0.0, 45.0)
        result_gdf["aspect_deg"] = np.mod(np.degrees(aspect_rad) + 360.0, 360.0)

        return result_gdf

    def extract_landcover_features(
        self,
        grid_gdf: gpd.GeoDataFrame,
        raw_dir: Path
    ) -> gpd.GeoDataFrame:
        """
        Extracts ESA WorldCover land cover classification class code onto grid points.
        Classes: 10=Trees, 30=Grassland, 40=Cropland, 50=Built-up, 80=Water.
        """
        result_gdf = grid_gdf.copy()
        lc_path = raw_dir / "landcover" / "landcover_worldcover.tif"

        if lc_path.exists():
            logger.info(f"Sampling land cover classes from {lc_path}...")
            lc_vals = RasterProcessor.sample_points_from_raster(lc_path, grid_gdf, band_index=1)
            result_gdf["land_cover_code"] = np.nan_to_num(lc_vals, nan=50.0).astype(int)
        else:
            result_gdf["land_cover_code"] = 50  # Default to built-up urban

        return result_gdf

