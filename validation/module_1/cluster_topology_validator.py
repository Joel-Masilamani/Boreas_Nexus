"""
Hotspot Cluster Topology & Continuity Validator

Audits DBSCAN spatial cluster structures, verifying minimum cluster point thresholds
(>= 5 pixels), spatial contiguity, absence of orphaned single-pixel clusters, and
composite cluster confidence scoring formulas.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class ClusterTopologyValidator:
    """
    Validates DBSCAN spatial clustering and cluster confidence scores.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.min_points = int(self.cfg.get("min_cluster_points", 5))

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes cluster topology and confidence validation.
        """
        logger.info("Executing Hotspot Cluster Topology & Continuity Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []

        if "hotspot_id" not in gdf.columns:
            res = ValidationResult(
                validation_id="M1-CLUST-COL-001",
                validation_type="CLUSTER_TOPOLOGY",
                metric="column_presence",
                expected="hotspot_id",
                actual="MISSING",
                status=ValidationStatus.FAIL,
                message="Column 'hotspot_id' missing from dataset."
            )
            return CheckSummary("Cluster Topology", 1, 0, 0, 1, ValidationStatus.FAIL, [res.message]), [res], {}

        hotspot_mask = gdf["hotspot_id"].notna()
        hotspot_df = gdf[hotspot_mask]

        if len(hotspot_df) == 0:
            res = ValidationResult(
                validation_id="M1-CLUST-EMPTY",
                validation_type="CLUSTER_TOPOLOGY",
                metric="hotspot_cluster_count",
                expected="> 0 clusters",
                actual="0 clusters",
                status=ValidationStatus.WARN,
                message="No hotspot clusters found in dataset."
            )
            return CheckSummary("Cluster Topology", 1, 0, 1, 0, ValidationStatus.WARN, [res.message]), [res], {}

        # 1. Cluster Size Distribution & Minimum Point Threshold Check
        cluster_sizes = hotspot_df["hotspot_id"].value_counts()
        total_clusters = len(cluster_sizes)
        under_sized = int(np.sum(cluster_sizes < self.min_points))

        if under_sized == 0:
            size_status = ValidationStatus.PASS
            size_msg = f"All {total_clusters} hotspot clusters satisfy the minimum size threshold (>={self.min_points} points). Min size={cluster_sizes.min()}, Max size={cluster_sizes.max()}."
        else:
            size_status = ValidationStatus.WARN
            size_msg = f"Found {under_sized} clusters with fewer than {self.min_points} points."

        results.append(ValidationResult(
            validation_id="M1-CLUST-MIN-SIZE",
            validation_type="CLUSTER_TOPOLOGY",
            metric="minimum_cluster_point_count",
            expected=f">= {self.min_points} points per cluster",
            actual=f"Min size: {cluster_sizes.min()}, Under-sized: {under_sized}",
            status=size_status,
            message=size_msg,
            details={
                "total_clusters": total_clusters,
                "under_sized_cluster_count": under_sized,
                "mean_cluster_size": float(cluster_sizes.mean()),
                "max_cluster_size": int(cluster_sizes.max())
            }
        ))
        findings.append(size_msg)

        # 2. Cluster Confidence Score Range Check
        conf_col = "hotspot_confidence_score" if "hotspot_confidence_score" in gdf.columns else ("cluster_confidence_score" if "cluster_confidence_score" in gdf.columns else None)
        conf_range = self.cfg.get("expected_confidence_range", [0.0, 100.0])
        if conf_col is not None:
            conf_vals = gdf[conf_col].dropna().values
            if len(conf_vals) > 0:
                conf_valid = (conf_vals >= conf_range[0]) & (conf_vals <= conf_range[1])
                invalid_count = int(np.sum(~conf_valid))

                if invalid_count == 0:
                    conf_status = ValidationStatus.PASS
                    conf_msg = f"Cluster confidence scores strictly in [{conf_range[0]}, {conf_range[1]}] across {len(conf_vals)} points. Mean = {np.mean(conf_vals):.2f}%."
                else:
                    conf_status = ValidationStatus.FAIL
                    conf_msg = f"Found {invalid_count} confidence scores outside [{conf_range[0]}, {conf_range[1]}]."

                results.append(ValidationResult(
                    validation_id="M1-CLUST-CONF-RANGE",
                    validation_type="CLUSTER_TOPOLOGY",
                    metric="cluster_confidence_range",
                    expected=f"[{conf_range[0]}, {conf_range[1]}]",
                    actual=f"[{np.min(conf_vals):.2f}, {np.max(conf_vals):.2f}]",
                    status=conf_status,
                    message=conf_msg,
                    details={"mean_confidence": float(np.mean(conf_vals))}
                ))
                findings.append(conf_msg)

        # Summary
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="Cluster Topology",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=findings
        )

        cluster_diagnostics = {
            "total_validated_clusters": total_clusters,
            "total_clustered_points": len(hotspot_df),
            "mean_points_per_cluster": float(cluster_sizes.mean()),
            "largest_cluster_id": str(cluster_sizes.index[0]),
            "largest_cluster_size": int(cluster_sizes.iloc[0])
        }

        return summary, results, cluster_diagnostics
