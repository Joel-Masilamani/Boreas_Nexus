"""
Boreas-Nexus Configuration Loader Module

Loads, validates, and parses YAML configuration files into strongly-typed
dataclasses for consumption across ingestion services.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

from utils.logger import logger
from utils.constants import DEFAULT_CRS


@dataclass
class CityConfig:
    name: str
    state: str
    country: str
    output_directory: Path
    crs: str = DEFAULT_CRS

    @property
    def query_name(self) -> str:
        """Constructs a search query string for geocoding services (e.g. 'Chennai, Tamil Nadu, India')."""
        parts = [self.name]
        if self.state:
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


@dataclass
class BoundaryConfig:
    format_geojson: bool = True
    format_shapefile: bool = True


@dataclass
class VectorConfig:
    layers: List[str] = field(default_factory=lambda: [
        "roads", "buildings", "water", "parks", "vegetation", "railways", "landuse"
    ])


@dataclass
class WeatherConfig:
    provider: str = "nasa_power"
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"


@dataclass
class ElevationConfig:
    provider: str = "srtm"
    dem_resolution: int = 30


@dataclass
class SatelliteConfig:
    providers: List[str] = field(default_factory=lambda: ["sentinel", "landsat"])
    years: List[int] = field(default_factory=lambda: [2024])
    months: List[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])


@dataclass
class IngestionConfig:
    boundary: BoundaryConfig = field(default_factory=BoundaryConfig)
    vector: VectorConfig = field(default_factory=VectorConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    elevation: ElevationConfig = field(default_factory=ElevationConfig)
    satellite: SatelliteConfig = field(default_factory=SatelliteConfig)


@dataclass
class Config:
    city: CityConfig
    ingestion: IngestionConfig
    config_file_path: Path


class ConfigLoader:
    """
    Handles loading, parsing, and validation of city configuration YAML files.
    """

    @staticmethod
    def load_config(config_path: Path | str = Path("config/city.yaml")) -> Config:
        """
        Reads and validates a YAML configuration file.

        Args:
            config_path: Path to city.yaml file.

        Returns:
            Config dataclass instance containing strongly typed settings.
        """
        path = Path(config_path)
        if not path.is_file():
            raise FileNotFoundError(f"Configuration file not found at: {path.resolve()}")

        logger.info(f"Loading configuration from {path.resolve()}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to parse YAML file {path}: {e}")
            raise ValueError(f"Invalid YAML structure in {path}: {e}") from e

        # Validate city block
        city_raw = data.get("city", {})
        if not city_raw.get("name"):
            raise ValueError("Configuration error: 'city.name' is required in configuration.")

        output_dir = Path(city_raw.get("output_directory", "data/raw"))
        city_config = CityConfig(
            name=city_raw.get("name"),
            state=city_raw.get("state", ""),
            country=city_raw.get("country", ""),
            output_directory=output_dir,
            crs=city_raw.get("crs", DEFAULT_CRS)
        )

        # Ingestion block parsing
        ingestion_raw = data.get("ingestion", {})

        b_raw = ingestion_raw.get("boundary", {})
        boundary_cfg = BoundaryConfig(
            format_geojson=b_raw.get("format_geojson", True),
            format_shapefile=b_raw.get("format_shapefile", True)
        )

        v_raw = ingestion_raw.get("vector", {})
        vector_cfg = VectorConfig(
            layers=v_raw.get("layers", ["roads", "buildings", "water", "parks", "vegetation", "railways", "landuse"])
        )

        w_raw = ingestion_raw.get("weather", {})
        weather_cfg = WeatherConfig(
            provider=w_raw.get("provider", "nasa_power"),
            start_date=str(w_raw.get("start_date", "2024-01-01")),
            end_date=str(w_raw.get("end_date", "2024-12-31"))
        )

        e_raw = ingestion_raw.get("elevation", {})
        elevation_cfg = ElevationConfig(
            provider=e_raw.get("provider", "srtm"),
            dem_resolution=e_raw.get("dem_resolution", 30)
        )

        s_raw = ingestion_raw.get("satellite", {})
        satellite_cfg = SatelliteConfig(
            providers=s_raw.get("providers", ["sentinel", "landsat"]),
            years=s_raw.get("years", [2024]),
            months=s_raw.get("months", list(range(1, 13)))
        )

        ingestion_config = IngestionConfig(
            boundary=boundary_cfg,
            vector=vector_cfg,
            weather=weather_cfg,
            elevation=elevation_cfg,
            satellite=satellite_cfg
        )

        config_obj = Config(
            city=city_config,
            ingestion=ingestion_config,
            config_file_path=path.resolve()
        )

        logger.info(
            f"Configuration successfully loaded for city: '{city_config.query_name}' "
            f"Output Target: '{output_dir.resolve()}'"
        )
        return config_obj
