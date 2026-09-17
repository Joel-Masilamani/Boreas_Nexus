"""
Boreas-Nexus Module 2 - Stage 5: XAI Attribution Plausibility Audit

Audits and flags explainable AI (SHAP) driver attributions against directional urban
microclimate physical expectations. Computes per-driver and global physical consistency
metrics without altering empirical SHAP values, emitting an explicit audit status.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
import geopandas as gpd
import yaml

from utils.logger import logger


class Stage5PhysicsValidator:
    """
    Stage 5: XAI Attribution Plausibility Auditor.
    Performs directional physical sanity checks on local SHAP values.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/driver_analysis.yaml")
    ):
        self.config_path = Path(config_path)
        self.cfg = self._load_config()
        self.last_gdf: Optional[gpd.GeoDataFrame] = None
        self.audit_results: Dict[str, Any] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Loads YAML configuration file."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def run(self, gdf_in: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Executes Stage 5 Directional Physics Audit on SHAP attributions.
        """
        logger.info("--- Starting Module 2 Stage 5: XAI Attribution Plausibility Audit ---")

        if gdf_in is None or len(gdf_in) == 0:
            raise ValueError("Input GeoDataFrame to Stage 5 is None or empty.")

        gdf = gdf_in.copy()
        
        audit_cfg = self.cfg.get("physics_audit", {})
        expectations = audit_cfg.get("directional_expectations", {
            "ndvi": "negative",
            "ndbi": "positive",
            "building_density": "positive",
            "distance_to_water_m": "positive",
            "distance_to_parks_m": "positive"
        })
        min_pass_pct = float(audit_cfg.get("minimum_passing_consistency_pct", 70.0))

        targets = ["day", "night"]
        global_audit = {}

        for prefix in targets:
            logger.info(f"Auditing SHAP directional plausibility for {prefix}time thermal model...")
            driver_stats = {}
            total_points = len(gdf)
            consistent_counts_per_point = np.zeros(total_points, dtype=int)
            evaluated_rules = 0

            for feature, expected_direction in expectations.items():
                shap_col = f"shap_{prefix}_{feature}"
                if shap_col not in gdf.columns:
                    continue

                shap_vals = gdf[shap_col].values
                evaluated_rules += 1

                if expected_direction == "negative":
                    # Cooling driver -> expected SHAP <= 0 for majority of above-average feature values
                    # Or check correlation between feature value and SHAP value
                    is_consistent = (shap_vals <= 0.05)  # allow tiny floating tolerance
                else:
                    # Heating driver -> expected SHAP >= 0
                    is_consistent = (shap_vals >= -0.05)

                consistent_count = int(np.sum(is_consistent))
                consistency_pct = float((consistent_count / total_points) * 100.0)
                consistent_counts_per_point += is_consistent.astype(int)

                driver_stats[feature] = {
                    "expected_direction": expected_direction,
                    "consistent_point_count": consistent_count,
                    "consistency_percentage": round(consistency_pct, 2)
                }

                logger.info(
                    f"Driver '{feature}' ({prefix}) -> Consistency: {consistency_pct:.1f}% "
                    f"({consistent_count}/{total_points} points consistent with {expected_direction} direction)"
                )

            # Per-point consistency score (0 to 100%)
            if evaluated_rules > 0:
                point_consistency_pct = (consistent_counts_per_point / evaluated_rules) * 100.0
                gdf[f"shap_domain_consistency_score_{prefix}"] = np.round(point_consistency_pct, 2)
                # Flag points with < 50% consistency as anomalies
                gdf[f"shap_domain_anomaly_flag_{prefix}"] = point_consistency_pct < 50.0

                mean_city_consistency = float(np.mean(point_consistency_pct))
            else:
                mean_city_consistency = 100.0
                gdf[f"shap_domain_consistency_score_{prefix}"] = 100.0
                gdf[f"shap_domain_anomaly_flag_{prefix}"] = False

            # Determine Stage Audit Status
            if mean_city_consistency >= min_pass_pct:
                audit_status = "PASSED"
            elif mean_city_consistency >= 50.0:
                audit_status = "WARNING"
            else:
                audit_status = "FAILED"

            global_audit[prefix] = {
                "status": audit_status,
                "city_mean_consistency_pct": round(mean_city_consistency, 2),
                "evaluated_rules_count": evaluated_rules,
                "per_driver_statistics": driver_stats,
                "anomalous_points_count": int(np.sum(gdf[f"shap_domain_anomaly_flag_{prefix}"]))
            }

            logger.info(
                f"Directional Audit {prefix} -> Status: {audit_status} | "
                f"City Mean Consistency: {mean_city_consistency:.2f}% | "
                f"Anomalous Points: {global_audit[prefix]['anomalous_points_count']}"
            )

        self.last_gdf = gdf
        self.audit_results = global_audit

        stage_metrics = {
            "stage": "Stage 5: XAI Attribution Plausibility Audit",
            "status": "SUCCESS",
            "audit_results": global_audit,
            "overall_audit_status": "PASSED" if all(v["status"] == "PASSED" for v in global_audit.values()) else "WARNING"
        }

        logger.info("Module 2 Stage 5 executed successfully.")
        return stage_metrics
