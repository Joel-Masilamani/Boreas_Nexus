"""
Boreas-Nexus Module 1 - Hotspot Confidence Scorer (Part 2 Extension)

Purpose: Compute a deterministic, transparent 0-100 Hotspot Confidence Score and assign
confidence classifications based on a configurable weighted combination of:
1. Getis-Ord Gi* Z-score (45%)
2. Surface Urban Heat Island Intensity - SUHII (30%)
3. Heat Persistence Index (15%)
4. City Temperature Percentile (10%)

Configuration: Read from config/hotspot_scoring.yaml. Never hardcode weights.
"""

from pathlib import Path
from typing import Dict, Any
import yaml
import pandas as pd
import geopandas as gpd
import numpy as np

from utils.logger import logger


class HotspotConfidenceScorer:
    """
    Computes deterministic 0-100 Hotspot Confidence Score and confidence classification.
    """

    def __init__(
        self,
        scoring_config_path: Path | str = Path("config/hotspot_scoring.yaml"),
        input_path: Path | str = Path("data/processed/module_1_stage5_pct.parquet"),
        output_dir: Path | str = Path("data/processed")
    ):
        self.scoring_config_path = Path(scoring_config_path)
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.config = self._load_scoring_config()

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
                {"name": "Critical", "min_score": 90.0},
                {"name": "Very High", "min_score": 75.0},
                {"name": "High", "min_score": 60.0},
                {"name": "Moderate", "min_score": 45.0},
                {"name": "Low", "min_score": 30.0},
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
        if self.input_path.exists():
            logger.info(f"Loading percentile dataset from Parquet: {self.input_path}...")
            df = pd.read_parquet(self.input_path)
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
                crs="EPSG:4326"
            )
        else:
            geojson_path = self.input_path.with_suffix(".geojson")
            if geojson_path.exists():
                logger.info(f"Loading percentile dataset from GeoJSON: {geojson_path}...")
                gdf = gpd.read_file(geojson_path)
            else:
                raise FileNotFoundError(f"Input dataset not found at {self.input_path}.")

        return gdf

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
        """
        Calculates weighted hotspot_confidence_score and assigns confidence_class.
        """
        result_gdf = gdf.copy()
        logger.info("Computing Hotspot Confidence Scores (0-100)...")

        weights = self.config["weights"]
        w_gi = float(weights.get("gi_zscore", 0.45))
        w_suhii = float(weights.get("suhii", 0.30))
        w_hp = float(weights.get("heat_persistence", 0.15))
        w_pct = float(weights.get("temperature_percentile", 0.10))

        # Normalize components
        # 1. Gi* Z-score
        z_day = result_gdf.get("gi_zscore_day", pd.Series(0.0, index=result_gdf.index)).values
        z_night = result_gdf.get("gi_zscore_night", pd.Series(0.0, index=result_gdf.index)).values
        z_comp = np.maximum(z_day, z_night)
        norm_gi = self._min_max_normalize(z_comp)

        # 2. SUHII
        suhii_day = result_gdf.get("suhii_day_celsius", pd.Series(0.0, index=result_gdf.index)).values
        suhii_night = result_gdf.get("suhii_night_celsius", pd.Series(0.0, index=result_gdf.index)).values
        suhii_comp = np.maximum(suhii_day, suhii_night)
        norm_suhii = self._min_max_normalize(suhii_comp)

        # 3. Heat Persistence
        hp = result_gdf.get("heat_persistence_index", pd.Series(0.0, index=result_gdf.index)).values
        norm_hp = self._min_max_normalize(hp)

        # 4. City Temperature Percentile
        pct = result_gdf.get("city_temperature_percentile", pd.Series(0.0, index=result_gdf.index)).values
        norm_pct = np.nan_to_num(pct / 100.0, nan=0.0)

        # Calculate weighted confidence score
        raw_score = 100.0 * (
            w_gi * norm_gi +
            w_suhii * norm_suhii +
            w_hp * norm_hp +
            w_pct * norm_pct
        )
        scores = np.round(np.clip(raw_score, 0.0, 100.0), 2)

        # Classify scores into confidence classes
        classes = []
        conf_classes_cfg = sorted(
            self.config["confidence_classes"],
            key=lambda x: float(x.get("min_score", x.get("min", 0))),
            reverse=True
        )

        for s in scores:
            assigned_cls = "Very Low"
            for item in conf_classes_cfg:
                threshold = float(item.get("min_score", item.get("min", 0)))
                name = str(item.get("name", item.get("class", "Very Low")))
                if s >= threshold:
                    assigned_cls = name
                    break
            classes.append(assigned_cls)

        result_gdf["hotspot_confidence_score"] = scores
        result_gdf["confidence_class"] = classes

        return result_gdf

    def run(self) -> Dict[str, Any]:
        """Executes Hotspot Confidence Scorer and updates intermediate dataset."""
        logger.info("=================================================================")
        logger.info("MODULE 1 - EXTENSION 2: HOTSPOT CONFIDENCE SCORE")
        logger.info("=================================================================")

        gdf = self.load_input_data()
        gdf_scored = self.compute_confidence_scores(gdf)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        parquet_out = self.output_dir / "module_1_stage5_scored.parquet"

        logger.info(f"Saving scored dataset to {parquet_out}...")
        df_export = pd.DataFrame(gdf_scored.drop(columns=["geometry"]))
        df_export.to_parquet(parquet_out, index=False)

        metrics = {
            "status": "SUCCESS",
            "mean_confidence_score": round(float(gdf_scored["hotspot_confidence_score"].mean()), 2),
            "max_confidence_score": round(float(gdf_scored["hotspot_confidence_score"].max()), 2),
            "min_confidence_score": round(float(gdf_scored["hotspot_confidence_score"].min()), 2),
            "confidence_class_counts": gdf_scored["confidence_class"].value_counts().to_dict(),
            "output_parquet": str(parquet_out)
        }

        logger.info(f"Hotspot Confidence Scorer complete! Mean score: {metrics['mean_confidence_score']}")
        logger.info("=================================================================")
        return metrics
