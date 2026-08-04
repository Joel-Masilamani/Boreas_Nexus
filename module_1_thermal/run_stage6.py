"""
Stage 6 Execution Script for Module 1
"""

from pathlib import Path
import json
from module_1_thermal.stage6_knowledge_export import Stage6KnowledgeExporter
from utils.logger import logger

def main():
    exporter = Stage6KnowledgeExporter()
    manifest = exporter.run()
    logger.info("Stage 6 Knowledge Layer Manifest:")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
