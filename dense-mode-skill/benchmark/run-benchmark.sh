#!/usr/bin/env bash
set -euo pipefail

# Dense Mode vs Caveman Benchmark
# Runs 6 prompts through 3 configs (baseline, caveman, dense) via claude CLI
# Measures real API token counts from --output-format json

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL="${MODEL:-sonnet}"
TRIALS="${TRIALS:-1}"
SLEEP="${SLEEP:-2}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
RESULTS_DIR="$SCRIPT_DIR/results/run-$TIMESTAMP"

# Paths
PROMPTS_FILE="$SCRIPT_DIR/prompts.json"
CAVEMAN_SKILL="$SCRIPT_DIR/skills/caveman.md"
DENSE_SKILL="$SCRIPT_DIR/skills/dense.md"

# Validate prerequisites
command -v claude >/dev/null 2>&1 || { echo "Error: claude CLI not found"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "Error: jq not found"; exit 1; }
[ -f "$PROMPTS_FILE" ] || { echo "Error: prompts.json not found"; exit 1; }
[ -f "$CAVEMAN_SKILL" ] || { echo "Error: skills/caveman.md not found"; exit 1; }
[ -f "$DENSE_SKILL" ] || { echo "Error: skills/dense.md not found"; exit 1; }

# Create results directories
mkdir -p "$RESULTS_DIR/raw" "$RESULTS_DIR/responses"

echo "=== Dense Mode vs Caveman Benchmark ==="
echo "Model: $MODEL | Trials: $TRIALS | Sleep: ${SLEEP}s"
echo "Results: $RESULTS_DIR"
echo ""

# Common flags for controlled experiment
COMMON_FLAGS=(
  -p
  --output-format json
  --tools ""
  --disable-slash-commands
  --no-session-persistence
  --model "$MODEL"
)

