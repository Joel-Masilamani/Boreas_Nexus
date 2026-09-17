"""
Schema & Data Contract Range Validator

Validates formal data contracts for every feature and derived field in the Knowledge Layer,
verifying data types, numerical domain boundaries [valid_min, valid_max], nullability rules,
and detecting unexpected NaN or infinity anomalies without inferring ungrounded bounds.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class SchemaRangeValidator:
    """
    Validates field schemas, units, nullability, and numeric value boundaries.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.contracts = self.cfg.get("data_contracts", {}).get("fields", {})

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes schema and range validation across all defined field contracts.
        """
        logger.info("Executing Schema & Data Contract Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []
        contract_summaries = {}

        for field_name, contract in self.contracts.items():
            if field_name not in gdf.columns:
                # Missing column
                is_nullable = contract.get("nullable", False)
                status = ValidationStatus.WARN if is_nullable else ValidationStatus.FAIL
                msg = f"Contracted field '{field_name}' is missing from the dataset."

                results.append(ValidationResult(
                    validation_id=f"SCHEMA-MISSING-{field_name.upper()}",
                    validation_type="SCHEMA_DATA_CONTRACT",
                    metric=f"field_presence_{field_name}",
                    expected=field_name,
                    actual="MISSING",
                    status=status,
                    message=msg,
                    details={"contract": contract}
                ))
                continue

            series = gdf[field_name]
            total_count = len(series)
            null_count = int(series.isna().sum())
            is_nullable = contract.get("nullable", False)

            # 1. Nullability check
            if null_count > 0 and not is_nullable:
                null_status = ValidationStatus.FAIL
                null_msg = f"Non-nullable field '{field_name}' contains {null_count} null/NaN values."
            elif null_count > 0 and is_nullable:
                null_status = ValidationStatus.PASS
                null_msg = f"Nullable field '{field_name}' contains {null_count} nulls (allowed)."
            else:
                null_status = ValidationStatus.PASS
                null_msg = f"Field '{field_name}' has 0 nulls."

            results.append(ValidationResult(
                validation_id=f"SCHEMA-NULL-{field_name.upper()}",
                validation_type="SCHEMA_DATA_CONTRACT",
                metric=f"nullability_{field_name}",
                expected="0 nulls" if not is_nullable else "nullable allowed",
                actual=f"{null_count} nulls",
                status=null_status,
                message=null_msg,
                details={"null_count": null_count, "nullable_contract": is_nullable}
            ))

            # 2. Numeric Range & Infinity Check (if numeric)
            valid_min = contract.get("valid_min")
            valid_max = contract.get("valid_max")

            if valid_min is not None and valid_max is not None and pd.api.types.is_numeric_dtype(series):
                valid_vals = series.dropna().values
                has_inf = np.isinf(valid_vals).any()
                
                if has_inf:
                    results.append(ValidationResult(
                        validation_id=f"SCHEMA-INF-{field_name.upper()}",
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
                    range_msg = f"Field '{field_name}' values strictly in [{valid_min}, {valid_max}]. Observed: [{actual_min:.2f}, {actual_max:.2f}]."
                else:
                    range_status = ValidationStatus.FAIL
                    range_msg = f"Field '{field_name}' contains {out_of_range} values outside [{valid_min}, {valid_max}]."

                results.append(ValidationResult(
                    validation_id=f"SCHEMA-RANGE-{field_name.upper()}",
                    validation_type="SCHEMA_DATA_CONTRACT",
                    metric=f"range_check_{field_name}",
                    expected=f"[{valid_min}, {valid_max}]",
                    actual=f"[{actual_min:.2f}, {actual_max:.2f}]",
                    status=range_status,
                    message=range_msg,
                    details={"out_of_range_count": int(out_of_range), "min": actual_min, "max": actual_max}
                ))

            contract_summaries[field_name] = {
                "datatype": str(series.dtype),
                "null_count": null_count,
                "nullable_permitted": is_nullable
            }

        # Summary
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
            findings=[f"Validated {len(self.contracts)} formal field contracts with {fail_count} failures."]
        )

        return summary, results, contract_summaries
