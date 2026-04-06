#!/bin/bash
# Statusbar capture hook for Claude Code
# Logs the full statusbar JSON payload to a per-session JSONL file
# AND displays a compact status line in the terminal.
#
# Install: Add to Claude Code settings.json:
#   { "statusLine": { "type": "command", "command": "/Users/pili/tokens-experiment/scripts/capture_statusbar.sh" } }
#
# Data written to: $TOKENS_EXPERIMENT_DIR/data/raw/statusbar/<session_id>.jsonl
# Each line is a complete JSON payload received after an assistant message.

set -euo pipefail

# Read JSON from stdin (Claude Code pipes statusbar payload)
input=$(cat)

# Determine output directory
TOKENS_EXPERIMENT_DIR="${TOKENS_EXPERIMENT_DIR:-$HOME/tokens-experiment}"
LOGDIR="$TOKENS_EXPERIMENT_DIR/data/raw/statusbar"
mkdir -p "$LOGDIR"

# Extract session ID for per-session log file
SESSION_ID=$(echo "$input" | jq -r '.session_id // "unknown"')
LOGFILE="$LOGDIR/${SESSION_ID}.jsonl"

# Append timestamped payload (add capture_timestamp for our records)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$input" | jq -c --arg ts "$TIMESTAMP" '. + {capture_timestamp: $ts}' >> "$LOGFILE"

# Display compact status line
MODEL=$(echo "$input" | jq -r '.model.display_name // "?"')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
COST_FMT=$(printf '$%.4f' "$COST")
INPUT_TOKENS=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // "?"')
OUTPUT_TOKENS=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // "?"')

echo "[$MODEL] ${PCT}% ctx | in:${INPUT_TOKENS} out:${OUTPUT_TOKENS} | $COST_FMT"
