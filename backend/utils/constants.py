"""
Boreas-Nexus Constants Module

Defines system-wide constants, OSM tag definitions, API endpoints,
default coordinate reference systems, and file paths.
"""

from typing import Dict, Any

DEFAULT_CRS = "EPSG:4326"

# Directory names under data/raw
DIR_BOUNDARY = "boundary"
DIR_SATELLITE = "satellite"
DIR_VECTOR = "vector"
DIR_WEATHER = "weather"
DIR_ELEVATION = "elevation"
DIR_METADATA = "metadata"

RAW_SUBDIRECTORIES = [
    DIR_BOUNDARY,
    DIR_SATELLITE,
    DIR_VECTOR,
    DIR_WEATHER,
    DIR_ELEVATION,
]

# OpenStreetMap feature tags for OSMnx querying
OSM_TAGS: Dict[str, Dict[str, Any]] = {
    "roads": {"highway": True},
    "buildings": {"building": True},
    "water": {"natural": ["water", "bay", "wetland"], "waterway": True},
    "parks": {"leisure": ["park", "garden", "playground", "nature_reserve"]},
    "vegetation": {"landuse": ["forest", "meadow", "grass", "allotments"], "natural": ["wood", "scrub", "grassland"]},
    "railways": {"railway": True},
    "landuse": {"landuse": True},
}

# NASA POWER API configuration
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_POWER_COMMUNITY = "RE"

# Weather parameters mapping
NASA_POWER_PARAMETERS = [
    "T2M",       # Temperature at 2 Meters (°C)
    "RH2M",      # Relative Humidity at 2 Meters (%)
    "WS2M",      # Wind Speed at 2 Meters (m/s)
    "WD2M",      # Wind Direction at 2 Meters (Degrees)
    "PRECTOTCORR", # Corrected Total Precipitation (mm/day)
    "ALLSKY_SWRAD_DAILY", # All Sky Surface Shortwave Downward Irradiance (MJ/m^2/day)
    "PS",        # Surface Pressure (kPa)
    "CLRSKY_DAYS" # Clear Sky Days / Cloud Cover proxy
]

# Expected dataset metadata keys
REQUIRED_METADATA_KEYS = [
    "dataset_name",
    "source",
    "provider",
    "download_time",
    "projection",
    "bounding_box",
    "resolution",
    "file_size_bytes",
    "license",
    "version",
    "checksum",
    "storage_path",
    "status",
]
