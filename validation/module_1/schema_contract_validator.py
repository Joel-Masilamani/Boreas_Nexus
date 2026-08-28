"""
Module 1 Schema & Knowledge Layer Data Contract Validator

Validates formal data contracts for every field in the Module 1 Urban Heat Hotspot
Knowledge Layer, checking data types, valid physical boundaries, and nullability constraints.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class SchemaContractValidator:
    """
    Validates data contracts, schema constraints, and value boundaries for Module 1.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.contracts = self.cfg.get("data_contracts", {}).get("fields", {})

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes schema contract validation.
        """
        logger.info("Executing Module 1 Schema & Data Contract Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []
        contract_summaries = {}

        for field_name, contract in self.contracts.items():
            if field_name not in gdf.columns:
                is_nullable = contract.get("nullable", False)
                status = ValidationStatus.WARN if is_nullable else ValidationStatus.FAIL
                msg = f"Contracted field '{field_name}' is missing from Module 1 Knowledge Layer."

                results.append(ValidationResult(
                    validation_id=f"M1-SCHEMA-MISSING-{field_name.upper()}",
                    validation_type="SCHEMA_DATA_CONTRACT",
                    metric=f"field_presence_{field_name}",
                    expected=field_name,
                    actual="MISSING",
                    status=status,
                    message=msg
                ))
                continue

            series = gdf[field_name]
            null_count = int(series.isna().sum())
            is_nullable = contract.get("nullable", False)

            # Nullability Check
            if null_count > 0 and not is_nullable:
                null_status = ValidationStatus.FAIL
                null_msg = f"Non-nullable field '{field_name}' contains {null_count} nulls."
            elif null_count > 0 and is_nullable:
                null_status = ValidationStatus.PASS
                null_msg = f"Nullable field '{field_name}' contains {null_count} nulls (allowed)."
            else:
                null_status = ValidationStatus.PASS
                null_msg = f"Field '{field_name}' has 0 nulls."

            results.append(ValidationResult(
                validation_id=f"M1-SCHEMA-NULL-{field_name.upper()}",
                validation_type="SCHEMA_DATA_CONTRACT",
                metric=f"nullability_{field_name}",
                expected="0 nulls" if not is_nullable else "nullable allowed",
                actual=f"{null_count} nulls",
                status=null_status,
                message=null_msg
            ))

            # Numeric Range and Infinity Check
            valid_min = contract.get("valid_min")
            valid_max = contract.get("valid_max")

            if valid_min is not None and valid_max is not None and pd.api.types.is_numeric_dtype(series):
                valid_vals = series.dropna().values
                has_inf = np.isinf(valid_vals).any()

                if has_inf:
                    results.append(ValidationResult(
                        validation_id=f"M1-SCHEMA-INF-{field_name.upper()}",
                        validation_type="SCHEMA_DATA_CONTRACT",
                        metric=f"infinity_check_{field_name}",
                        expected="Finite numbers",
                        actual="Contains +/- Inf",
                        status=ValidationStatus.FAIL,
                        message=f"Field '{field_name}' contains infinite values."
                    ))

                actual_min = float(np.min(valid_vals)) if len(valid_vals) > 0 else np.nan
                actual_max = float(np.max(valid_vals)) if len(valid_vals) > 0 else np.nan
                out_of_range = np.sum((valid_vals < valid_min) | (valid_vals > valid_max))

                if out_of_range == 0:
                    range_status = ValidationStatus.PASS
                    range_msg = f"Field '{field_name}' strictly in [{valid_min}, {valid_max}]. Observed: [{actual_min:.2f}, {actual_max:.2f}]."
                else:
                    range_status = ValidationStatus.FAIL
                    range_msg = f"Field '{field_name}' contains {out_of_range} values outside [{valid_min}, {valid_max}]."

                results.append(ValidationResult(
                    validation_id=f"M1-SCHEMA-RANGE-{field_name.upper()}",
                    validation_type="SCHEMA_DATA_CONTRACT",
                    metric=f"range_check_{field_name}",
                    expected=f"[{valid_min}, {valid_max}]",
                    actual=f"[{actual_min:.2f}, {actual_max:.2f}]",
                    status=range_status,
                    message=range_msg,
                    details={"out_of_range_count": int(out_of_range)}
                ))

            contract_summaries[field_name] = {
                "datatype": str(series.dtype),
                "null_count": null_count,
                "nullable_permitted": is_nullable
            }

        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        summary = CheckSummary(
            category="Schema & Data Contracts",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=[f"Validated {len(self.contracts)} formal field contracts for Module 1 with {fail_count} failures."]
        )

        return summary, results, contract_summaries
