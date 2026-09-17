"""
Boreas-Nexus Module 1 Pipeline Orchestrator

Executes all stages of Module 1: Physical Urban Heat & Hotspot Intelligence Engine:
Stage 1: Data Acquisition & Preprocessing Alignment
Stage 2: Urban–Non-Urban Delineation
Stage 3: Surface Urban Heat Island (SUHII) Computation
Stage 4: Night-Time Thermal Behaviour Analysis
Stage 5: Spatial Hotspot Validation (Getis-Ord Gi*)
Extension 1: Hotspot Cluster Generator (Connected Component Analysis)
Extension 2: City Temperature Percentile Calculator
Extension 3: Hotspot Confidence Scorer (0-100 Weighted Model)
Stage 6: Urban Heat Hotspot Knowledge Layer Export (GeoParquet & Registry)
"""

from pathlib import Path
from typing import Dict, Any

from utils.logger import logger
from module_1_thermal.stage1_data_aligner import Stage1DataAligner
from module_1_thermal.stage2_urban_delineation import Stage2UrbanDelineator
from module_1_thermal.stage3_suhii_calculator import Stage3SUHIICalculator
from module_1_thermal.stage4_nighttime_thermal import Stage4NighttimeThermal
from module_1_thermal.stage5_hotspot_validator import Stage5HotspotValidator
from module_1_thermal.hotspot_cluster_generator import HotspotClusterGenerator
from module_1_thermal.city_temperature_percentile import CityTemperaturePercentileCalculator
from module_1_thermal.hotspot_confidence_scorer import HotspotConfidenceScorer
from module_1_thermal.stage6_knowledge_export import Stage6KnowledgeExporter


class Module1ThermalPipeline:
    """
    Class orchestrating end-to-end execution of Module 1.
    """

    def __init__(
        self,
        config_path: Path | str = Path("config/city.yaml"),
        scoring_config_path: Path | str = Path("config/hotspot_scoring.yaml")
    ):
        self.config_path = Path(config_path)
        self.scoring_config_path = Path(scoring_config_path)

    def run(self) -> Dict[str, Any]:
        """Runs Stage 1 through Stage 6 sequentially including extensions."""
        logger.info("=================================================================")
        logger.info("STARTING MODULE 1: PHYSICAL URBAN HEAT & HOTSPOT INTELLIGENCE ENGINE")
        logger.info("=================================================================")

        # Stage 1: Data Acquisition & Preprocessing Alignment
        s1 = Stage1DataAligner(config_path=self.config_path)
        m1 = s1.run()

        # Stage 2: Urban-Rural Delineation
        s2 = Stage2UrbanDelineator()
        m2 = s2.run(gdf_in=s1.last_gdf)

        # Stage 3: SUHII Computation
        s3 = Stage3SUHIICalculator()
        m3 = s3.run(gdf_in=s2.last_gdf)

        # Stage 4: Night-Time Thermal Analysis
        s4 = Stage4NighttimeThermal()
        m4 = s4.run(gdf_in=s3.last_gdf)

        # Stage 5: Spatial Hotspot Validation (Getis-Ord Gi*)
        s5 = Stage5HotspotValidator()
        m5 = s5.run(gdf_in=s4.last_gdf)

        # Extension 1: Hotspot Cluster Generator
        cluster_gen = HotspotClusterGenerator(
            config_path=self.config_path,
            scoring_config_path=self.scoring_config_path
        )
        m_cluster = cluster_gen.run(gdf_in=s5.last_gdf)

        # Extension 2: City Temperature Percentile
        pct_calc = CityTemperaturePercentileCalculator()
        m_pct = pct_calc.run(gdf_in=cluster_gen.last_gdf)

        # Extension 3: Hotspot Confidence Scorer
        conf_scorer = HotspotConfidenceScorer(scoring_config_path=self.scoring_config_path)
        m_conf = conf_scorer.run(gdf_in=pct_calc.last_gdf)

        # Stage 6: Knowledge Layer & Registry Exporter
        s6 = Stage6KnowledgeExporter(config_path=self.config_path)
        m6 = s6.run(gdf_in=conf_scorer.last_gdf)

        summary = {
            "module": "Module 1",
            "status": "SUCCESS",
            "stage1_metrics": m1,
            "stage2_metrics": m2,
            "stage3_metrics": m3,
            "stage4_metrics": m4,
            "stage5_metrics": m5,
            "cluster_metrics": m_cluster,
            "percentile_metrics": m_pct,
            "confidence_metrics": m_conf,
            "stage6_manifest": m6
        }

        logger.info("=================================================================")
        logger.info("MODULE 1 EXECUTION FINISHED WITH STATUS: SUCCESS")
        logger.info("=================================================================")
        return summary
