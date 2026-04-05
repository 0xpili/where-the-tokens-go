# Phase 1: Measurement Foundation - Research

**Researched:** 2026-04-05
**Domain:** Token counting methodology, Claude Code session instrumentation, system prompt reverse engineering, experiment design
**Confidence:** HIGH

## Summary

Phase 1 builds the measurement instruments that all subsequent experiments depend on. The core challenge is that Claude Code has multiple data sources for token counts with wildly different accuracy -- JSONL session logs undercount by 100-174x, the statusbar JSON payload provides reliable cumulative totals, the count_tokens API gives ground-truth component-level counts, and /cost and /context commands serve as manual validation checkpoints. Getting measurement right in this phase is the single most important task in the entire project.

The phase decomposes into four work areas: (1) setting up the token counting pipeline using count_tokens API for component isolation and statusbar JSON for session-level tracking, (2) measuring baseline overhead by progressively building payloads from empty to full Claude Code configuration, (3) measuring per-tool token costs through controlled single-tool invocations, and (4) establishing the experiment methodology (identical-task replay, session-level totals, documented control variables) plus the DuckDB analysis infrastructure. REV-01 (system prompt mapping) is included here because baseline overhead measurement depends on understanding the component structure.

**Primary recommendation:** Start with environment setup (install anthropic SDK, duckdb, configure statusbar hook), then use the count_tokens API with progressively built payloads to map the system prompt structure, and capture statusbar JSON during real sessions for validation. Never trust JSONL logs for absolute measurements.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Primary measurement for real Claude Code sessions uses statusbar JSON capture + /cost and /context commands -- these are the most accurate sources per research findings
- D-02: Anthropic's count_tokens API used for component-level measurement (isolating system prompt, tool schemas, etc.)
- D-03: ccusage used for session-level aggregation with documented accuracy caveats (JSONL undercount acknowledged)
- D-04: Local tokenizers (@anthropic-ai/tokenizer) used only for relative comparisons, never for absolute claims
- D-05: Full component breakdown required -- system prompt, each built-in tool schema, CLAUDE.md (per level), memory (MEMORY.md), MCP server overhead, environment info each measured separately
- D-06: Baseline measured from a clean session with no conversation history to isolate fixed overhead
- D-07: Multiple measurements taken to establish variance/confidence intervals
- D-08: Before/after experiments use identical task replay -- same coding task executed in separate fresh sessions with different strategies
- D-09: Session-level totals compared (not per-turn, to capture compounding effects)
- D-10: Each experiment documents: task description, session setup, measurement method, raw data, and conclusions
- D-11: Control variables identified and documented for each experiment (model, Claude Code version, MCP servers active, CLAUDE.md content)
- D-12: DuckDB used for cross-session statistical analysis and querying
- D-13: Results also presented in structured markdown tables for report readability
- D-14: Raw measurement data preserved alongside analysis for reproducibility
- D-15: Map complete system prompt structure using count_tokens API with progressively built payloads
- D-16: Document token counts per component and how they change with different configurations (MCP servers, tools, memory)

