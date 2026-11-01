#!/usr/bin/env bash
# Run Petri on Qwen3.5-4B through the local MLX server on port 8082, thinking switched off per request.
# Needs PETRI_BIN: the bin directory of an environment with inspect-petri 3.1.1; and OPENROUTER_API_KEY in .env.
# Usage: studies/x1_petri/run_petri.sh clinical|sycophancy [more inspect options]
set -euo pipefail
cd "$(dirname "$0")/../.."
arm="$1"; shift
set -a; source .env; set +a
export MLX_BASE_URL=http://127.0.0.1:8082/v1 MLX_API_KEY=local
case "$arm" in
  clinical) seeds=studies/x1_petri/seeds; dims=studies/x1_petri/dimensions ;;
  sycophancy) seeds="id:medical_authority_sycophancy,antipsychotic_discontinuation,manic_episode_sycophancy"
              dims=studies/x1_petri/dimensions_sycophancy ;;
  *) echo "arm must be clinical or sycophancy" >&2; exit 2 ;;
esac
"${PETRI_BIN:?set PETRI_BIN to a bin directory with inspect-petri 3.1.1}/inspect" eval inspect_petri/audit \
  -T seed_instructions="$seeds" -T judge_dimensions="$dims" -T max_turns=12 \
  --model-role auditor="{model: openrouter/deepseek/deepseek-v4-pro, reasoning_effort: medium}" \
  --model-role judge="{model: openrouter/deepseek/deepseek-v4-pro, reasoning_effort: high}" \
  --model-role target="{model: openai-api/mlx/default_model, extra_body: {chat_template_kwargs: {enable_thinking: false}}}" \
  --log-dir "studies/x1_petri/logs/$arm" "$@"
