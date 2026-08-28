"""
Boreas-Nexus Module 2 - Stage 7: Driver Knowledge Layer Export

Purpose: Consolidate all Module 2 driver attribution, SHAP values, domain audit scores,
and spatial GWR outputs into the unified driver knowledge layer (GeoParquet) and generate
the Cluster Attribution Registry (Parquet).
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger
from storage.storage_manager import StorageManager


class Stage7DriverKnowledgeExporter:
    """
    Consolidates and exports Module 2 driver intelligence outputs into GeoParquet and Parquet registry artifacts.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/city.yaml"),
        output_dir: Path | str | None = None,
        metadata_dir: Path | str | None = None
    ):
        self.config_path = Path(config_path)
        self.storage_manager = StorageManager()
        self.output_dir = Path(output_dir) if output_dir is not None else self.storage_manager.get_processed_dir("module_2")
        self.metadata_dir = Path(metadata_dir) if metadata_dir is not None else self.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def _validate_column_nullability(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Validates column completeness across driver features and SHAP values.
        """
        total_rows = len(gdf)
        null_counts = gdf.isnull().sum().to_dict()

        critical_driver_cols = [
            "point_id", "lst_day_celsius", "lst_night_celsius",
            "building_density", "distance_to_water_m", "distance_to_roads_m", "distance_to_parks_m",
            "ndvi", "ndbi", "ndwi", "elevation_m", "slope_deg"
        ]

        critical_nulls = {c: int(null_counts.get(c, 0)) for c in critical_driver_cols if c in gdf.columns}
        has_critical_nulls = any(val > 0 for val in critical_nulls.values())

        report = {
            "total_rows": total_rows,
            "has_critical_nulls": has_critical_nulls,
            "critical_column_null_counts": critical_nulls,
            "all_column_null_counts": {k: int(v) for k, v in null_counts.items() if v > 0}
        }
        return report

    def _summarize_group(self, hid: str, period: str, group: pd.DataFrame) -> Dict[str, Any]:
        """Summarizes driver attributions for a single hotspot cluster entity."""
        record = {
            "hotspot_id": hid,
            "period": period,
            "hotspot_group_id": group["hotspot_group_id"].dropna().iloc[0] if "hotspot_group_id" in group.columns and group["hotspot_group_id"].notna().any() else None,
            "pixel_count": len(group),
            "mean_lst_day_celsius": float(group["lst_day_celsius"].mean()) if "lst_day_celsius" in group.columns else np.nan,
            "mean_lst_night_celsius": float(group["lst_night_celsius"].mean()) if "lst_night_celsius" in group.columns else np.nan,
            "mean_ndvi": float(group["ndvi"].mean()) if "ndvi" in group.columns else np.nan,
            "mean_building_density": float(group["building_density"].mean()) if "building_density" in group.columns else np.nan,
            "mean_distance_to_water_m": float(group["distance_to_water_m"].mean()) if "distance_to_water_m" in group.columns else np.nan,
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

        return record

    def _build_cluster_attribution_registry(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Builds the normalized Cluster Attribution Registry for period-specific hotspot entities.
        """
        logger.info("Building normalized Driver Cluster Attribution Registry...")

        has_day = "day_hotspot_id" in gdf.columns and gdf["day_hotspot_id"].notna().any()
        has_night = "night_hotspot_id" in gdf.columns and gdf["night_hotspot_id"].notna().any()
        has_hotspot = "hotspot_id" in gdf.columns and gdf["hotspot_id"].notna().any()

        if not (has_day or has_night or has_hotspot):
            logger.warning("No hotspot points detected. Empty cluster registry.")
            return pd.DataFrame()

        registry_records = []

        if has_day:
            day_df = gdf[gdf["day_hotspot_id"].notna()]
            for hid, group in day_df.groupby("day_hotspot_id"):
                rec = self._summarize_group(hid, "DAY", group)
                registry_records.append(rec)

        if has_night:
            night_df = gdf[gdf["night_hotspot_id"].notna()]
            for hid, group in night_df.groupby("night_hotspot_id"):
                rec = self._summarize_group(hid, "NIGHT", group)
                registry_records.append(rec)

        if len(registry_records) == 0 and has_hotspot:
            hotspot_df = gdf[gdf["hotspot_id"].notna() & (gdf["hotspot_id"] != "")]
            for hid, group in hotspot_df.groupby("hotspot_id"):
                period = "DAY" if str(hid).startswith("DAY") else ("NIGHT" if str(hid).startswith("NIGHT") else "COMPOSITE")
                rec = self._summarize_group(hid, period, group)
                registry_records.append(rec)

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
