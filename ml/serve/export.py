#!/usr/bin/env python3
"""
GENERATED FILE - DO NOT EDIT MANUALLY
Source: docs-to-code-pipeline Model Factory
Generated: 2026-01-01T00:00:00Z
Regenerate: Managed by repository template

Model Export for Release
------------------------
Merges adapters, applies quantization, and packages for release.

Usage:
    python ml/serve/export.py --run-id run_001 --tag v0.1.0 --output-dir release/v0.1.0

"""

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def merge_lora_adapters(model_path: str, output_path: str):
    """Merge LoRA adapters into base model."""
    try:
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        logger.info("Merging LoRA adapters...")

        # Load base model
        base_model_path = Path(model_path) / "config.json"
        if base_model_path.exists():
            with open(base_model_path) as f:
                config = json.load(f)
            base_model_name = config.get("_name_or_path", model_path)
        else:
            base_model_name = model_path

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)

        # Load base model
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype="auto",
            device_map="auto",
        )

        # Load and merge LoRA
        model = PeftModel.from_pretrained(model, model_path)
        model = model.merge_and_unload()

        # Save merged model
        model.save_pretrained(output_path, safe_serialization=True)
        tokenizer.save_pretrained(output_path)

        logger.info(f"Merged model saved to {output_path}")

    except Exception as e:
        logger.warning(f"Could not merge adapters (may not be LoRA): {e}")
        # Copy as-is if not LoRA
        shutil.copytree(model_path, output_path, dirs_exist_ok=True)


def apply_quantization(model_path: str, output_path: str, quant_type: str):
    """Apply quantization to model."""
    if quant_type == "none":
        logger.info("No quantization requested")
        return

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        logger.info(f"Applying {quant_type} quantization...")

        tokenizer = AutoTokenizer.from_pretrained(model_path)

        if quant_type == "8bit":
            from transformers import BitsAndBytesConfig

            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        elif quant_type == "4bit":
            from transformers import BitsAndBytesConfig

            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype="float16",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
        else:
            logger.warning(f"Unknown quantization type: {quant_type}")
            return

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            device_map="auto",
        )

        model.save_pretrained(output_path, safe_serialization=True)
        tokenizer.save_pretrained(output_path)

        logger.info(f"Quantized model saved to {output_path}")

    except Exception as e:
        logger.error(f"Quantization failed: {e}")
        raise


def create_release_metadata(
    run_id: str, tag: str, output_path: str, quantize: str
):
    """Create release metadata file."""
    metadata = {
        "run_id": run_id,
        "release_tag": tag,
        "quantization": quantize,
        "released_at": datetime.utcnow().isoformat(),
        "release_type": "model",
    }

    metadata_file = Path(output_path) / "release_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Release metadata saved to {metadata_file}")


def main():
    parser = argparse.ArgumentParser(description="Model Export for Release")
    parser.add_argument("--run-id", required=True, help="Training run ID")
    parser.add_argument("--tag", required=True, help="Release tag")
    parser.add_argument(
        "--quantize",
        choices=["none", "4bit", "8bit"],
        default="none",
        help="Quantization type",
    )
    parser.add_argument("--output-dir", required=True, help="Output directory")

    args = parser.parse_args()

    model_path = f"runs/{args.run_id}"
    output_path = args.output_dir

    logger.info(f"Exporting model for release: {args.tag}")
    logger.info(f"Source: {model_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Quantization: {args.quantize}")

    # Create output directory
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # Merge adapters if LoRA
    merge_lora_adapters(model_path, output_path)

    # Apply quantization if requested
    if args.quantize != "none":
        apply_quantization(output_path, output_path, args.quantize)

    # Create release metadata
    create_release_metadata(args.run_id, args.tag, output_path, args.quantize)

    logger.info("Export complete!")


if __name__ == "__main__":
    main()
