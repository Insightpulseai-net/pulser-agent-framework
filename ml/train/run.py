#!/usr/bin/env python3
"""
GENERATED FILE - DO NOT EDIT MANUALLY
Source: docs-to-code-pipeline Model Factory
Generated: 2026-01-01T00:00:00Z
Regenerate: Managed by repository template

Model Training Entry Point
--------------------------
Unified training script for SFT, LoRA, and DPO training runs.

Usage:
    python ml/train/run.py --config configs/sft_lora_1b.yaml --run-id run_001

"""

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load training configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def compute_config_hash(config: dict) -> str:
    """Compute deterministic hash of config for reproducibility."""
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def setup_training(config: dict, run_id: str, output_dir: str):
    """Setup training environment and logging."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save config for reproducibility
    config_file = output_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Save run metadata
    metadata = {
        "run_id": run_id,
        "config_hash": compute_config_hash(config),
        "started_at": datetime.utcnow().isoformat(),
        "python_version": sys.version,
    }
    metadata_file = output_path / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Run ID: {run_id}")
    logger.info(f"Config hash: {metadata['config_hash']}")
    logger.info(f"Output dir: {output_path}")


def run_sft_training(config: dict, dataset_path: str, output_dir: str):
    """Run supervised fine-tuning."""
    logger.info("Starting SFT training...")

    try:
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            TrainingArguments,
        )
        from trl import SFTTrainer

        # Load model and tokenizer
        model_name = config.get("model_name", "meta-llama/Llama-2-7b-hf")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            load_in_8bit=config.get("load_in_8bit", True),
            device_map="auto",
        )

        # Setup LoRA if configured
        if config.get("use_lora", True):
            lora_config = LoraConfig(
                r=config.get("lora_r", 16),
                lora_alpha=config.get("lora_alpha", 32),
                target_modules=config.get(
                    "target_modules", ["q_proj", "v_proj"]
                ),
                lora_dropout=config.get("lora_dropout", 0.05),
                bias="none",
                task_type="CAUSAL_LM",
            )
            model = get_peft_model(model, lora_config)

        # Load dataset
        dataset = load_dataset("json", data_files=dataset_path, split="train")

        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=config.get("epochs", 3),
            per_device_train_batch_size=config.get("batch_size", 4),
            gradient_accumulation_steps=config.get(
                "gradient_accumulation_steps", 4
            ),
            learning_rate=config.get("learning_rate", 2e-4),
            warmup_ratio=config.get("warmup_ratio", 0.03),
            logging_steps=10,
            save_strategy="epoch",
            fp16=config.get("fp16", True),
            report_to=config.get("report_to", ["tensorboard"]),
        )

        # Create trainer
        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=dataset,
            args=training_args,
            max_seq_length=config.get("max_seq_length", 2048),
        )

        # Train
        trainer.train()

        # Save final model
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)

        logger.info(f"Training complete. Model saved to {output_dir}")

    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.info("Please install: pip install -r ml/train/requirements.txt")
        raise


def main():
    parser = argparse.ArgumentParser(description="Model Training Entry Point")
    parser.add_argument(
        "--config", required=True, help="Path to training config YAML"
    )
    parser.add_argument("--run-id", required=True, help="Unique run identifier")
    parser.add_argument(
        "--dataset", default="data/train.jsonl", help="Path to training dataset"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: runs/<run-id>)",
    )

    args = parser.parse_args()

    # Set output directory
    output_dir = args.output_dir or f"runs/{args.run_id}"

    # Load config
    config = load_config(args.config)

    # Setup training
    setup_training(config, args.run_id, output_dir)

    # Run training based on type
    training_type = config.get("training_type", "sft")

    if training_type == "sft":
        run_sft_training(config, args.dataset, output_dir)
    else:
        logger.error(f"Unknown training type: {training_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()
