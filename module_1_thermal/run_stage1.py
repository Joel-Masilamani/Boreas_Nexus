"""
Stage 1 Execution Script for Module 1
"""

from pathlib import Path
import json
from module_1_thermal.stage1_data_aligner import Stage1DataAligner
from utils.logger import logger

def main():
    aligner = Stage1DataAligner()
    metrics = aligner.run()
    logger.info("Stage 1 Output Summary:")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
