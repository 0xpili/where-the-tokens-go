# Measurement Source Hierarchy

Per decisions D-01, D-02, D-03, D-05 from the project context.

## Source Hierarchy (most accurate first)

| Priority | Source | Type | Accuracy | Use Case |
|----------|--------|------|----------|----------|
| 1 | **Statusbar JSON** | Per-turn, session-level | HIGH -- receives finalized totals | Primary measurement for real Claude Code sessions (D-01) |
| 2 | **count_tokens API** | Component-level | HIGH -- slight variance possible | Isolating system prompt, tool schemas, individual components (D-02) |
| 3 | **/cost command** | Session-level summary | HIGH -- matches billing | Validation checkpoint during live sessions (MEAS-05) |
| 4 | **/context command** | Context window breakdown | HIGH -- per-component view | Validation of component breakdown during live sessions (MEAS-05) |
| 5 | **ccusage** | Session aggregation | LOW for absolute, OK for relative | Relative session comparisons only (D-03) |
| 6 | **JSONL session logs** | Per-message raw data | VERY LOW -- 100-174x undercount | Never for absolute claims; reference only |

## When to Use Each Source

### Statusbar JSON (primary)
- **What:** Full JSON payload captured after each assistant message via hook script
- **When:** Any real Claude Code session where you need per-turn token tracking
- **Provides:** input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens, session cost, context usage percentage
- **Script:** `scripts/capture_statusbar.sh`

### count_tokens API (component isolation)
- **What:** Anthropic's POST /v1/messages/count_tokens endpoint via Python SDK
- **When:** Measuring the token cost of specific payload components (system prompts, tool definitions, messages)
- **Provides:** Exact input token count for a constructed message payload
- **Script:** `scripts/count_tokens.py`
- **Note:** Counts are estimates that "may differ slightly from actual billing" per Anthropic docs. May include system optimization tokens that are NOT billed but ARE counted.

### /cost command (validation)
- **What:** Built-in Claude Code command showing session cost summary
- **When:** Quick validation during live experiment sessions
- **Provides:** Total cost, total duration, token usage summary
- **Note:** Use to cross-reference against statusbar captures for first few sessions

### /context command (validation)
- **What:** Built-in Claude Code command showing context window breakdown
- **When:** Validating component breakdown and monitoring compaction
- **Provides:** Per-component token counts (system prompt, tools, MCP, memory, conversation)
- **Note:** Shows breakdown that matches what the API sees

### ccusage (relative only)
- **What:** CLI tool that reads JSONL session logs and aggregates by session/day/month
- **When:** Comparing relative usage between sessions (session A vs session B)
- **Script:** `scripts/validate_ccusage.sh`
- **CRITICAL CAVEATS:**
  - Reads JSONL logs which undercount input tokens by 100-174x
  - 75% of JSONL input_tokens entries are 0 or 1 (streaming placeholders)
  - Thinking tokens excluded entirely
  - Use ONLY for relative comparisons, NEVER for absolute claims

### JSONL Session Logs (reference only)
- **What:** Raw per-message logs at `~/.claude/projects/<hash>/sessions/*.jsonl`
- **When:** Never for token counts; useful for message content, timing, session structure
- **CRITICAL:** input_tokens field is a streaming placeholder, NOT actual token count

## Known Accuracy Issues

1. **JSONL undercount (100-174x):** Session logs record streaming placeholders for input_tokens. A session reporting 225K via ccusage may actually be 10.4M tokens.

2. **count_tokens variance:** The API may return slightly different counts for identical payloads (small variance). Always measure multiple times per D-07 and report mean/min/max.

3. **Cache TTL effects (5-minute eviction):** Prompt cache evicts after 5 minutes of inactivity. cache_creation vs cache_read tokens shift based on session continuity. Document pauses as experimental variables.

4. **System optimization tokens:** count_tokens may include tokens added by Anthropic for internal optimization. These are counted but NOT billed. This means count_tokens >= actual billed input.

5. **Thinking token invisibility:** Extended thinking tokens (~32K default budget) are billed as output but invisible in terminal. Verify statusbar includes them.

## Cross-Validation Procedure

For the first few measurement sessions:

1. Capture statusbar JSON via hook script
2. At session end, run `/cost` and record output
3. Compare statusbar `context_window.total_input_tokens` with /cost input token total
4. If discrepancy > 5%, investigate which source is more accurate
5. Document the comparison in the experiment notes

This procedure establishes trust in the primary measurement source (statusbar JSON) before running experiments that depend on it.
