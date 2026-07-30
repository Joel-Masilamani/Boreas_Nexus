"""
Boreas-Nexus CLI Entry Point for Phase 2 Preprocessing Pipeline

Executes spatial grid generation, vector proximity calculation, spectral index computation,
and exports the dataset to data/processed/features.parquet and features.geojson.

Usage:
    python run_preprocessing.py --config config/city.yaml
"""

import argparse
import sys
from pathlib import Path
from preprocessing.preprocessor_pipeline import PreprocessorPipeline
from utils.logger import logger


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Boreas-Nexus: Phase 2 Feature Preprocessing Pipeline"
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
        pipeline = PreprocessorPipeline(config_path=config_file)
        summary = pipeline.run()
        print("\n--- PREPROCESSING SUMMARY ---")
        print(f"City: {summary['city']}")
        print(f"Status: {summary['status']}")
        print(f"Grid Resolution: {summary['grid_resolution_meters']} meters")
        print(f"Samples Extracted: {summary['sample_count']}")
        print(f"Parquet Dataset: {summary['parquet_output']}")
        print(f"GeoJSON Dataset: {summary['geojson_output']}")
        print(f"Features Generated ({len(summary['feature_columns'])}): {', '.join(summary['feature_columns'])}")
    except Exception as e:
        logger.critical(f"Fatal preprocessing error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
