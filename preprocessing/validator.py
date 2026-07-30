"""
Boreas-Nexus Data Validator Module

Performs strict data validation across ingested vector, raster, weather, and metadata files.
Checks CRS consistency, empty files, missing/duplicate geometries, raster corruption,
and metadata completeness. Produces a detailed validation report JSON.
"""

from pathlib import Path
from typing import Dict, List, Any
import geopandas as gpd
import pandas as pd

from utils.logger import logger
from utils.config_loader import Config
from utils.constants import REQUIRED_METADATA_KEYS
from utils.helpers import get_file_size_bytes
from storage.metadata_store import MetadataStore
from preprocessing.raster_processor import RasterProcessor


class DatasetValidator:
    """
    Comprehensive Data Validator verifying dataset integrity, projection consistency,
    geometry sanity, and metadata completeness.
    """

    def __init__(self, config: Config, metadata_store: MetadataStore):
        self.config = config
        self.target_crs = config.city.crs
        self.metadata_store = metadata_store

    def validate_vector_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validates vector file (CRS consistency, empty file, missing geometries, duplicate geometries).
        """
        file_size = get_file_size_bytes(file_path)
        if file_size == 0 or not file_path.exists():
            return {
                "file": file_path.name,
                "status": "FAILED",
                "issues": ["File is empty or missing on disk"]
            }

        issues: List[str] = []
        try:
            gdf = gpd.read_file(file_path)
            
            # Check empty
            if gdf.empty:
                issues.append("GeoDataFrame contains 0 features.")

            # Check CRS
            if gdf.crs is not None and str(gdf.crs).upper() != self.target_crs.upper():
                issues.append(f"CRS mismatch: found '{gdf.crs}', expected '{self.target_crs}'")

            # Check missing geometries
            if not gdf.empty:
                null_geoms = gdf.geometry.isnull().sum()
                if null_geoms > 0:
                    issues.append(f"Found {null_geoms} missing/null geometries.")

                # Check duplicate geometries
                duplicate_geoms = gdf.geometry.duplicated().sum()
                if duplicate_geoms > 0:
                    issues.append(f"Found {duplicate_geoms} duplicate geometries.")

        except Exception as e:
            issues.append(f"Failed to parse vector file: {e}")

        status = "PASSED" if len(issues) == 0 else "WARNING" if "Failed to parse" not in str(issues) else "FAILED"
        return {
            "file": file_path.name,
            "status": status,
            "issues": issues,
            "feature_count": len(gdf) if 'gdf' in locals() and not gdf.empty else 0
        }

    def validate_raster_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validates raster GeoTIFF files for corruption and CRS alignment.
        """
        file_size = get_file_size_bytes(file_path)
        if file_size == 0 or not file_path.exists():
            return {
                "file": file_path.name,
                "status": "FAILED",
                "issues": ["Raster file is empty or missing on disk"]
            }

        issues: List[str] = []
        raster_info = RasterProcessor.inspect_raster(file_path)
        if not raster_info.get("valid", False):
            issues.append(f"Raster corruption / unreadable header: {raster_info.get('error')}")

        status = "PASSED" if len(issues) == 0 else "FAILED"
        return {
            "file": file_path.name,
            "status": status,
            "issues": issues,
            "raster_info": raster_info
        }

    def validate_weather_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validates tabular weather CSV data.
        """
        file_size = get_file_size_bytes(file_path)
        if file_size == 0 or not file_path.exists():
            return {
                "file": file_path.name,
                "status": "FAILED",
                "issues": ["Weather CSV file is missing or 0 bytes"]
            }

        issues: List[str] = []
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                issues.append("Weather dataset CSV is empty.")
            if "temperature_2m_c" not in df.columns:
                issues.append("Missing essential meteorological column 'temperature_2m_c'")
        except Exception as e:
            issues.append(f"Failed to read CSV: {e}")

        status = "PASSED" if len(issues) == 0 else "FAILED"
        return {
            "file": file_path.name,
            "status": status,
            "issues": issues,
            "record_count": len(df) if 'df' in locals() else 0
        }

    def validate_metadata_completeness(self) -> Dict[str, Any]:
        """
        Validates metadata.json records for completeness of required fields.
        """
        metadata = self.metadata_store.get_all_metadata()
        missing_fields_map: Dict[str, List[str]] = {}

        for dataset_name, record in metadata.items():
            missing = [k for k in REQUIRED_METADATA_KEYS if k not in record]
            if missing:
                missing_fields_map[dataset_name] = missing

        status = "PASSED" if not missing_fields_map else "WARNING"
        return {
            "status": status,
            "total_datasets_tracked": len(metadata),
            "missing_fields": missing_fields_map
        }

    def run_full_validation(
        self,
        raw_data_dir: Path | str = Path("data/raw")
    ) -> Dict[str, Any]:
        """
        Runs comprehensive validation across all ingested files in data/raw.
        """
        raw_dir = Path(raw_data_dir).resolve()
        logger.info(f"Starting pipeline validation suite on {raw_dir}...")

        vector_results = []
        raster_results = []
        weather_results = []

        # Vector check
        for vec_file in raw_dir.glob("**/*.geojson"):
            vector_results.append(self.validate_vector_file(vec_file))
        for shp_file in raw_dir.glob("**/*.shp"):
            vector_results.append(self.validate_vector_file(shp_file))

        # Raster check
        for tif_file in raw_dir.glob("**/*.tif"):
            raster_results.append(self.validate_raster_file(tif_file))

        # Weather check
        for csv_file in raw_dir.glob("**/*.csv"):
            weather_results.append(self.validate_weather_file(csv_file))

        metadata_val = self.validate_metadata_completeness()

        report = {
            "city": self.config.city.name,
            "target_crs": self.target_crs,
            "vector_validation": vector_results,
            "raster_validation": raster_results,
            "weather_validation": weather_results,
            "metadata_validation": metadata_val,
            "overall_status": "PASSED" if all(
                r["status"] != "FAILED" for r in vector_results + raster_results + weather_results
            ) else "PASSED_WITH_WARNINGS"
        }

        # Save report
        self.metadata_store.save_validation_report(report)
        logger.info(f"Validation completed. Overall status: {report['overall_status']}")
        return report