PROMPT_COUNT=$(jq '.prompts | length' "$PROMPTS_FILE")
CONFIGS=("baseline" "caveman" "dense")
TOTAL_RUNS=$((PROMPT_COUNT * ${#CONFIGS[@]} * TRIALS))
RUN_NUM=0

for trial in $(seq 1 "$TRIALS"); do
  for i in $(seq 0 $((PROMPT_COUNT - 1))); do
    PROMPT_ID=$(jq -r ".prompts[$i].id" "$PROMPTS_FILE")
    PROMPT_TYPE=$(jq -r ".prompts[$i].type" "$PROMPTS_FILE")
    PROMPT_TEXT=$(jq -r ".prompts[$i].prompt" "$PROMPTS_FILE")

    for config in "${CONFIGS[@]}"; do
      RUN_NUM=$((RUN_NUM + 1))
      SUFFIX=""
      [ "$TRIALS" -gt 1 ] && SUFFIX="-t${trial}"
      OUTPUT_FILE="$RESULTS_DIR/raw/${config}-${PROMPT_ID}${SUFFIX}.json"

      echo "[$RUN_NUM/$TOTAL_RUNS] $config | $PROMPT_ID ($PROMPT_TYPE)..."

      # Build command
      CMD=(claude "${COMMON_FLAGS[@]}")
      case "$config" in
        caveman) CMD+=(--append-system-prompt-file "$CAVEMAN_SKILL") ;;
        dense)   CMD+=(--append-system-prompt-file "$DENSE_SKILL") ;;
      esac
      CMD+=("$PROMPT_TEXT")

      # Run and capture
      if "${CMD[@]}" > "$OUTPUT_FILE" 2>/dev/null; then
        OUT_TOKENS=$(jq '.usage.output_tokens // 0' "$OUTPUT_FILE")
        echo "  -> ${OUT_TOKENS} output tokens"

        # Save response text separately for review
        jq -r '.result // empty' "$OUTPUT_FILE" > "$RESULTS_DIR/responses/${config}-${PROMPT_ID}${SUFFIX}.txt"
      else
        echo "  -> FAILED"
        echo '{"error": true}' > "$OUTPUT_FILE"
      fi

      sleep "$SLEEP"
    done
  done
done

echo ""
echo "=== Generating Summary ==="

# Build summary
SUMMARY="$RESULTS_DIR/summary.md"
cat > "$SUMMARY" << 'HEADER'
# Benchmark Results: Dense Mode vs Caveman

HEADER

echo "**Date:** $(date +%Y-%m-%d)" >> "$SUMMARY"
echo "**Model:** $MODEL" >> "$SUMMARY"
echo "**Trials:** $TRIALS" >> "$SUMMARY"
echo "" >> "$SUMMARY"

# Output token comparison table
echo "## Output Tokens" >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "| Prompt | Type | Baseline | Caveman | Dense | Cave % | Dense % |" >> "$SUMMARY"
echo "|--------|------|----------|---------|-------|--------|---------|" >> "$SUMMARY"

TOTAL_BASELINE=0
TOTAL_CAVEMAN=0
TOTAL_DENSE=0
PROMPT_COUNT_INT=$((PROMPT_COUNT))

for i in $(seq 0 $((PROMPT_COUNT - 1))); do
  PROMPT_ID=$(jq -r ".prompts[$i].id" "$PROMPTS_FILE")
  PROMPT_TYPE=$(jq -r ".prompts[$i].type" "$PROMPTS_FILE")

  # For multiple trials, take the median; for single trial, just read the value
  if [ "$TRIALS" -eq 1 ]; then
    B=$(jq '.usage.output_tokens // 0' "$RESULTS_DIR/raw/baseline-${PROMPT_ID}.json")
    C=$(jq '.usage.output_tokens // 0' "$RESULTS_DIR/raw/caveman-${PROMPT_ID}.json")
    D=$(jq '.usage.output_tokens // 0' "$RESULTS_DIR/raw/dense-${PROMPT_ID}.json")
  else
    # Median of trials
    B=$(for t in $(seq 1 "$TRIALS"); do jq '.usage.output_tokens // 0' "$RESULTS_DIR/raw/baseline-${PROMPT_ID}-t${t}.json"; done | sort -n | sed -n "$((( TRIALS + 1 ) / 2))p")
    C=$(for t in $(seq 1 "$TRIALS"); do jq '.usage.output_tokens // 0' "$RESULTS_DIR/raw/caveman-${PROMPT_ID}-t${t}.json"; done | sort -n | sed -n "$((( TRIALS + 1 ) / 2))p")
    D=$(for t in $(seq 1 "$TRIALS"); do jq '.usage.output_tokens // 0' "$RESULTS_DIR/raw/dense-${PROMPT_ID}-t${t}.json"; done | sort -n | sed -n "$((( TRIALS + 1 ) / 2))p")
  fi

  TOTAL_BASELINE=$((TOTAL_BASELINE + B))
  TOTAL_CAVEMAN=$((TOTAL_CAVEMAN + C))
  TOTAL_DENSE=$((TOTAL_DENSE + D))

  # Calculate reduction percentages
  if [ "$B" -gt 0 ]; then
    CAVE_PCT=$(echo "scale=0; (($B - $C) * 100) / $B" | bc)
    DENSE_PCT=$(echo "scale=0; (($B - $D) * 100) / $B" | bc)
  else
    CAVE_PCT=0
    DENSE_PCT=0
  fi

  echo "| $PROMPT_ID | $PROMPT_TYPE | $B | $C | $D | ${CAVE_PCT}% | ${DENSE_PCT}% |" >> "$SUMMARY"
done

# Averages
AVG_B=$((TOTAL_BASELINE / PROMPT_COUNT_INT))
AVG_C=$((TOTAL_CAVEMAN / PROMPT_COUNT_INT))
AVG_D=$((TOTAL_DENSE / PROMPT_COUNT_INT))
AVG_CAVE_PCT=$(echo "scale=0; (($TOTAL_BASELINE - $TOTAL_CAVEMAN) * 100) / $TOTAL_BASELINE" | bc)
AVG_DENSE_PCT=$(echo "scale=0; (($TOTAL_BASELINE - $TOTAL_DENSE) * 100) / $TOTAL_BASELINE" | bc)

echo "| **Average** | | **$AVG_B** | **$AVG_C** | **$AVG_D** | **${AVG_CAVE_PCT}%** | **${AVG_DENSE_PCT}%** |" >> "$SUMMARY"

# Cost comparison
echo "" >> "$SUMMARY"
echo "## Cost" >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "| Config | Total Output Tokens | Total Cost (USD) |" >> "$SUMMARY"
echo "|--------|--------------------:|------------------:|" >> "$SUMMARY"

for config in "${CONFIGS[@]}"; do
  TOTAL_COST=0
  TOTAL_OUT=0
  for i in $(seq 0 $((PROMPT_COUNT - 1))); do
    PROMPT_ID=$(jq -r ".prompts[$i].id" "$PROMPTS_FILE")
    if [ "$TRIALS" -eq 1 ]; then
      FILE="$RESULTS_DIR/raw/${config}-${PROMPT_ID}.json"
    else
      FILE="$RESULTS_DIR/raw/${config}-${PROMPT_ID}-t1.json"
    fi
    COST=$(jq '.total_cost_usd // 0' "$FILE")
    OUT=$(jq '.usage.output_tokens // 0' "$FILE")
    TOTAL_COST=$(echo "$TOTAL_COST + $COST" | bc)
    TOTAL_OUT=$((TOTAL_OUT + OUT))
  done
  echo "| $config | $TOTAL_OUT | \$$(printf '%.4f' "$TOTAL_COST") |" >> "$SUMMARY"
done

# Input token sanity check
echo "" >> "$SUMMARY"
echo "## Input Token Sanity Check" >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "Input tokens should be roughly equal across configs for the same prompt (confirms controlled experiment)." >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "| Prompt | Baseline Input | Caveman Input | Dense Input |" >> "$SUMMARY"
echo "|--------|---------------:|--------------:|------------:|" >> "$SUMMARY"

for i in $(seq 0 $((PROMPT_COUNT - 1))); do
  PROMPT_ID=$(jq -r ".prompts[$i].id" "$PROMPTS_FILE")
  if [ "$TRIALS" -eq 1 ]; then
    BI=$(jq '(.usage.input_tokens // 0) + (.usage.cache_creation_input_tokens // 0) + (.usage.cache_read_input_tokens // 0)' "$RESULTS_DIR/raw/baseline-${PROMPT_ID}.json")
    CI=$(jq '(.usage.input_tokens // 0) + (.usage.cache_creation_input_tokens // 0) + (.usage.cache_read_input_tokens // 0)' "$RESULTS_DIR/raw/caveman-${PROMPT_ID}.json")
    DI=$(jq '(.usage.input_tokens // 0) + (.usage.cache_creation_input_tokens // 0) + (.usage.cache_read_input_tokens // 0)' "$RESULTS_DIR/raw/dense-${PROMPT_ID}.json")
  else
    BI=$(jq '(.usage.input_tokens // 0) + (.usage.cache_creation_input_tokens // 0) + (.usage.cache_read_input_tokens // 0)' "$RESULTS_DIR/raw/baseline-${PROMPT_ID}-t1.json")
    CI=$(jq '(.usage.input_tokens // 0) + (.usage.cache_creation_input_tokens // 0) + (.usage.cache_read_input_tokens // 0)' "$RESULTS_DIR/raw/caveman-${PROMPT_ID}-t1.json")
    DI=$(jq '(.usage.input_tokens // 0) + (.usage.cache_creation_input_tokens // 0) + (.usage.cache_read_input_tokens // 0)' "$RESULTS_DIR/raw/dense-${PROMPT_ID}-t1.json")
  fi
  echo "| $PROMPT_ID | $BI | $CI | $DI |" >> "$SUMMARY"
done

# Context compounding projection
echo "" >> "$SUMMARY"
echo "## 30-Turn Session Projection" >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "Each response persists in context for all subsequent turns. Cumulative cost = avg_tokens × sum(1..30) = avg × 465" >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "| Config | Avg Output/Turn | 30-Turn Cumulative | Savings vs Baseline |" >> "$SUMMARY"
echo "|--------|----------------:|-------------------:|--------------------:|" >> "$SUMMARY"

B_CUM=$((AVG_B * 465))
C_CUM=$((AVG_C * 465))
D_CUM=$((AVG_D * 465))
C_SAVE=$((B_CUM - C_CUM))
D_SAVE=$((B_CUM - D_CUM))

echo "| baseline | $AVG_B | $B_CUM | — |" >> "$SUMMARY"
echo "| caveman | $AVG_C | $C_CUM | $C_SAVE tokens |" >> "$SUMMARY"
echo "| dense | $AVG_D | $D_CUM | $D_SAVE tokens |" >> "$SUMMARY"

echo "" >> "$SUMMARY"
echo "---" >> "$SUMMARY"
echo "*Generated by run-benchmark.sh on $(date)*" >> "$SUMMARY"

echo ""
echo "=== Done ==="
echo "Summary: $SUMMARY"
echo "Raw data: $RESULTS_DIR/raw/"
echo "Responses: $RESULTS_DIR/responses/"
