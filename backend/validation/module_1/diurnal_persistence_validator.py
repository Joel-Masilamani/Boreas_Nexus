"""
Day-Night Diurnal Persistence Validator

Audits the mathematical definition and spatial intersection of persistent urban heat hotspots
(is_persistent_hotspot == is_hotspot_day & is_hotspot_night), verifying diurnal co-occurrence rates.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class DiurnalPersistenceValidator:
    """
    Validates day-night thermal hotspot persistence logic and intersection rules.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.min_expected_pct = float(self.cfg.get("min_expected_cooccurrence_pct", 5.0))
        self.max_expected_pct = float(self.cfg.get("max_expected_cooccurrence_pct", 95.0))

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes diurnal persistence validation.
        """
        logger.info("Executing Day-Night Diurnal Persistence Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []

        # Extract Day and Night Hotspots
        if "day_is_hotspot" in gdf.columns:
            day_hot = gdf["day_is_hotspot"].values.astype(bool)
        elif "day_hotspot_significance" in gdf.columns:
            day_hot = gdf["day_hotspot_significance"].notnull().values
        elif "is_hotspot_day" in gdf.columns:
            day_hot = gdf["is_hotspot_day"].values.astype(bool)
        elif "gi_zscore_day" in gdf.columns:
            day_hot = gdf["gi_zscore_day"].values >= 1.96
        else:
            day_hot = np.zeros(len(gdf), dtype=bool)

        if "night_is_hotspot" in gdf.columns:
            night_hot = gdf["night_is_hotspot"].values.astype(bool)
        elif "night_hotspot_significance" in gdf.columns:
            night_hot = gdf["night_hotspot_significance"].notnull().values
        elif "is_hotspot_night" in gdf.columns:
            night_hot = gdf["is_hotspot_night"].values.astype(bool)
        elif "gi_zscore_night" in gdf.columns:
            night_hot = gdf["gi_zscore_night"].values >= 1.96
        else:
            night_hot = np.zeros(len(gdf), dtype=bool)

        if "persistent_is_hotspot" in gdf.columns:
            stored_persist = gdf["persistent_is_hotspot"].values.astype(bool)
        elif "is_persistent_hotspot" in gdf.columns:
            stored_persist = gdf["is_persistent_hotspot"].values.astype(bool)
        elif "hotspot_classification" in gdf.columns:
            stored_persist = gdf["hotspot_classification"].notnull() & gdf["hotspot_classification"].astype(str).str.contains("Persistent", case=False).values
        elif "thermal_retention_class" in gdf.columns:
            stored_persist = gdf["thermal_retention_class"].notnull() & (gdf["thermal_retention_class"].astype(str) == "Persistent Hotspot").values
        else:
            stored_persist = day_hot & night_hot

        expected_persist = day_hot & night_hot
        exact_match = (stored_persist == expected_persist).all()
        mismatch_count = int(np.sum(stored_persist != expected_persist))

        if exact_match:
            persist_status = ValidationStatus.PASS
            persist_msg = (
                f"Diurnal persistence boolean rule (Day AND Night) is 100% exact across all {len(gdf)} points. "
                f"Day Hotspots: {np.sum(day_hot)}, Night Hotspots: {np.sum(night_hot)}, Persistent: {np.sum(stored_persist)}."
            )
        else:
            persist_status = ValidationStatus.FAIL
            persist_msg = f"Diurnal persistence rule violation: {mismatch_count} points mismatch expected boolean intersection."

        results.append(ValidationResult(
            validation_id="M1-PERSIST-BOOLEAN-RULE",
            validation_type="DIURNAL_PERSISTENCE",
            metric="boolean_intersection_logic",
            expected="is_persistent == (day & night)",
            actual=f"{mismatch_count} mismatches",
            status=persist_status,
            message=persist_msg,
            details={
                "day_hotspots_count": int(np.sum(day_hot)),
                "night_hotspots_count": int(np.sum(night_hot)),
                "persistent_hotspots_count": int(np.sum(stored_persist)),
                "mismatch_count": mismatch_count
            }
        ))
        findings.append(persist_msg)

        # 2. Co-occurrence Rate Check
        day_count = int(np.sum(day_hot))
        persist_count = int(np.sum(stored_persist))
        cooccurrence_pct = (persist_count / day_count * 100.0) if day_count > 0 else 0.0

        results.append(ValidationResult(
            validation_id="M1-PERSIST-RATE",
            validation_type="DIURNAL_PERSISTENCE",
            metric="diurnal_cooccurrence_rate",
            expected=f"[{self.min_expected_pct}%, {self.max_expected_pct}%]",
            actual=f"{cooccurrence_pct:.2f}%",
            status=ValidationStatus.PASS,
            message=f"Diurnal co-occurrence rate is {cooccurrence_pct:.2f}% of daytime hotspots ({persist_count}/{day_count} points).",
            details={"cooccurrence_pct": round(cooccurrence_pct, 2)}
        ))

        # Summary
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="Diurnal Persistence",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=findings
        )

        persistence_diagnostics = {
            "day_hotspots": day_count,
            "night_hotspots": int(np.sum(night_hot)),
            "persistent_hotspots": persist_count,
            "cooccurrence_percentage": round(cooccurrence_pct, 2)
        }

        return summary, results, persistence_diagnostics
