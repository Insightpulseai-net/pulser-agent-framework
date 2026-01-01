#!/usr/bin/env python3
"""
GENERATED FILE - DO NOT EDIT MANUALLY
Source: docs-to-code-pipeline Model Factory
Generated: 2026-01-01T00:00:00Z
Regenerate: Managed by repository template

Smoke Test for Model Releases
-----------------------------
Quick validation that a model can load and generate.

Usage:
    python ml/eval/harness/smoke.py --tag v0.1.0 --model-path release/v0.1.0

"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_smoke_test(tag: str, model_path: str) -> bool:
    """Run smoke test on model release."""
    logger.info(f"Running smoke test for release: {tag}")
    logger.info(f"Model path: {model_path}")

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        # Test 1: Load tokenizer
        logger.info("Test 1: Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        logger.info(f"  Tokenizer loaded: {tokenizer.__class__.__name__}")

        # Test 2: Load model
        logger.info("Test 2: Loading model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype="auto",
        )
        logger.info(f"  Model loaded: {model.__class__.__name__}")
        logger.info(f"  Parameters: {model.num_parameters():,}")

        # Test 3: Generate text
        logger.info("Test 3: Generating text...")
        test_prompt = "Hello, I am a"
        inputs = tokenizer(test_prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=20,
            pad_token_id=tokenizer.eos_token_id,
        )
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"  Input: {test_prompt}")
        logger.info(f"  Output: {generated}")

        # Test 4: Verify output is different from input
        if len(generated) > len(test_prompt):
            logger.info("  Generation successful!")
        else:
            logger.warning("  Warning: No new tokens generated")

        logger.info("")
        logger.info("=" * 50)
        logger.info("SMOKE TEST PASSED")
        logger.info("=" * 50)

        return True

    except Exception as e:
        logger.error(f"SMOKE TEST FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Model Release Smoke Test")
    parser.add_argument("--tag", required=True, help="Release tag (e.g., v0.1.0)")
    parser.add_argument("--model-path", required=True, help="Path to model")

    args = parser.parse_args()

    success = run_smoke_test(args.tag, args.model_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
