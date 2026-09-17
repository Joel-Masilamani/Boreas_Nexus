"""
Boreas-Nexus Module 1 Main Entry Point
Executes the full Module 1 Physical Urban Heat & Hotspot Intelligence Engine.
"""

from pathlib import Path
import json
from module_1_thermal.pipeline import Module1ThermalPipeline
from utils.logger import logger

def main():
    pipeline = Module1ThermalPipeline()
    summary = pipeline.run()
    logger.info("Module 1 Execution Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
