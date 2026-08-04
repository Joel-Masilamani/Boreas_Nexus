"""
Stage 4 Execution Script for Module 1
"""

from pathlib import Path
import json
from module_1_thermal.stage4_nighttime_thermal import Stage4NighttimeThermal
from utils.logger import logger

def main():
    analyzer = Stage4NighttimeThermal()
    metrics = analyzer.run()
    logger.info("Stage 4 Output Summary:")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
