#!/usr/bin/env bash
set -euo pipefail

python harness/run_eval.py \
  --dataset harness/datasets/smoke_cases.jsonl \
  --prompt harness/prompts/translate_v1.md \
  --model "${OLLAMA_MODEL:-qwen3:14b}"
