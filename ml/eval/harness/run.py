#!/usr/bin/env python3
"""
GENERATED FILE - DO NOT EDIT MANUALLY
Source: docs-to-code-pipeline Model Factory
Generated: 2026-01-01T00:00:00Z
Regenerate: Managed by repository template

Model Evaluation Harness
------------------------
Evaluates trained models on benchmark tasks.

Usage:
    python ml/eval/harness/run.py --run-id run_001 --model-path runs/run_001

"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def load_model(model_path: str):
    """Load model and tokenizer from path."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype="auto",
        )
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def evaluate_generation(model, tokenizer, test_samples: list) -> dict:
    """Evaluate generation quality on test samples."""
    import torch

    results = []

    for sample in test_samples:
        prompt = sample.get("instruction", sample.get("prompt", ""))
        expected = sample.get("output", sample.get("response", ""))

        # Generate
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated = generated[len(prompt) :].strip()

        results.append(
            {
                "prompt": prompt[:100],
                "expected": expected[:100],
                "generated": generated[:100],
            }
        )

    return {"samples": len(results), "results": results[:5]}  # First 5 samples


def compute_metrics(model, tokenizer, eval_dataset) -> dict:
    """Compute evaluation metrics."""
    try:
        import evaluate
        import numpy as np

        # Load metrics
        rouge = evaluate.load("rouge")
        bleu = evaluate.load("bleu")

        predictions = []
        references = []

        for sample in eval_dataset[:100]:  # Limit for speed
            prompt = sample.get("instruction", "")
            expected = sample.get("output", "")

            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,
                pad_token_id=tokenizer.eos_token_id,
            )
            generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated = generated[len(prompt) :].strip()

            predictions.append(generated)
            references.append(expected)

        # Compute ROUGE
        rouge_results = rouge.compute(
            predictions=predictions, references=references
        )

        # Compute BLEU (requires tokenized references)
        bleu_results = bleu.compute(
            predictions=predictions,
            references=[[r] for r in references],
        )

        return {
            "rouge1": rouge_results.get("rouge1", 0),
            "rouge2": rouge_results.get("rouge2", 0),
            "rougeL": rouge_results.get("rougeL", 0),
            "bleu": bleu_results.get("bleu", 0),
            "samples_evaluated": len(predictions),
        }

    except ImportError as e:
        logger.warning(f"Could not compute metrics: {e}")
        return {"error": str(e)}


def run_evaluation(run_id: str, model_path: str, output_dir: str):
    """Run full evaluation suite."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Running evaluation for: {run_id}")
    logger.info(f"Model path: {model_path}")

    # Load model
    model, tokenizer = load_model(model_path)

    # Load eval dataset (golden test set)
    golden_path = Path("ml/eval/golden/test.jsonl")
    eval_samples = []
    if golden_path.exists():
        import jsonlines

        with jsonlines.open(golden_path) as reader:
            eval_samples = list(reader)
        logger.info(f"Loaded {len(eval_samples)} golden test samples")
    else:
        logger.warning("No golden test set found, using synthetic samples")
        eval_samples = [
            {
                "instruction": "What is 2 + 2?",
                "output": "4",
            },
            {
                "instruction": "Write a Python function to add two numbers.",
                "output": "def add(a, b): return a + b",
            },
        ]

    # Run evaluations
    results = {
        "run_id": run_id,
        "model_path": model_path,
        "evaluated_at": datetime.utcnow().isoformat(),
    }

    # Generation evaluation
    gen_results = evaluate_generation(model, tokenizer, eval_samples[:10])
    results["generation"] = gen_results

    # Metrics
    metrics = compute_metrics(model, tokenizer, eval_samples)
    results["metrics"] = metrics

    # Save results
    results_file = output_path / "eval_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Evaluation complete. Results saved to {results_file}")
    logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Model Evaluation Harness")
    parser.add_argument("--run-id", required=True, help="Training run ID")
    parser.add_argument(
        "--model-path", required=True, help="Path to trained model"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: evals/<run-id>)",
    )

    args = parser.parse_args()

    output_dir = args.output_dir or f"evals/{args.run_id}"

    run_evaluation(args.run_id, args.model_path, output_dir)


if __name__ == "__main__":
    main()