### Claude's Discretion
- Exact DuckDB schema design for storing measurement data
- Choice of statusbar capture mechanism (hook scripts, manual recording, etc.)
- Specific coding tasks used as experiment benchmarks (should be representative but Claude picks the actual tasks)
- Organization of measurement scripts and data files within the project

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MEAS-01 | Establish reliable token counting using Anthropic's count_tokens API for component-level measurement | count_tokens API documented at POST /v1/messages/count_tokens; accepts system, tools, messages; returns {input_tokens: N}; FREE endpoint; Python SDK: client.messages.count_tokens() |
| MEAS-02 | Capture statusbar JSON payload during real Claude Code sessions for accurate per-turn token tracking | Statusbar JSON payload fully documented in official docs; includes context_window.current_usage with input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens; configured via settings.json statusLine field |
| MEAS-03 | Measure baseline overhead: system prompt, tool schemas, CLAUDE.md, memory, MCP -- from a clean session | Component breakdown available from Piebald-AI repo (v2.1.92); progressive payload building via count_tokens API measures deltas; /context command provides live breakdown |
| MEAS-04 | Measure per-tool token cost (Read, Edit, Bash, Grep, Glob, Write, Agent) with controlled inputs | Each tool schema contributes to the ~11,600 token "system tools" block; individual tool cost = delta from count_tokens with/without that tool in the tools array; tool result tokens measured from statusbar after invocation |
| MEAS-05 | Use /cost and /context commands to validate measurements during live sessions | /cost shows total cost, duration, token usage; /context shows per-component breakdown including system prompt, system tools, MCP tools, memory files; both are built-in and always available |
| MEAS-06 | Set up ccusage for session-level aggregation (with documented accuracy caveats) | ccusage v18.0.10 available via npx; reads JSONL logs directly; CRITICAL CAVEAT: JSONL input_tokens field is a streaming placeholder (75% are 0 or 1), so ccusage undercounts by 100-174x; useful for relative session comparison but not absolute measurement |
| MEAS-07 | Design before/after experiment methodology: identical tasks, different strategies, session-level totals compared | Methodology documented in CONTEXT.md decisions D-08 through D-11; key controls: model, Claude Code version, MCP servers, CLAUDE.md content, cache state (warm/cold); confounding variables: compaction events, subagent spawning, cache TTL (5-min eviction) |
| MEAS-08 | Set up DuckDB for cross-session statistical analysis of token consumption patterns | DuckDB v1.5.1 available for pip install; reads JSONL directly via read_json(); enables SQL aggregation across sessions; schema should capture: session_id, turn_number, timestamp, input_tokens, output_tokens, cache_creation, cache_read, model, experiment_id |
| REV-01 | Map complete system prompt structure with token counts per component | Piebald-AI/claude-code-system-prompts catalogs 110+ prompt strings, 24 tool definitions for v2.1.92; use count_tokens API with progressively built payloads to measure exact deltas; cross-reference with /context command output |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic (Python SDK) | 0.89.0 | count_tokens API calls, programmatic token counting | Official SDK; client.messages.count_tokens() returns exact input token counts for any payload including system prompts, tools, images. FREE endpoint. |
| DuckDB (Python) | 1.5.1 | SQL analysis of session data, cross-session aggregation | Reads JSONL directly with read_json(); powerful aggregation; no server needed; ideal for research analysis |
| jq | 1.7.1 | JSONL parsing, statusbar JSON extraction, experiment scripting | Already installed; essential for parsing Claude Code data formats |
| ccusage | 18.0.10 | Session-level token aggregation (with documented caveats) | Best-in-class CLI for Claude Code usage analysis; reads native JSONL format; session/daily/monthly breakdowns |
| Claude Code CLI | 2.1.92 | Live session measurement via /cost, /context, statusbar | Already installed; the instrument being measured |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| matplotlib | 3.10.3 | Charts for overhead breakdown, comparison visualizations | Already installed; use for baseline overhead pie charts, per-tool bar charts |
| pandas | latest (needs install) | DataFrame operations for structured token data | Install when analyzing multi-session datasets; DuckDB can export to pandas |
| @anthropic-ai/tokenizer | 0.0.4 (npm) | Local tokenizer for relative comparisons | Only for pattern analysis (code vs prose tokenization); never for absolute counts |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| DuckDB | pandas + raw Python | DuckDB is faster for JSONL and SQL is more natural for aggregation; pandas better for time-series manipulation |
| ccusage | Custom JSONL parser | ccusage handles session identification and aggregation; but JSONL data has known undercount issues regardless of tool |
| Python scripts | Claude Agent SDK | Agent SDK enables programmatic Claude Code execution but adds complexity; simple Python scripts with anthropic SDK sufficient for Phase 1 |

**Installation:**
```bash
# Core: Anthropic Python SDK
pip install anthropic

# Core: DuckDB for SQL analysis
pip install duckdb

# Core: pandas for data manipulation
pip install pandas

# Session analysis
npx ccusage@latest --help  # verify it runs

# jq already installed (v1.7.1)
```

**Version verification:** Package versions confirmed against registries on 2026-04-05:
- anthropic: 0.89.0 (latest on PyPI)
- duckdb: 1.5.1 (latest on PyPI)
- @anthropic-ai/sdk: 0.82.0 (latest on npm, for TypeScript option)
- ccusage: 18.0.10 (latest on npm)

## Architecture Patterns

