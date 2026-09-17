"""
Boreas-Nexus Module 1 - Hotspot Confidence Scorer (Part 2 Extension)

Purpose: Compute a deterministic, transparent 0-100 Hotspot Confidence Score and assign
confidence classifications based on a configurable weighted combination of:
1. Getis-Ord Gi* Z-score (45%)
2. Surface Urban Heat Island Intensity - SUHII (30%)
3. Heat Persistence Index (15%)
4. City Temperature Percentile (10%)
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger
from storage.storage_manager import StorageManager


class HotspotConfidenceScorer:
    """
    Computes deterministic 0-100 Hotspot Confidence Score and confidence classification.
    """

    def __init__(
        self,
        scoring_config_path: Path | str = Path("config/hotspot_scoring.yaml"),
        input_path: Path | str | None = None,
        output_dir: Path | str | None = None
    ):
        self.scoring_config_path = Path(scoring_config_path)
        self.storage_manager = StorageManager()
        self.custom_output_dir = (output_dir is not None)

        if input_path is not None:
            self.input_path = Path(input_path)
        else:
            self.input_path = self.storage_manager.get_debug_filepath("module_1", "module_1_stage5_pct.parquet")

        if output_dir is not None:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.storage_manager.get_debug_dir("module_1")

        self.config = self._load_scoring_config()
        self.last_gdf: Optional[gpd.GeoDataFrame] = None

    def _load_scoring_config(self) -> Dict[str, Any]:
        """Loads scoring configuration from YAML."""
        default_config = {
            "weights": {
                "gi_zscore": 0.45,
                "suhii": 0.30,
                "heat_persistence": 0.15,
                "temperature_percentile": 0.10
            },
            "confidence_classes": [
                {"name": "Critical", "min_score": 95.0},
                {"name": "Very High", "min_score": 80.0},
                {"name": "High", "min_score": 60.0},
                {"name": "Moderate", "min_score": 40.0},
                {"name": "Low", "min_score": 20.0},
                {"name": "Very Low", "min_score": 0.0}
            ]
        }

        p = Path(self.scoring_config_path)
        if not p.exists():
            logger.warning(f"Scoring config not found at {p}. Using default weights.")
            return default_config

        try:
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            scoring = data.get("hotspot_scoring", {})
            weights = scoring.get("weights", default_config["weights"])
            classes = scoring.get("confidence_classes", default_config["confidence_classes"])

            return {
                "weights": weights,
                "confidence_classes": classes
            }
        except Exception as e:
            logger.warning(f"Failed to load scoring config from {p}: {e}. Using default weights.")
            return default_config

    def load_input_data(self) -> gpd.GeoDataFrame:
        """Loads dataset with percentiles."""
        candidates = [
            self.input_path,
            self.output_dir / "module_1_stage5_pct.parquet",
            self.storage_manager.get_debug_filepath("module_1", "module_1_stage5_pct.parquet"),
            self.storage_manager.get_debug_filepath("module_1", "module_1_stage5_labeled.parquet"),
            self.storage_manager.get_processed_filepath("feature_engineering", "features.geoparquet"),
            Path("data/processed/features.parquet")
        ]

        target_path = None
        for p in candidates:
            if p.exists():
                target_path = p
                break

        if target_path is not None:
            logger.info(f"Loading dataset from: {target_path}...")
            df = pd.read_parquet(target_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
            return gdf

        raise FileNotFoundError(f"Input dataset not found at {self.input_path}.")

    def _min_max_normalize(self, arr: np.ndarray, default_val: float = 0.0) -> np.ndarray:
        """Normalizes array values to [0, 1] range using min-max scaling."""
        valid_mask = ~np.isnan(arr)
        if not valid_mask.any():
            return np.full_like(arr, default_val)

        min_v = np.nanmin(arr)
        max_v = np.nanmax(arr)

        if max_v == min_v:
            norm_arr = np.full_like(arr, 0.5)
        else:
            norm_arr = (arr - min_v) / (max_v - min_v)

        norm_arr = np.clip(norm_arr, 0.0, 1.0)
        norm_arr[~valid_mask] = 0.0
        return norm_arr

    def compute_confidence_scores(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Calculates weighted hotspot_confidence_score and assigns confidence_class independently for day and night."""
        result_gdf = gdf.copy()
        logger.info("Computing Hotspot Confidence Scores (0-100)...")

        weights = self.config["weights"]
        w_gi = float(weights.get("gi_zscore", 0.45))
        w_suhii = float(weights.get("suhii", 0.30))
        w_hp = float(weights.get("heat_persistence", 0.15))
        w_pct = float(weights.get("temperature_percentile", 0.10))

        z_day = result_gdf.get("gi_zscore_day", pd.Series(0.0, index=result_gdf.index)).values.astype(np.float64)
        z_night = result_gdf.get("gi_zscore_night", pd.Series(0.0, index=result_gdf.index)).values.astype(np.float64)

        norm_gi_day = self._min_max_normalize(z_day)
        norm_gi_night = self._min_max_normalize(z_night)
        norm_gi_comp = self._min_max_normalize(np.maximum(z_day, z_night))

        suhii_day = result_gdf.get("suhii_day_celsius", pd.Series(0.0, index=result_gdf.index)).values.astype(np.float64)
        suhii_night = result_gdf.get("suhii_night_celsius", pd.Series(0.0, index=result_gdf.index)).values.astype(np.float64)

        norm_suhii_day = self._min_max_normalize(suhii_day)
        norm_suhii_night = self._min_max_normalize(suhii_night)
        norm_suhii_comp = self._min_max_normalize(np.maximum(suhii_day, suhii_night))

        hp = result_gdf.get("heat_persistence_index", pd.Series(0.0, index=result_gdf.index)).values.astype(np.float64)
        norm_hp = self._min_max_normalize(hp)

        pct = result_gdf.get("city_temperature_percentile", pd.Series(0.0, index=result_gdf.index)).values.astype(np.float64)
        norm_pct = np.nan_to_num(pct / 100.0, nan=0.0)

        raw_score_day = 100.0 * (w_gi * norm_gi_day + w_suhii * norm_suhii_day + w_hp * norm_hp + w_pct * norm_pct)
        raw_score_night = 100.0 * (w_gi * norm_gi_night + w_suhii * norm_suhii_night + w_hp * norm_hp + w_pct * norm_pct)
        raw_score_comp = 100.0 * (w_gi * norm_gi_comp + w_suhii * norm_suhii_comp + w_hp * norm_hp + w_pct * norm_pct)

        scores_day = np.round(np.clip(raw_score_day, 0.0, 100.0), 2)
        scores_night = np.round(np.clip(raw_score_night, 0.0, 100.0), 2)
        scores_comp = np.round(np.clip(raw_score_comp, 0.0, 100.0), 2)

        conf_classes_cfg = sorted(
            self.config["confidence_classes"],
            key=lambda x: float(x.get("min_score", x.get("min", 0))),
            reverse=True
        )

        def assign_class(s: float) -> str:
            for item in conf_classes_cfg:
                threshold = float(item.get("min_score", item.get("min", 0)))
                name = str(item.get("name", item.get("class", "Very Low")))
                if s >= threshold:
                    return name
            return "Very Low"

        # Masks for period-specific clusters
        has_day_id = result_gdf["day_hotspot_id"].notnull() if "day_hotspot_id" in result_gdf.columns else pd.Series(False, index=result_gdf.index)
        has_night_id = result_gdf["night_hotspot_id"].notnull() if "night_hotspot_id" in result_gdf.columns else pd.Series(False, index=result_gdf.index)

        day_final_scores = np.full(len(result_gdf), np.nan, dtype=np.float64)
        night_final_scores = np.full(len(result_gdf), np.nan, dtype=np.float64)
        comp_final_scores = np.full(len(result_gdf), np.nan, dtype=np.float64)
        final_classes = np.full(len(result_gdf), None, dtype=object)

        for i in range(len(result_gdf)):
            d_flag = has_day_id.iloc[i] if hasattr(has_day_id, 'iloc') else has_day_id[i]
            n_flag = has_night_id.iloc[i] if hasattr(has_night_id, 'iloc') else has_night_id[i]

            if d_flag:
                day_final_scores[i] = scores_day[i]
            if n_flag:
                night_final_scores[i] = scores_night[i]

            if d_flag or n_flag:
                comp_s = scores_comp[i]
                comp_final_scores[i] = comp_s
                final_classes[i] = assign_class(comp_s)

        result_gdf["day_hotspot_confidence_score"] = day_final_scores
        result_gdf["night_hotspot_confidence_score"] = night_final_scores
        result_gdf["hotspot_confidence_score"] = comp_final_scores
        result_gdf["confidence_class"] = final_classes

        return result_gdf

    def run(self, gdf_in: Optional[gpd.GeoDataFrame] = None) -> Dict[str, Any]:
        """Executes Hotspot Confidence Scorer."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - EXTENSION 3: HOTSPOT CONFIDENCE SCORE")
        logger.info("=================================================================")

        gdf = gdf_in.copy() if gdf_in is not None else self.load_input_data()
        gdf_scored = self.compute_confidence_scores(gdf)

        self.last_gdf = gdf_scored

        valid_scores = gdf_scored["hotspot_confidence_score"].dropna()
        metrics = {
            "status": "SUCCESS",
            "evaluated_hotspots": len(valid_scores),
            "mean_confidence_score": round(float(valid_scores.mean()), 2) if len(valid_scores) > 0 else 0.0,
            "max_confidence_score": round(float(valid_scores.max()), 2) if len(valid_scores) > 0 else 0.0,
            "min_confidence_score": round(float(valid_scores.min()), 2) if len(valid_scores) > 0 else 0.0,
            "confidence_class_counts": gdf_scored["confidence_class"].value_counts().to_dict()
        }

        if self.custom_output_dir or self.storage_manager.should_save_intermediate():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            parquet_out = self.output_dir / "module_1_stage5_scored.parquet"
            logger.info(f"Saving intermediate scored dataset to {parquet_out}...")
            df_export = pd.DataFrame(gdf_scored.drop(columns=["geometry"]))
            df_export.to_parquet(parquet_out, index=False)
            metrics["output_parquet"] = str(parquet_out)

        logger.info(f"Hotspot Confidence Scorer complete! Mean score: {metrics['mean_confidence_score']}")
        logger.info("=================================================================")
        return metrics
