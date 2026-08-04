"""
Stage 3 Execution Script for Module 1
"""

from pathlib import Path
import json
from module_1_thermal.stage3_suhii_calculator import Stage3SUHIICalculator
from utils.logger import logger

def main():
    calculator = Stage3SUHIICalculator()
    metrics = calculator.run()
    logger.info("Stage 3 Output Summary:")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