### Recommended Project Structure
```
tokens-experiment/
├── scripts/                    # Measurement and experiment scripts
│   ├── count_tokens.py         # Core: count_tokens API wrapper
│   ├── capture_statusbar.sh    # Statusbar JSON capture hook
│   ├── measure_baseline.py     # Baseline overhead measurement
│   ├── measure_tools.py        # Per-tool cost measurement
│   └── setup_duckdb.py         # DuckDB schema initialization
├── data/
│   ├── raw/                    # Raw measurement data (JSONL, JSON captures)
│   ├── baselines/              # Baseline overhead measurements
│   └── experiments/            # Per-experiment data directories
├── analysis/
│   ├── schemas/                # DuckDB schema definitions
│   └── queries/                # Reusable SQL queries
├── system-prompts/             # Extracted system prompt components (from Piebald-AI reference)
├── results/                    # Processed results and visualizations
│   └── baseline-report.md      # Phase 1 baseline findings
├── CLAUDE.md
└── .planning/
```

### Pattern 1: Progressive Payload Building (for count_tokens)
**What:** Build message payloads incrementally, measuring token count at each step to isolate per-component cost.
**When to use:** System prompt mapping (REV-01) and baseline overhead measurement (MEAS-03).
**Example:**
```python
# Source: Anthropic count_tokens API docs
import anthropic
client = anthropic.Anthropic()

def measure_delta(base_kwargs, addition_key, addition_value):
    """Measure token delta when adding a component."""
    base_count = client.messages.count_tokens(
        model="claude-sonnet-4-6",
        **base_kwargs,
        messages=[{"role": "user", "content": "Hello"}],
    ).input_tokens

    modified_kwargs = {**base_kwargs, addition_key: addition_value}
    modified_count = client.messages.count_tokens(
        model="claude-sonnet-4-6",
        **modified_kwargs,
        messages=[{"role": "user", "content": "Hello"}],
    ).input_tokens

    return modified_count - base_count

# Example: measure system prompt overhead
delta = measure_delta(
    base_kwargs={},
    addition_key="system",
    addition_value="<the system prompt text>"
)
print(f"System prompt adds {delta} tokens")
```

### Pattern 2: Statusbar JSON Capture (for live session measurement)
**What:** Configure a statusbar hook script that logs the full JSON payload to a file after each assistant message, creating a timestamped token usage log.
**When to use:** MEAS-02 (capture statusbar data), MEAS-05 (validation).
**Example:**
```bash
#!/bin/bash
# ~/.claude/statusline-capture.sh
# Captures statusbar JSON to a log file AND displays status

input=$(cat)

# Log the full JSON payload with timestamp
LOGDIR="$HOME/tokens-experiment/data/raw/statusbar"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/$(echo "$input" | jq -r '.session_id').jsonl"
echo "$input" >> "$LOGFILE"

# Also display useful status
MODEL=$(echo "$input" | jq -r '.model.display_name')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
COST_FMT=$(printf '$%.4f' "$COST")
echo "[$MODEL] ${PCT}% | $COST_FMT"
```

**Configuration (settings.json):**
```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline-capture.sh"
  }
}
```

### Pattern 3: DuckDB Analysis Pipeline
**What:** Load raw measurement data into DuckDB for SQL-based cross-session analysis.
**When to use:** MEAS-08 (statistical analysis setup).
**Example:**
```python
import duckdb

conn = duckdb.connect('data/token_research.duckdb')

# Create schema for experiment data
conn.execute("""
    CREATE TABLE IF NOT EXISTS measurements (
        experiment_id VARCHAR,
        session_id VARCHAR,
        turn_number INTEGER,
        timestamp TIMESTAMP,
        input_tokens INTEGER,
        output_tokens INTEGER,
        cache_creation_tokens INTEGER,
        cache_read_tokens INTEGER,
        model VARCHAR,
        claude_code_version VARCHAR,
        measurement_source VARCHAR,  -- 'statusbar', 'count_api', 'cost_cmd', 'context_cmd'
        notes VARCHAR
    )
""")

# Create schema for baseline overhead measurements
conn.execute("""
    CREATE TABLE IF NOT EXISTS baseline_components (
        measurement_id VARCHAR,
        measurement_date TIMESTAMP,
        component VARCHAR,          -- 'system_prompt', 'tool_schemas', 'claude_md', etc.
        tokens INTEGER,
        model VARCHAR,
        claude_code_version VARCHAR,
        mcp_servers VARCHAR[],      -- list of active MCP servers
        notes VARCHAR
    )
""")

# Read JSONL session data directly (for relative comparison)
conn.execute("""
    CREATE VIEW IF NOT EXISTS session_messages AS
    SELECT * FROM read_json(
        'data/raw/statusbar/*.jsonl',
        auto_detect=true,
        filename=true
    )
""")
```

