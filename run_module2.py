"""
Boreas-Nexus Module 2 Main Execution Entry Point
Executes the full Urban Heat Driver Intelligence Pipeline.
"""

import json
from pathlib import Path
from module_2_driver.pipeline import Module2DriverPipeline
from utils.logger import logger


def main():
    pipeline = Module2DriverPipeline()
    summary = pipeline.run()
    logger.info("Module 2 Execution Summary:")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
