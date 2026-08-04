"""
Boreas-Nexus Module 1 Pipeline Orchestrator

Executes all 6 stages of Module 1: Physical Urban Heat & Hotspot Intelligence Engine:
Stage 1: Data Acquisition & Preprocessing Alignment
Stage 2: Urban–Non-Urban Delineation
Stage 3: Surface Urban Heat Island (SUHII) Computation
Stage 4: Night-Time Thermal Behaviour Analysis
Stage 5: Spatial Hotspot Validation (Getis-Ord Gi*)
Stage 6: Urban Heat Hotspot Knowledge Layer Export
"""

from pathlib import Path
from typing import Dict, Any

from utils.logger import logger
from module_1_thermal.stage1_data_aligner import Stage1DataAligner
from module_1_thermal.stage2_urban_delineation import Stage2UrbanDelineator
from module_1_thermal.stage3_suhii_calculator import Stage3SUHIICalculator
from module_1_thermal.stage4_nighttime_thermal import Stage4NighttimeThermal
from module_1_thermal.stage5_hotspot_validator import Stage5HotspotValidator
from module_1_thermal.stage6_knowledge_export import Stage6KnowledgeExporter


class Module1ThermalPipeline:
    """
    Class orchestrating end-to-end execution of Module 1.
    """

    def __init__(self, config_path: Path | str = Path("config/city.yaml")):
        self.config_path = Path(config_path)

    def run(self) -> Dict[str, Any]:
        """Runs Stage 1 through Stage 6 sequentially."""
        logger.info("=================================================================")
        logger.info("STARTING MODULE 1: PHYSICAL URBAN HEAT & HOTSPOT INTELLIGENCE ENGINE")
        logger.info("=================================================================")

        # Stage 1
        s1 = Stage1DataAligner(config_path=self.config_path)
        m1 = s1.run()

        # Stage 2
        s2 = Stage2UrbanDelineator()
        m2 = s2.run()

        # Stage 3
        s3 = Stage3SUHIICalculator()
        m3 = s3.run()

        # Stage 4
        s4 = Stage4NighttimeThermal()
        m4 = s4.run()

        # Stage 5
        s5 = Stage5HotspotValidator()
        m5 = s5.run()

        # Stage 6
        s6 = Stage6KnowledgeExporter(config_path=self.config_path)
        m6 = s6.run()

        summary = {
            "module": "Module 1",
            "status": "SUCCESS",
            "stage1_metrics": m1,
            "stage2_metrics": m2,
            "stage3_metrics": m3,
            "stage4_metrics": m4,
            "stage5_metrics": m5,
            "stage6_manifest": m6
        }

        logger.info("=================================================================")
        logger.info("MODULE 1 EXECUTION FINISHED WITH STATUS: SUCCESS")
        logger.info("=================================================================")
        return summary