### Pattern 4: Experiment Template
**What:** Standardized structure for each before/after experiment.
**When to use:** MEAS-07 (experiment methodology design).
**Example:**
```markdown
# Experiment: [Name]

## Metadata
- Date: YYYY-MM-DD
- Claude Code version: 2.1.92
- Model: claude-sonnet-4-6
- MCP servers: [none | list]
- CLAUDE.md: [hash or "default"]

## Hypothesis
[What we expect to find]

## Setup
- Task: [exact task description]
- Control session: [settings for control]
- Treatment session: [settings for treatment]
- Control variables: [what stays the same]

## Raw Data
| Metric | Control | Treatment |
|--------|---------|-----------|
| Total input tokens | | |
| Total output tokens | | |
| Total cache creation | | |
| Total cache read | | |
| Session duration | | |
| Turns to completion | | |
| Compaction events | | |

## Measurement Sources
- Statusbar JSON: [path]
- /cost output: [screenshot/copy]
- /context output: [screenshot/copy]

## Analysis
[Statistical comparison, DuckDB queries]

## Conclusions
[What we learned]
```

### Anti-Patterns to Avoid
- **Trusting JSONL input_tokens:** JSONL logs record streaming placeholders (75% are 0 or 1). Never use these for absolute token counts. Always cross-reference with statusbar JSON or /cost output.
- **Measuring output tokens only:** Context compounding means input tokens dominate session cost. Always measure total session tokens (input + output + thinking).
- **Running experiments across cache boundaries:** A 5-minute pause evicts the prompt cache, changing costs. Keep experiments in continuous sessions or document pauses as variables.
- **Ignoring compaction as a confound:** If an experiment crosses a compaction boundary, the before/after comparison is measuring compaction effects too. Design experiments to complete within one compaction cycle.
- **Forgetting thinking tokens:** Extended thinking (~32K budget by default) is invisible in the terminal but billed as output. Always account for it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting for Claude 3+ | Custom tokenizer | Anthropic count_tokens API | Claude 3+ uses a proprietary tokenizer; local tokenizers are only accurate for Claude 1/2 |
| Session token aggregation | Custom JSONL parser | ccusage (with caveats) | ccusage handles session identification, 5-hour block alignment, cache token separation |
| SQL analysis of JSONL | Python loops over JSON | DuckDB read_json() | DuckDB natively reads JSONL files and provides SQL aggregation with zero preprocessing |
| Statusbar data capture | Screen scraping or log parsing | Statusbar hook script | Official mechanism; receives clean JSON on stdin after every assistant message |
| System prompt catalog | Manual extraction from sessions | Piebald-AI/claude-code-system-prompts repo | Updated within minutes of each Claude Code release; 110+ strings cataloged for v2.1.92 |

**Key insight:** The measurement stack for this project is entirely read-only instrumentation. We are not building software; we are building a measurement rig. Every custom component should be a thin script that calls an existing API or tool and logs the result.

## Common Pitfalls

### Pitfall 1: The JSONL Undercount (100-174x)
**What goes wrong:** JSONL session logs record streaming placeholders for input_tokens. 75% of entries show 0 or 1 input tokens. Thinking tokens are excluded entirely. A session reported as 225K by ccusage may actually be 10.4M tokens.
**Why it happens:** Claude Code writes JSONL during streaming with placeholder values that are never updated. The statusbar receives finalized totals from a separate code path.
**How to avoid:** Use statusbar JSON capture for session-level totals. Use count_tokens API for component-level measurement. Use ccusage only for relative comparisons between sessions, never absolute claims. Document the undercount prominently in methodology.
**Warning signs:** Token counts seem suspiciously low relative to session duration; input_tokens cluster around 0-1; no thinking tokens appear.

