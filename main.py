"""
Boreas-Nexus CLI Entry Point

Main command line interface to execute Phase 1 Data Ingestion Pipeline.
Usage:
    python main.py --config config/city.yaml
"""

import argparse
import sys
from pathlib import Path
from orchestrator.ingestion_pipeline import IngestionPipeline
from utils.logger import logger


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Boreas-Nexus: Urban Heat Island Data Ingestion Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/city.yaml",
        help="Path to city configuration YAML file (default: config/city.yaml)"
    )

    args = parser.parse_args()
    config_file = Path(args.config)

    if not config_file.exists():
        logger.error(f"Configuration file not found: {config_file.resolve()}")
        sys.exit(1)

    try:
        pipeline = IngestionPipeline(config_path=config_file)
        summary = pipeline.run()
        print("\n--- INGESTION SUMMARY ---")
        print(f"City: {summary['city']}")
        print(f"Status: {summary['status']}")
        print(f"Execution Time: {summary['execution_time_seconds']} seconds")
        print(f"Boundary: {summary['boundary']}")
        print(f"Weather: {summary['weather_file']}")
        print(f"Elevation: {summary['elevation_file']}")
        print(f"Vector Layers Ingested: {len(summary['vector_layers'])}")
        print(f"Satellite Files Ingested: {len(summary['satellite_files'])}")
        if summary["errors"]:
            print(f"Encountered {len(summary['errors'])} non-fatal warnings/errors:")
            for err in summary["errors"]:
                print(f" - {err}")
    except Exception as e:
        logger.critical(f"Fatal pipeline error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
