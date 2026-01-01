"""
Model Training Pipeline
-----------------------
End-to-end pipeline for training, evaluating, and releasing models.

Pipeline stages:
1. 00_ingest_docs.py - Ingest and preprocess source documents
2. 10_make_sft_jsonl.py - Build SFT training datasets
3. 20_train_lora.py - Run LoRA fine-tuning
4. 30_eval.py - Evaluate trained models
5. 40_export_release.py - Package and release models
"""
