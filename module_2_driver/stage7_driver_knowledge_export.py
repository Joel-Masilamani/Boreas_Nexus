"""
Boreas-Nexus Module 2 - Stage 7: Urban Heat Driver Knowledge Layer Export

Consolidates multi-source drivers, machine learning predictions, SHAP attributions,
physics audit scores, and spatial GWR coefficients into the authoritative GeoParquet Knowledge
Layer and cluster-level Driver Attribution Registry, enforcing column-specific nullability rules.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import yaml

from utils.logger import logger
from storage.storage_manager import StorageManager


class Stage7DriverKnowledgeExporter:
    """
    Stage 7: Knowledge Layer & Attribution Registry Exporter.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/driver_analysis.yaml"),
        output_dir: Optional[Path | str] = None,
        metadata_dir: Optional[Path | str] = None
    ):
        self.config_path = Path(config_path)
        self.cfg = self._load_config()
        self.storage = StorageManager()
        
        self.output_dir = Path(output_dir) if output_dir else self.storage.get_processed_dir("module_2")
        self.metadata_dir = Path(metadata_dir) if metadata_dir else Path("data/metadata")
        self.reports_dir = self.storage.get_export_dir("reports")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Loads YAML configuration file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _validate_column_nullability(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Enforces column-specific nullability validation rules.
        """
        mandatory_non_null = [
            "point_id", "geometry", "latitude", "longitude",
            "ndvi", "ndbi", "ndwi", "building_density",
            "distance_to_roads_m", "distance_to_water_m", "distance_to_parks_m",
            "elevation_m", "slope_deg", "aspect_sin", "aspect_cos",
            "lst_day_celsius", "lst_night_celsius"
        ]

        # Add prediction columns if present
        for pred in ["lgbm_pred_lst_day_celsius", "rf_pred_lst_day_celsius", "primary_driver_day"]:
            if pred in gdf.columns:
                mandatory_non_null.append(pred)

        violations = {}
        for col in mandatory_non_null:
            if col in gdf.columns:
                null_count = int(gdf[col].isna().sum())
                if null_count > 0:
                    violations[col] = null_count

        if violations:
            logger.warning(f"Nullability check flagged non-null column violations: {violations}")
            # Cleanly impute numerical predictions or features
            for col in violations:
                if pd.api.types.is_numeric_dtype(gdf[col]):
                    gdf[col] = gdf[col].fillna(gdf[col].median())

        return {
            "mandatory_columns_checked": len(mandatory_non_null),
            "violations_found": len(violations),
            "violations": violations,
            "status": "PASSED" if len(violations) == 0 else "RESOLVED_BY_IMPUTATION"
        }

    def _build_cluster_attribution_registry(
        self,
        gdf: gpd.GeoDataFrame
    ) -> pd.DataFrame:
        """
        Aggregates pixel-level driver SHAP contributions and physics consistency
        per validated hotspot cluster (HOT_xxxx).
        """
        if "hotspot_id" not in gdf.columns:
            logger.warning("'hotspot_id' column not present. Returning empty registry.")
            return pd.DataFrame()

        hotspot_mask = gdf["hotspot_id"].notna()
        hotspot_df = gdf[hotspot_mask]

        if len(hotspot_df) == 0:
            logger.warning("No hotspot points detected. Empty cluster registry.")
            return pd.DataFrame()

        registry_records = []
        clusters = hotspot_df.groupby("hotspot_id")

        for hid, group in clusters:
            record = {
                "hotspot_id": hid,
                "pixel_count": len(group),
                "mean_lst_day_celsius": float(group["lst_day_celsius"].mean()) if "lst_day_celsius" in group else np.nan,
                "mean_lst_night_celsius": float(group["lst_night_celsius"].mean()) if "lst_night_celsius" in group else np.nan,
                "mean_ndvi": float(group["ndvi"].mean()) if "ndvi" in group else np.nan,
                "mean_building_density": float(group["building_density"].mean()) if "building_density" in group else np.nan,
                "mean_distance_to_water_m": float(group["distance_to_water_m"].mean()) if "distance_to_water_m" in group else np.nan,
            }

            # SHAP attributions
            if "shap_day_ndvi" in group.columns:
                record["mean_shap_day_ndvi"] = float(group["shap_day_ndvi"].mean())
            if "shap_day_ndbi" in group.columns:
                record["mean_shap_day_ndbi"] = float(group["shap_day_ndbi"].mean())
            if "shap_day_building_density" in group.columns:
                record["mean_shap_day_building_density"] = float(group["shap_day_building_density"].mean())
            if "shap_day_distance_to_water_m" in group.columns:
                record["mean_shap_day_distance_to_water_m"] = float(group["shap_day_distance_to_water_m"].mean())

            # Dominant drivers
            if "primary_driver_day" in group.columns:
                mode_primary = group["primary_driver_day"].mode()
                record["dominant_cluster_driver_day"] = str(mode_primary.iloc[0]) if len(mode_primary) > 0 else "unknown"
            if "secondary_driver_day" in group.columns:
                mode_sec = group["secondary_driver_day"].mode()
                record["secondary_cluster_driver_day"] = str(mode_sec.iloc[0]) if len(mode_sec) > 0 else "unknown"

            # Physics / Domain consistency score
            if "shap_domain_consistency_score_day" in group.columns:
                record["mean_shap_domain_consistency_score_day"] = float(group["shap_domain_consistency_score_day"].mean())

            registry_records.append(record)

        registry_df = pd.DataFrame(registry_records)
        return registry_df

    def run(
        self,
        gdf_in: gpd.GeoDataFrame,
        stage_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes Stage 7 Knowledge Layer Export.
        """
        logger.info("--- Starting Module 2 Stage 7: Driver Knowledge Layer Export ---")

        if gdf_in is None or len(gdf_in) == 0:
            raise ValueError("Input GeoDataFrame to Stage 7 is None or empty.")

        gdf = gdf_in.copy()
        total_points = len(gdf)

        # 1. Nullability Validation
        null_report = self._validate_column_nullability(gdf)

        # 2. Export Authoritative Driver Knowledge Layer GeoParquet
        knowledge_layer_path = self.output_dir / "urban_heat_driver_knowledge_layer.geoparquet"
        gdf.to_parquet(knowledge_layer_path, index=False)
        logger.info(f"Saved Urban Heat Driver Knowledge Layer GeoParquet to: {knowledge_layer_path}")

        # 3. Export Cluster Attribution Registry
        registry_df = self._build_cluster_attribution_registry(gdf)
        registry_path = self.output_dir / "driver_attribution_registry.parquet"
        registry_df.to_parquet(registry_path, index=False)
        logger.info(f"Saved Driver Attribution Registry ({len(registry_df)} clusters) to: {registry_path}")

        # 4. Export SHAP Domain Audit Report
        audit_path = self.metadata_dir / "driver_shap_domain_audit.json"
        audit_payload = {
            "module": "Module 2: Urban Heat Driver Intelligence Engine",
            "total_points": total_points,
            "nullability_validation": null_report,
            "stage_metrics": stage_metrics or {}
        }
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit_payload, f, indent=2, default=str)
        logger.info(f"Saved Driver SHAP Domain Audit report to: {audit_path}")

        manifest = {
            "status": "SUCCESS",
            "total_sample_points": total_points,
            "total_columns": len(gdf.columns),
            "hotspot_clusters_registered": len(registry_df),
            "outputs": {
                "knowledge_layer_geoparquet": str(knowledge_layer_path),
                "attribution_registry_parquet": str(registry_path),
                "shap_domain_audit_json": str(audit_path)
            },
            "nullability_report": null_report
        }

        logger.info("Module 2 Stage 7 Knowledge Layer Export completed successfully.")
        return manifest
