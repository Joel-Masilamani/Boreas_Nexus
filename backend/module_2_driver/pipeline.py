"""
Boreas-Nexus Module 2: Urban Heat Driver Intelligence Pipeline Orchestrator

Executes all 7 stages of Module 2 sequentially:
Stage 1: Multi-Source Feature Engineering & Alignment (Circular Aspect)
Stage 2: Baseline Driver Modeling (Random Forest + Spatial Block CV)
Stage 3: Advanced Driver Modeling (LightGBM + Spatial Block CV + Performance Gates)
Stage 4: Explainable AI Driver Attribution (SHAP TreeExplainer + Additive Check)
Stage 5: XAI Attribution Plausibility Audit (Directional Sanity Check)
Stage 6: Spatial Driver Intelligence (Spatially Balanced GWR)
Stage 7: Urban Heat Driver Knowledge Layer Export & Registry Generation
"""

from pathlib import Path
from typing import Dict, Any, Optional
import time
import json
import geopandas as gpd

from utils.logger import logger
from module_2_driver.stage1_feature_builder import Stage1FeatureBuilder
from module_2_driver.stage2_baseline_rf import Stage2BaselineRF
from module_2_driver.stage3_advanced_lgbm import Stage3AdvancedLGBM
from module_2_driver.stage4_shap_explainer import Stage4ShapExplainer
from module_2_driver.stage5_physics_validator import Stage5PhysicsValidator
from module_2_driver.stage6_spatial_gwr import Stage6SpatialGWR
from module_2_driver.stage7_driver_knowledge_export import Stage7DriverKnowledgeExporter


class Module2DriverPipeline:
    """
    Orchestrator class managing end-to-end execution of Module 2.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/driver_analysis.yaml"),
        output_dir: Optional[Path | str] = None,
        metadata_dir: Optional[Path | str] = None,
        hotspot_registry_path: Optional[Path | str] = None
    ):
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.metadata_dir = Path(metadata_dir) if metadata_dir is not None else None
        self.hotspot_registry_path = Path(hotspot_registry_path) if hotspot_registry_path is not None else None

    def run(self, gdf_in: Optional[gpd.GeoDataFrame] = None) -> Dict[str, Any]:
        """
        Executes all stages of Module 2 sequentially with progress logging.
        """
        start_time = time.time()
        logger.info("=================================================================")
        logger.info("STARTING MODULE 2: URBAN HEAT DRIVER INTELLIGENCE ENGINE")
        logger.info("=================================================================")

        # Stage 1: Feature Engineering & Alignment
        s1 = Stage1FeatureBuilder(config_path=self.config_path)
        m1 = s1.run(gdf_in=gdf_in)

        # Stage 2: Baseline Random Forest Modeling
        s2 = Stage2BaselineRF(config_path=self.config_path)
        m2 = s2.run(gdf_in=s1.last_gdf)

        # Stage 3: Advanced LightGBM Modeling
        s3 = Stage3AdvancedLGBM(config_path=self.config_path)
        m3 = s3.run(gdf_in=s2.last_gdf)

        # Stage 4: Explainable AI Driver Attribution (SHAP)
        s4 = Stage4ShapExplainer(config_path=self.config_path)
        m4 = s4.run(gdf_in=s3.last_gdf, lgbm_models=s3.lgbm_models)

        # Stage 5: XAI Attribution Plausibility Audit
        s5 = Stage5PhysicsValidator(config_path=self.config_path)
        m5 = s5.run(gdf_in=s4.last_gdf)

        # Stage 6: Spatial Driver Intelligence (GWR)
        s6 = Stage6SpatialGWR(config_path=self.config_path)
        m6 = s6.run(gdf_in=s5.last_gdf)

        # Stage 7: Driver Knowledge Layer & Registry Export
        s7 = Stage7DriverKnowledgeExporter(
            config_path=self.config_path,
            output_dir=self.output_dir,
            metadata_dir=self.metadata_dir,
            hotspot_registry_path=self.hotspot_registry_path
        )
        all_metrics = {
            "stage1": m1, "stage2": m2, "stage3": m3,
            "stage4": m4, "stage5": m5, "stage6": m6
        }
        m7 = s7.run(gdf_in=s6.last_gdf, stage_metrics=all_metrics)

        elapsed_sec = round(time.time() - start_time, 2)

        summary = {
            "module": "Module 2: Urban Heat Driver Intelligence Engine",
            "status": "SUCCESS",
            "elapsed_seconds": elapsed_sec,
            "stage1_metrics": m1,
            "stage2_metrics": m2,
            "stage3_metrics": m3,
            "stage4_metrics": m4,
            "stage5_metrics": m5,
            "stage6_metrics": m6,
            "stage7_manifest": m7
        }

        logger.info("=================================================================")
        logger.info(f"MODULE 2 COMPLETED SUCCESSFULLY IN {elapsed_sec} SECONDS")
        logger.info("=================================================================")
        return summary
