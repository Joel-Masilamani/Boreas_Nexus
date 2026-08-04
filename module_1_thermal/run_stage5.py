"""
Stage 5 Execution Script for Module 1
"""

from pathlib import Path
import json
from module_1_thermal.stage5_hotspot_validator import Stage5HotspotValidator
from utils.logger import logger

def main():
    validator = Stage5HotspotValidator()
    metrics = validator.run()
    logger.info("Stage 5 Output Summary:")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
