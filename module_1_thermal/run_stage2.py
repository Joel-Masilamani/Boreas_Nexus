"""
Stage 2 Execution Script for Module 1
"""

from pathlib import Path
import json
from module_1_thermal.stage2_urban_delineation import Stage2UrbanDelineator
from utils.logger import logger

def main():
    delineator = Stage2UrbanDelineator()
    metrics = delineator.run()
    logger.info("Stage 2 Output Summary:")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
