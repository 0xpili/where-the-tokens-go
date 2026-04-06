# Statusbar Capture Hook Installation

## Configuration

Add the following to your Claude Code `settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "/Users/pili/tokens-experiment/scripts/capture_statusbar.sh"
  }
}
```

The settings file is typically located at `~/.claude/settings.json`.

## Custom Data Directory

By default, captured data is written to `~/tokens-experiment/data/raw/statusbar/`.
Override this by setting the `TOKENS_EXPERIMENT_DIR` environment variable:

```bash
export TOKENS_EXPERIMENT_DIR="/path/to/your/tokens-experiment"
```

## Verification

1. Start a Claude Code session
2. Send any message (e.g., "Hello")
3. Check for a `.jsonl` file in `data/raw/statusbar/`:

```bash
ls -la ~/tokens-experiment/data/raw/statusbar/
```

4. Each file is named `<session_id>.jsonl` and contains one JSON object per assistant message turn.

## What Gets Captured

Each line in the JSONL file contains the full statusbar JSON payload with an added `capture_timestamp` field:
- `session_id` -- unique session identifier
- `model` -- model info (id, display name)
- `context_window` -- current usage breakdown (input/output/cache tokens, percentage used)
- `cost` -- running session cost in USD
- `rate_limits` -- 5-hour and 7-day usage percentages
- `capture_timestamp` -- UTC ISO timestamp when the capture occurred