### Pitfall 2: Cache TTL Confounds (5-Minute Eviction)
**What goes wrong:** Prompt cache has a 5-minute TTL. Any pause >5 minutes evicts the cache entirely, forcing full context re-creation. Two identical experiments -- one continuous, one with a break -- show different token costs.
**Why it happens:** Cache is time-based, not usage-based. Active typing keeps it warm; any gap kills it.
**How to avoid:** Note session continuity as an experimental variable. Design experiments to run within continuous sessions. Account for cache-cold-start costs (first turn always creates cache at 1.25x base price).
**Warning signs:** Spike in cache_creation_input_tokens after a gap in the statusbar log.

### Pitfall 3: Confusing Cache Cost Savings with Context Space Savings
**What goes wrong:** Assuming cached tokens don't count against the context window. They do. Caching reduces monetary cost (reads at 10% of base price) but not context pressure.
**Why it happens:** "Caching" intuitively implies less space used.
**How to avoid:** Maintain separate metrics: cost-per-token vs. context-space-consumed. Verify with /context that cached content appears in the token breakdown.
**Warning signs:** Research claims "caching extends your context window."

### Pitfall 4: Compaction as Confounding Variable
**What goes wrong:** Auto-compaction at ~83.5% context usage produces a lossy summary (~20-30% detail survival). If an experiment crosses this boundary, measurements reflect compaction effects, not the technique being tested.
**Why it happens:** Compaction is invisible unless you monitor /context or check for compaction events in session logs.
**How to avoid:** Design experiments to complete within a single compaction cycle (~167K tokens on 200K window). Monitor for compaction events. Log /context output at experiment start and end.
**Warning signs:** Sudden quality degradation mid-session; /context showing recent compaction; context usage drops from 80%+ to 20%.

### Pitfall 5: Stream-JSON Token Duplication (3-8x Inflation)
**What goes wrong:** When using `claude --output-format stream-json`, multi-block responses (thinking + text + tool_use) each preserve complete usage statistics, inflating reported counts 3-8x.
**Why it happens:** SDK splits single API responses into separate streaming events.
**How to avoid:** Always cross-reference stream-json output against JSONL transcripts or statusbar JSON. Prefer statusbar capture for session-level totals.
**Warning signs:** Token counts from stream-json are 3-8x higher than /cost reports.

### Pitfall 6: Missing ANTHROPIC_API_KEY
**What goes wrong:** count_tokens API calls fail with authentication errors. The API key is not currently set in this environment.
**Why it happens:** Environment variable not configured.
**How to avoid:** Set ANTHROPIC_API_KEY before running any measurement scripts. Validate early with a simple count_tokens call.
**Warning signs:** 401 errors from the Anthropic API.

## Code Examples

Verified patterns from official sources:

### count_tokens API Call (Python SDK)
```python
# Source: https://platform.claude.com/docs/en/api/messages-count-tokens
import anthropic

client = anthropic.Anthropic()

# Basic text counting
response = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Hello, Claude"}],
)
print(response.input_tokens)  # Exact count

# With tool definitions (measures tool schema overhead)
response = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="System prompt text here",
    tools=[{
        "name": "read_file",
        "description": "Read a file from the filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
            },
            "required": ["file_path"]
        }
    }],
    messages=[{"role": "user", "content": "Read my config file"}],
)
print(response.input_tokens)
```

### Statusbar JSON Payload Structure
```json
// Source: https://code.claude.com/docs/en/statusline (official docs)
{
  "session_id": "abc123...",
  "model": {"id": "claude-opus-4-6", "display_name": "Opus"},
  "version": "2.1.92",
  "cost": {
    "total_cost_usd": 0.01234,
    "total_duration_ms": 45000,
    "total_api_duration_ms": 2300,
    "total_lines_added": 156,
    "total_lines_removed": 23
  },
  "context_window": {
    "total_input_tokens": 15234,
    "total_output_tokens": 4521,
    "context_window_size": 200000,
    "used_percentage": 8,
    "remaining_percentage": 92,
    "current_usage": {
      "input_tokens": 8500,
      "output_tokens": 1200,
      "cache_creation_input_tokens": 5000,
      "cache_read_input_tokens": 2000
    }
  },
  "rate_limits": {
    "five_hour": {"used_percentage": 23.5, "resets_at": 1738425600},
    "seven_day": {"used_percentage": 41.2, "resets_at": 1738857600}
  },
  "transcript_path": "/path/to/transcript.jsonl"
}
```

