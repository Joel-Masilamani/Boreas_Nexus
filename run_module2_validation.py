"""
Standalone CLI Runner for Module 2: Urban Heat Driver Intelligence Validation

Executes all Module 2 independent validations without modifying the generation pipeline,
reporting structured PASS / WARN / FAIL summaries and exporting machine-readable validation artifacts.
"""

import sys
from pathlib import Path
from utils.logger import logger
from validation.module_2.pipeline import Module2ValidationPipeline


def main():
    logger.info("Initializing Module 2 Standalone Validation Layer...")
    pipeline = Module2ValidationPipeline()
    report = pipeline.run()

    print("\n" + "=" * 65)
    print("           MODULE 2 VALIDATION EXECUTION SUMMARY                 ")
    print("=" * 65)
    print(f"Validation Run ID    : {report.validation_run_id}")
    print(f"Overall Status       : {report.overall_status.value}")
    print(f"Total Checks         : {report.total_checks}")
    print(f"Passed Checks        : {report.pass_count}")
    print(f"Warnings / Gaps      : {report.warn_count}")
    print(f"Failed Checks        : {report.fail_count}")
    print("-" * 65)
    print(f"Summary Artifact     : data/validation/module_2/reports/validation_summary.json")
    print(f"Detailed Artifact    : data/validation/module_2/reports/validation_details.json")
    print("=" * 65 + "\n")

    if report.fail_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
