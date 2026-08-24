# Phase 1 and 2 (Complete)

# **Walkthrough: Phase 1 (Data Collection) & Phase 2 (Feature Engineering) Real Data Integration**

**Project**: Boreas-Nexus — Integrating Cool Infrastructure into Urban Zoning

**City**: Chennai, Tamil Nadu, India

**Execution Date**: August 4, 2026

**Status**: 🏆 **SUCCESS — REAL DATA INGESTED & PREPROCESSED**

---

## **🏆 Accomplishments Overview**

Phase 0 (Data Collection) and Phase 1 (Feature Engineering) have been completely upgraded from synthetic placeholders to **real remote sensing datasets** fetched directly from the **Microsoft Planetary Computer STAC API** and OpenStreetMap.

All **44,298 sample grid points** across Chennai now contain authentic physical Land Surface Temperature (°C), multispectral vegetation & water indices (NDVI, NDWI), 30m terrain DEM elevation & slope metrics, land cover classification, building footprint density, and spatial vector proximity attributes.

---

## **📦 Ingested Real Datasets (`data/raw/`)**

| **Dataset** | **Provider / Catalog** | **Source File Path** | **File Size / Record Count** |
| --- | --- | --- | --- |
| **Sentinel-2 Multispectral** | MS Planetary Computer (`sentinel-2-l2a`) | `data/raw/satellite/sentinel/2024/05/sentinel2_scene_2024_05.tif` | **23.71 MB** (Red, Green, NIR, SWIR bands) |
| **Landsat-8 Surface Temp** | MS Planetary Computer (`landsat-c2-l2`) | `data/raw/satellite/landsat/2024/03/landsat8_scene_2024_03.tif` | **3.98 MB** (Band 10 Thermal IR, °C) |
| **Copernicus DEM 30m** | MS Planetary Computer (`cop-dem-glo-30`) | `data/raw/elevation/dem_elevation.tif` | **10.5 MB** GeoTIFF |
| **ESA WorldCover 10m** | MS Planetary Computer (`esa-worldcover`) | `data/raw/landcover/landcover_worldcover.tif` | **14.2 MB** Land Cover Classification GeoTIFF |
| **Road Network** | OpenStreetMap / OSMnx | `data/raw/vector/roads.geojson` | 63,481 features (~293 MB) |
| **Building Footprints** | OpenStreetMap / OSMnx | `data/raw/vector/buildings.geojson` | 277,442 features (~1.7 GB) |
| **Meteorological Timeseries** | NASA POWER REST API | `data/raw/weather/weather_data.csv` | 366 daily records (8 parameters) |
| **City Boundary** | OpenStreetMap / OSMnx | `data/raw/boundary/boundary.geojson` | 1 administrative polygon (`EPSG:4326`) |

---

## **📊 Extracted Real Feature Matrix (`data/processed/features.parquet`)**

- **Output Path**: `data/processed/features.parquet` (**4.46 MB**) & `data/processed/features.geojson` (**21.53 MB**)
- **Total Spatial Samples**: 44,298 grid points (100m resolution)
- **Missing / NaN Values**: **0 missing values across all 44,298 rows**

### **Summary Statistics of Real Physical Features**

| **Feature Column** | **Description** | **Mean** | **Std Dev** | **Min** | **Median (50%)** | **Max** |
| --- | --- | --- | --- | --- | --- | --- |
| `lst_celsius` | **Landsat-8 Surface Temperature (°C)** | **39.09 °C** | 2.34 °C | 29.74 °C | 39.42 °C | **49.72 °C** |
| `ndvi` | **Normalized Difference Vegetation Index** | **0.344** | 0.041 | -0.086 | 0.350 | **0.666** |
| `ndwi` | **Normalized Difference Water Index** | **-0.102** | 0.023 | -0.570 | -0.100 | **0.137** |
| `elevation_m` | **Copernicus DEM 30m Elevation (m)** | **8.17 m** | 6.68 m | 0.00 m | 8.33 m | **35.54 m** |
| `slope_deg` | **Terrain Slope (degrees)** | **26.52°** | 19.65° | 0.00° | 35.73° | **45.00°** |
| `building_density` | **Building Footprint Density (% coverage)** | **0.391** | 0.434 | 0.000 | 0.100 | **1.000** |
| `distance_to_water_m` | **Proximity to nearest water body (m)** | **278.98 m** | 244.00 m | 0.00 m | 229.10 m | **2137.66 m** |
| `distance_to_parks_m` | **Proximity to nearest green space (m)** | **798.34 m** | 832.52 m | 0.00 m | 514.48 m | **5442.68 m** |
| `distance_to_roads_m` | **Proximity to nearest road segment (m)** | **39.28 m** | 68.36 m | 0.00 m | 16.30 m | **722.87 m** |
| `land_cover_code` | **ESA WorldCover Class Code** | **41.51** | 18.19 | 10 (Trees) | 50 (Built-up) | 90 (Wetland) |

---

## **🧪 Verification Results**

- **Data Ingestion (`main.py`)**: `Status: SUCCESS` in 655.22s.
- **Preprocessing Pipeline (`run_preprocessing.py`)**: `Status: SUCCESS` in 1054s.
- **Feature Matrix Audit (`scratch/inspect_features.py`)**: 0 NaNs across all 44,298 points; physical LST distribution between 29.7°C and 49.7°C.
- **Automated Tests**: Unit test suite passed.

---

## **🚀 Next Steps: Module 1 (Urban Heat Hotspot Identification Engine)**

With real satellite LST, spectral indices, and land cover attributes now fully extracted into `data/processed/features.parquet`, we are ready to implement **Module 1**:

1. **Stage 2**: Urban vs. Rural Land Cover Delineation (using `land_cover_code`).
2. **Stage 3**: Surface Urban Heat Island Intensity computation (SUHII=LSTurban−*μ*(LSTrural)).
    
    SUHII=LSTurban−μ(LSTrural)
    
3. **Stage 5**: Getis-Ord *Gi*∗ Spatial Hotspot Clustering (*Z*scores & *p*values via PySAL `esda.getisord.G_Local`).
4. **Stage 6**: Urban Heat Hotspot Knowledge Layer export.