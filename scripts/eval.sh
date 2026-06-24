#!/usr/bin/env bash
set -euo pipefail

python harness/run_eval.py \
  --dataset harness/datasets/smoke_cases.jsonl \
  --prompt harness/prompts/translate_ja_ko_v1.md \
  --model "${LITERT_LM_MODEL_NAME:-gemma4-e4b}"