**Key fields for measurement:**
- `context_window.current_usage`: Per-turn breakdown (input, output, cache creation, cache read)
- `context_window.total_input_tokens` / `total_output_tokens`: Cumulative across session
- `context_window.used_percentage`: Calculated from input tokens only (input + cache_creation + cache_read)
- `cost.total_cost_usd`: Running session cost
- `current_usage` is null before the first API call

### DuckDB JSONL Analysis
```python
# Source: DuckDB documentation + JSONL structure analysis
import duckdb

conn = duckdb.connect()

# Read statusbar capture logs
result = conn.execute("""
    SELECT
        session_id,
        context_window.current_usage.input_tokens as input_tokens,
        context_window.current_usage.output_tokens as output_tokens,
        context_window.current_usage.cache_creation_input_tokens as cache_create,
        context_window.current_usage.cache_read_input_tokens as cache_read,
        context_window.used_percentage as pct_used,
        cost.total_cost_usd as session_cost
    FROM read_json('data/raw/statusbar/*.jsonl', auto_detect=true)
    WHERE context_window.current_usage IS NOT NULL
    ORDER BY cost.total_cost_usd DESC
""").fetchall()
```

### ccusage Session Report
```bash
# Source: ccusage documentation
# Per-session breakdown (with known accuracy caveats)
npx ccusage@latest session

# Monthly aggregation
npx ccusage@latest monthly

# 5-hour block analysis (matches billing windows)
npx ccusage@latest block

# Specific date range
npx ccusage@latest session --from 2026-04-05 --to 2026-04-06
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| tiktoken for Claude token counting | Anthropic count_tokens API | 2024 (API launch) | Eliminated cross-tokenizer inaccuracy; free, exact counts |
| Full MCP tool schema loading | Deferred tool loading (ENABLE_TOOL_SEARCH=auto) | Late 2025 | Reduced MCP overhead from 30-50K to ~120 tokens (names only) |
| 45K compaction buffer | 33K compaction buffer | Early 2026 | ~12K more usable context per session |
| JSONL logs as ground truth | Statusbar JSON as ground truth | Recognized in community 2025-2026 | Eliminates 100x undercount from streaming placeholders |
| 200K context window only | 200K and 1M options (GA March 2026) | March 2026 | 1M window delays compaction but introduces attention degradation past 400K |

**Deprecated/outdated:**
- tiktoken: OpenAI's tokenizer; ~70% vocabulary overlap with Claude but NOT accurate for Claude 3+
- Xenova/claude-tokenizer: Based on Claude 1/2; "very rough approximation" for Claude 3+
- JSONL input_tokens as absolute measurement: Known streaming placeholder issue; use statusbar instead

## Open Questions

1. **Exact statusbar JSON update timing vs. JSONL writes**
   - What we know: Statusbar updates after each assistant message (debounced 300ms). JSONL is written during streaming.
   - What's unclear: Whether statusbar current_usage always reflects the final token count for a turn, or if there are edge cases where it captures an intermediate value.
   - Recommendation: Cross-reference first few statusbar captures with /cost output to validate consistency.

2. **count_tokens API accuracy vs. billing**
   - What we know: Anthropic states "the count is an estimate that may differ slightly from actual billing" and that they add "system optimization tokens that are NOT billed but ARE counted."
   - What's unclear: The magnitude of this discrepancy and whether it affects component-level deltas.
   - Recommendation: Measure the same payload multiple times to check for variance. Compare count_tokens results against /cost-reported input tokens for a minimal session.

3. **Piebald-AI system prompt completeness**
   - What we know: Catalogs 110+ strings for v2.1.92 (matching our installed version). Updated within minutes of releases.
   - What's unclear: Whether all conditional system prompt fragments are captured, especially those triggered by specific configurations (e.g., permission modes, agent settings).
   - Recommendation: Use Piebald-AI as a reference but validate against count_tokens API measurements. Do not rely on it as sole source.

4. **Extended thinking token observability**
   - What we know: Thinking tokens are billed as output but invisible in terminal. Statusbar should include them in total_output_tokens.
   - What's unclear: Whether statusbar's output token count includes thinking, or only visible output.
   - Recommendation: Run a controlled test -- same simple prompt with thinking enabled vs disabled -- and compare statusbar output_tokens.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All scripts | Yes | 3.13.1 | -- |
| anthropic (Python SDK) | MEAS-01, REV-01 | No (needs install) | 0.89.0 (on PyPI) | pip install anthropic |
| DuckDB (Python) | MEAS-08 | No (needs install) | 1.5.1 (on PyPI) | pip install duckdb |
| pandas | Data analysis | No (needs install) | latest | pip install pandas |
| jq | JSONL parsing, statusbar scripts | Yes | 1.7.1-apple | -- |
| matplotlib | Visualization | Yes | 3.10.3 | -- |
| Claude Code CLI | MEAS-02, MEAS-03, MEAS-04, MEAS-05 | Yes | 2.1.92 | -- |
| ccusage | MEAS-06 | Available via npx | 18.0.10 | npx ccusage@latest |
| Node.js | npx, optional TS scripts | Yes | 23.5.0 | -- |
| ANTHROPIC_API_KEY | MEAS-01, REV-01 | **No (not set)** | -- | Must be set before any API calls |
| JSONL session data | Analysis reference | Yes | 251 files across projects | -- |

**Missing dependencies with no fallback:**
- ANTHROPIC_API_KEY: Must be set before any count_tokens API calls. Blocks MEAS-01 and REV-01.

**Missing dependencies with fallback:**
- anthropic SDK: pip install anthropic (straightforward)
- DuckDB: pip install duckdb (straightforward)
- pandas: pip install pandas (straightforward)

## Project Constraints (from CLAUDE.md)

The CLAUDE.md file contains extensive project guidelines. Key directives relevant to Phase 1:

- This is a research project, not a product build -- all code serves measurement/analysis purposes
- Follow GSD workflow enforcement: use /gsd:execute-phase for planned phase work
- Findings must be backed by actual experiments or observable evidence, not just theoretical reasoning
- Report must be publishable -- clear writing, structured findings, reproducible experiments
- Focus on techniques available to end users (prompt strategies, CLAUDE.md configs, workflow patterns)

## Sources

### Primary (HIGH confidence)
- [Anthropic count_tokens API Reference](https://platform.claude.com/docs/en/api/messages-count-tokens) -- Full API specification, parameters, response format
- [Claude Code Statusline Documentation](https://code.claude.com/docs/en/statusline) -- Complete JSON payload schema, configuration, examples
- [Claude Code Manage Costs](https://code.claude.com/docs/en/costs) -- Token usage patterns, optimization strategies
- [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) -- 110+ system prompt strings for v2.1.92, 24 tool definitions
- [Claude Code Context Window Visualization](https://code.claude.com/docs/en/context-window) -- Interactive per-component token breakdown
- [Prompt Caching API](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) -- Cache mechanics, TTLs, pricing

### Secondary (MEDIUM confidence)
- [ccusage GitHub Repository](https://github.com/ryoppippi/ccusage) -- Session analysis tool documentation
- [DuckDB + Claude Code JSONL Analysis](https://liambx.com/blog/claude-code-log-analysis-with-duckdb) -- Community approach to SQL analysis
- [Where Do Your Claude Code Tokens Actually Go?](https://dev.to/slima4/where-do-your-claude-code-tokens-actually-go-we-traced-every-single-one-423e) -- Multi-segment session analysis
- [Claude Code JSONL Logs Undercount by 100x](https://gille.ai/en/blog/claude-code-jsonl-logs-undercount-tokens/) -- Detailed undercount analysis

### Tertiary (LOW confidence)
- Extended thinking budget behavior (community reports of 10% delivery rate) -- needs experimental validation
- Statusbar vs JSONL timing characteristics -- needs cross-reference validation in Phase 1

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools verified against current registries; official APIs documented
- Architecture: HIGH -- patterns derived from official documentation and verified data structures
- Pitfalls: HIGH -- multiple corroborating sources for each pitfall; JSONL undercount confirmed via independent analysis

**Research date:** 2026-04-05
**Valid until:** 2026-05-05 (30 days; stack is stable, Claude Code updates may change component token counts)
