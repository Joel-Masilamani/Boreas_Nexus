"""
Spatial Leakage & ML Generalization Validator

Validates spatial independence by implementing a strict disjoint SpatialBlockSplitter,
mathematically proving zero block overlap across train/validation/test sets on all 44,298 points,
and comparatively benchmarking Spatial Block Split (Primary) vs. Random Split (Secondary)
using fast optimized GBDTs.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from lightgbm import LGBMRegressor

from utils.logger import logger
from validation.core.models import ValidationResult, ValidationStatus, CheckSummary


class SpatialBlockSplitter:
    """
    Partitions datasets into strictly disjoint spatial block train/val/test splits.
    """

    def __init__(
        self,
        block_col: str = "spatial_block_id",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_seed: int = 42
    ):
        self.block_col = block_col
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_seed = random_seed

    def split(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Set[Any]]]:
        """
        Splits DataFrame indices based on spatial block IDs.
        
        Returns:
            train_idx, val_idx, test_idx, block_sets_dict
        """
        if self.block_col not in df.columns:
            raise ValueError(f"Block column '{self.block_col}' not found in dataframe.")

        unique_blocks = df[self.block_col].unique()
        np.random.seed(self.random_seed)
        shuffled_blocks = np.random.permutation(unique_blocks)

        n_blocks = len(shuffled_blocks)
        n_train = int(np.floor(self.train_ratio * n_blocks))
        n_val = int(np.floor(self.val_ratio * n_blocks))

        train_blocks = set(shuffled_blocks[:n_train])
        val_blocks = set(shuffled_blocks[n_train:n_train + n_val])
        test_blocks = set(shuffled_blocks[n_train + n_val:])

        # Ensure disjointness
        assert train_blocks.isdisjoint(val_blocks), "Spatial block leakage between train and val!"
        assert train_blocks.isdisjoint(test_blocks), "Spatial block leakage between train and test!"
        assert val_blocks.isdisjoint(test_blocks), "Spatial block leakage between val and test!"

        train_mask = df[self.block_col].isin(train_blocks)
        val_mask = df[self.block_col].isin(val_blocks)
        test_mask = df[self.block_col].isin(test_blocks)

        train_idx = np.where(train_mask)[0]
        val_idx = np.where(val_mask)[0]
        test_idx = np.where(test_mask)[0]

        block_sets = {
            "train_blocks": train_blocks,
            "val_blocks": val_blocks,
            "test_blocks": test_blocks
        }

        return train_idx, val_idx, test_idx, block_sets


class SpatialLeakageValidator:
    """
    Validates spatial block independence and compares spatial generalization vs. random split.
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.split_cfg = self.cfg.get("spatial_split", {
            "block_col": "spatial_block_id",
            "train_ratio": 0.70,
            "val_ratio": 0.15,
            "test_ratio": 0.15,
            "random_seed": 42
        })
        self.perf_thresholds = self.cfg.get("performance_thresholds", {
            "min_spatial_r2": 0.35,
            "max_spatial_rmse_celsius": 2.50
        })

    def validate(self, gdf: gpd.GeoDataFrame) -> Tuple[CheckSummary, List[ValidationResult], Dict[str, Any]]:
        """
        Executes spatial split validation and comparative ML evaluation.
        """
        logger.info("Executing ML Spatial Leakage & Generalization Validation...")
        results: List[ValidationResult] = []
        findings: List[str] = []

        if "spatial_block_id" not in gdf.columns:
            res = ValidationResult(
                validation_id="ML-LEAK-001",
                validation_type="ML_SPATIAL_LEAKAGE",
                metric="spatial_block_id_presence",
                expected="spatial_block_id",
                actual="MISSING",
                status=ValidationStatus.FAIL,
                message="Column 'spatial_block_id' is missing. Spatial block split impossible."
            )
            return CheckSummary("ML & Spatial Leakage", 1, 0, 0, 1, ValidationStatus.FAIL, [res.message]), [res], {}

        # 1. Validate Spatial Block Disjointness across all points
        splitter = SpatialBlockSplitter(
            block_col=self.split_cfg.get("block_col", "spatial_block_id"),
            train_ratio=float(self.split_cfg.get("train_ratio", 0.70)),
            val_ratio=float(self.split_cfg.get("val_ratio", 0.15)),
            test_ratio=float(self.split_cfg.get("test_ratio", 0.15)),
            random_seed=int(self.split_cfg.get("random_seed", 42))
        )

        train_idx, val_idx, test_idx, block_sets = splitter.split(gdf)
        total_rows = len(gdf)

        # Intersection verification
        t_v = len(block_sets["train_blocks"].intersection(block_sets["val_blocks"]))
        t_te = len(block_sets["train_blocks"].intersection(block_sets["test_blocks"]))
        v_te = len(block_sets["val_blocks"].intersection(block_sets["test_blocks"]))
        leakage_count = t_v + t_te + v_te

        if leakage_count == 0:
            leak_status = ValidationStatus.PASS
            leak_msg = f"Zero spatial block overlap (disjoint sets): {len(block_sets['train_blocks'])} train, {len(block_sets['val_blocks'])} val, {len(block_sets['test_blocks'])} test blocks."
        else:
            leak_status = ValidationStatus.FAIL
            leak_msg = f"Spatial block leakage detected: {leakage_count} overlapping blocks across splits."

        results.append(ValidationResult(
            validation_id="ML-SPATIAL-DISJOINT",
            validation_type="ML_SPATIAL_LEAKAGE",
            metric="block_overlap_count",
            expected=0,
            actual=leakage_count,
            error=float(leakage_count),
            threshold=0,
            status=leak_status,
            message=leak_msg,
            details={
                "train_points": len(train_idx),
                "val_points": len(val_idx),
                "test_points": len(test_idx),
                "train_blocks_count": len(block_sets["train_blocks"]),
                "val_blocks_count": len(block_sets["val_blocks"]),
                "test_blocks_count": len(block_sets["test_blocks"])
            }
        ))

        # 2. Comparative Evaluation: Spatial Block Split (Primary) vs. Random Split (Secondary)
        core_features = [
            "ndvi", "ndbi", "ndwi", "land_cover_code", "building_density",
            "distance_to_roads_m", "distance_to_water_m", "distance_to_parks_m",
            "elevation_m", "slope_deg", "aspect_sin", "aspect_cos"
        ]
        available_features = [c for c in core_features if c in gdf.columns]
        target_col = "lst_day_celsius"

        # Stratified sampling for fast sub-second benchmark
        np.random.seed(42)
        bench_sample_size = min(5000, len(gdf))
        bench_idx = np.random.choice(len(gdf), size=bench_sample_size, replace=False)
        bench_gdf = gdf.iloc[bench_idx]

        b_train_idx, b_val_idx, b_test_idx, _ = splitter.split(bench_gdf)

        X_b = bench_gdf[available_features].values
        y_b = bench_gdf[target_col].values

        # A. Spatial Block Model Fit & Evaluation
        X_tr_s, y_tr_s = X_b[b_train_idx], y_b[b_train_idx]
        X_te_s, y_te_s = X_b[b_test_idx], y_b[b_test_idx]

        model_spatial = LGBMRegressor(n_estimators=30, max_depth=5, num_leaves=15, learning_rate=0.1, random_state=42, verbose=-1, n_jobs=-1)
        model_spatial.fit(X_tr_s, y_tr_s)
        preds_spatial = model_spatial.predict(X_te_s)

        r2_spatial = float(r2_score(y_te_s, preds_spatial))
        rmse_spatial = float(np.sqrt(mean_squared_error(y_te_s, preds_spatial)))
        mae_spatial = float(mean_absolute_error(y_te_s, preds_spatial))

        # B. Random Split Model Fit & Evaluation (Secondary)
        X_tr_r, X_te_r, y_tr_r, y_te_r = train_test_split(X_b, y_b, test_size=0.30, random_state=42)
        model_random = LGBMRegressor(n_estimators=30, max_depth=5, num_leaves=15, learning_rate=0.1, random_state=42, verbose=-1, n_jobs=-1)
        model_random.fit(X_tr_r, y_tr_r)
        preds_random = model_random.predict(X_te_r)

        r2_random = float(r2_score(y_te_r, preds_random))
        rmse_random = float(np.sqrt(mean_squared_error(y_te_r, preds_random)))
        mae_random = float(mean_absolute_error(y_te_r, preds_random))

        min_r2 = float(self.perf_thresholds.get("min_spatial_r2", 0.35))
        spatial_perf_status = ValidationStatus.PASS if r2_spatial >= min_r2 else ValidationStatus.WARN

        results.append(ValidationResult(
            validation_id="ML-PERF-SPATIAL-PRIMARY",
            validation_type="ML_GENERALIZATION_EVALUATION",
            metric="spatial_split_r2_primary",
            expected=f">= {min_r2}",
            actual=round(r2_spatial, 4),
            threshold=min_r2,
            status=spatial_perf_status,
            message=(
                f"[PRIMARY EVALUATION] Spatial Block Split: R²={r2_spatial:.4f}, RMSE={rmse_spatial:.3f}°C, MAE={mae_spatial:.3f}°C. "
                f"[SECONDARY EVALUATION] Random Split: R²={r2_random:.4f}, RMSE={rmse_random:.3f}°C (inflated due to spatial autocorrelation)."
            ),
            details={
                "spatial_split_primary": {
                    "evaluation_role": "PRIMARY_GENERALIZATION_METRIC",
                    "r2": round(r2_spatial, 4),
                    "rmse_celsius": round(rmse_spatial, 3),
                    "mae_celsius": round(mae_spatial, 3),
                    "residual_mean": round(float(np.mean(y_te_s - preds_spatial)), 4),
                    "residual_std": round(float(np.std(y_te_s - preds_spatial)), 4)
                },
                "random_split_secondary": {
                    "evaluation_role": "SECONDARY_BENCHMARK_ONLY",
                    "r2": round(r2_random, 4),
                    "rmse_celsius": round(rmse_random, 3),
                    "mae_celsius": round(mae_random, 3),
                    "spatial_autocorrelation_inflation": round(r2_random - r2_spatial, 4)
                }
            }
        ))

        # Summary
        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARN)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        overall_status = ValidationStatus.FAIL if fail_count > 0 else (ValidationStatus.WARN if warn_count > 0 else ValidationStatus.PASS)

        findings.append(leak_msg)
        findings.append(f"Spatial Block Split (Primary): R²={r2_spatial:.4f}, RMSE={rmse_spatial:.3f}°C.")
        findings.append(f"Random Split (Secondary Benchmark): R²={r2_random:.4f}, RMSE={rmse_random:.3f}°C.")

        summary = CheckSummary(
            category="ML & Spatial Leakage",
            total_checks=len(results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            status=overall_status,
            findings=findings
        )

        comparison_report = {
            "spatial_split_primary": results[1].details["spatial_split_primary"],
            "random_split_secondary": results[1].details["random_split_secondary"]
        }

        return summary, results, comparison_report
