"""
Boreas-Nexus Module 1 Validation CLI Runner

Executes the standalone validation layer on Module 1 outputs and displays the execution summary.
"""

import sys
from validation.module_1.pipeline import Module1ValidationPipeline
from utils.logger import logger


def main():
    logger.info("Initializing Module 1 Standalone Validation Layer...")
    pipeline = Module1ValidationPipeline()
    report = pipeline.run()

    print("\n=================================================================")
    print("           MODULE 1 VALIDATION EXECUTION SUMMARY                 ")
    print("=================================================================")
    print(f"Validation Run ID    : {report.validation_run_id}")
    print(f"Overall Status       : {report.overall_status.value}")
    print(f"Total Checks         : {report.total_checks}")
    print(f"Passed Checks        : {report.pass_count}")
    print(f"Warnings             : {report.warn_count}")
    print(f"Failed Checks        : {report.fail_count}")
    print("-----------------------------------------------------------------")
    print(f"Summary Artifact     : data/validation/module_1/reports/validation_summary.json")
    print(f"Detailed Artifact    : data/validation/module_1/reports/validation_details.json")
    print("=================================================================\n")

    if report.fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
