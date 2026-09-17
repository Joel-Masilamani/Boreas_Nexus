"""
Shared Pytest Fixtures for Boreas-Nexus Test Suites
"""

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
from storage.storage_manager import StorageManager


@pytest.fixture
def sample_boundary():
    """Square boundary polygon around Chennai coordinates."""
    poly = Polygon([(80.20, 13.00), (80.25, 13.00), (80.25, 13.05), (80.20, 13.05)])
    return gpd.GeoDataFrame([{"geometry": poly}], crs="EPSG:4326")


@pytest.fixture
def sample_grid_points():
    """Minimal 10-point synthetic grid fixture."""
    n = 10
    lats = np.linspace(13.01, 13.05, n)
    lons = np.linspace(80.21, 80.25, n)
    points = [Point(xy) for xy in zip(lons, lats)]
    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "geometry": points
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


@pytest.fixture
def sample_m1_gdf():
    """Synthetic Module 1 GeoDataFrame fixture for validation testing."""
    np.random.seed(42)
    n = 50
    lats = np.linspace(13.0, 13.2, n)
    lons = np.linspace(80.1, 80.3, n)

    is_rural = np.array([True] * 10 + [False] * 40)
    lst_day = np.where(is_rural, 32.0 + np.random.normal(0, 0.5, n), 38.0 + np.random.normal(0, 1.0, n))
    lst_night = np.where(is_rural, 24.0 + np.random.normal(0, 0.3, n), 28.0 + np.random.normal(0, 0.5, n))

    rural_base_day = float(np.mean(lst_day[is_rural]))
    rural_base_night = float(np.mean(lst_night[is_rural]))

    suhii_day = lst_day - rural_base_day
    suhii_night = lst_night - rural_base_night

    gi_z = np.clip((suhii_day - np.mean(suhii_day)) / (np.std(suhii_day) + 1e-6) * 2.0, -3.0, 5.0)
    is_hot_day = gi_z >= 1.96
    is_hot_night = suhii_night >= np.quantile(suhii_night, 0.80)
    is_persist = is_hot_day & is_hot_night

    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "is_rural": is_rural,
        "is_urban": ~is_rural,
        "land_cover_code": np.where(is_rural, 20, 50),
        "lst_day_celsius": lst_day,
        "lst_night_celsius": lst_night,
        "suhii_day_celsius": suhii_day,
        "suhii_night_celsius": suhii_night,
        "gi_zscore_day": gi_z,
        "gi_pvalue_day": np.random.uniform(0.001, 0.05, n),
        "gi_zscore_night": gi_z * 0.8,
        "gi_pvalue_night": np.random.uniform(0.001, 0.05, n),
        "day_hotspot_significance": np.where(is_hot_day, "99% Confidence Hotspot", None),
        "night_hotspot_significance": np.where(is_hot_night, "95% Confidence Hotspot", None),
        "heat_persistence_index": np.random.uniform(0.4, 0.9, n),
        "is_hotspot_day": is_hot_day,
        "is_hotspot_night": is_hot_night,
        "is_persistent_hotspot": is_persist,
        "hotspot_id": [f"HOT_{(i // 10) + 1:04d}" if is_hot_day[i] else None for i in range(n)],
        "hotspot_confidence_score": np.random.uniform(50.0, 95.0, n),
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


@pytest.fixture
def sample_shap_gdf():
    """Synthetic SHAP attribution GeoDataFrame fixture."""
    n = 30
    base_val = 38.0
    shap_bd = np.random.uniform(3.0, 5.0, n)
    shap_ndvi = -np.random.uniform(1.5, 2.5, n)
    shap_water = np.random.uniform(0.1, 0.8, n)

    pred = base_val + shap_ndvi + shap_bd + shap_water
    lats = np.linspace(13.0, 13.1, n)
    lons = np.linspace(80.1, 80.2, n)

    data = {
        "point_id": [f"pt_{i:06d}" for i in range(1, n + 1)],
        "latitude": lats,
        "longitude": lons,
        "shap_base_value_day": [base_val] * n,
        "shap_day_ndvi": shap_ndvi,
        "shap_day_building_density": shap_bd,
        "shap_day_distance_to_water_m": shap_water,
        "lgbm_pred_lst_day_celsius": pred,
        "primary_driver_day": ["building_density"] * n,
        "secondary_driver_day": ["ndvi"] * n,
        "tertiary_driver_day": ["distance_to_water_m"] * n,
        "geometry": [Point(xy) for xy in zip(lons, lats)]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")
