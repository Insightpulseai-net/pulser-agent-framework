#!/usr/bin/env python3
"""
GENERATED FILE - DO NOT EDIT MANUALLY
Source: docs-to-code-pipeline Model Factory
Generated: 2026-01-01T00:00:00Z
Regenerate: Managed by repository template

Model Evaluation Pipeline Step
------------------------------
Wrapper for running model evaluation as a pipeline step.

Usage:
    python pipelines/model/30_eval.py --run-id run_001
"""

import argparse
import logging
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_evaluation(run_id: str):
    """Run evaluation harness for a training run."""
    model_path = f"runs/{run_id}"
    output_dir = f"evals/{run_id}"

    logger.info(f"Running evaluation for run: {run_id}")

    cmd = [
        sys.executable,
        "ml/eval/harness/run.py",
        "--run-id", run_id,
        "--model-path", model_path,
        "--output-dir", output_dir,
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"Evaluation failed: {e}")
        logger.error(e.stderr)
        sys.exit(1)

    logger.info("Evaluation complete!")


def main():
    parser = argparse.ArgumentParser(description="Model Evaluation Pipeline Step")
    parser.add_argument("--run-id", required=True, help="Training run ID")

    args = parser.parse_args()
    run_evaluation(args.run_id)


if __name__ == "__main__":
    main()
