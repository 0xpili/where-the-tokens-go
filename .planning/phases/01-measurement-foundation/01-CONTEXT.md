# Phase 1: Measurement Foundation - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish reliable token counting methodology, measure baseline overhead of Claude Code's system components, measure per-tool token costs, and create a validated experiment methodology for before/after comparisons. This phase produces the measurement instruments — all subsequent experiments depend on these being accurate.

</domain>

<decisions>
## Implementation Decisions

### Token counting approach
- **D-01:** Primary measurement for real Claude Code sessions uses statusbar JSON capture + `/cost` and `/context` commands — these are the most accurate sources per research findings
- **D-02:** Anthropic's count_tokens API used for component-level measurement (isolating system prompt, tool schemas, etc.)
- **D-03:** ccusage used for session-level aggregation with documented accuracy caveats (JSONL undercount acknowledged)
- **D-04:** Local tokenizers (@anthropic-ai/tokenizer) used only for relative comparisons, never for absolute claims

### Baseline measurement scope
- **D-05:** Full component breakdown required — system prompt, each built-in tool schema, CLAUDE.md (per level), memory (MEMORY.md), MCP server overhead, environment info each measured separately
- **D-06:** Baseline measured from a clean session with no conversation history to isolate fixed overhead
- **D-07:** Multiple measurements taken to establish variance/confidence intervals

### Experiment design
- **D-08:** Before/after experiments use identical task replay — same coding task executed in separate fresh sessions with different strategies
- **D-09:** Session-level totals compared (not per-turn, to capture compounding effects)
- **D-10:** Each experiment documents: task description, session setup, measurement method, raw data, and conclusions
- **D-11:** Control variables identified and documented for each experiment (model, Claude Code version, MCP servers active, CLAUDE.md content)

### Data storage & analysis
- **D-12:** DuckDB used for cross-session statistical analysis and querying
- **D-13:** Results also presented in structured markdown tables for report readability
- **D-14:** Raw measurement data preserved alongside analysis for reproducibility

### System prompt reverse engineering
- **D-15:** Map complete system prompt structure using count_tokens API with progressively built payloads
- **D-16:** Document token counts per component and how they change with different configurations (MCP servers, tools, memory)

### Claude's Discretion
- Exact DuckDB schema design for storing measurement data
- Choice of statusbar capture mechanism (hook scripts, manual recording, etc.)
- Specific coding tasks used as experiment benchmarks (should be representative but Claude picks the actual tasks)
- Organization of measurement scripts and data files within the project

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Research findings
- `.planning/research/STACK.md` — Token counting tools, analysis stack, measurement methodology recommendations
- `.planning/research/ARCHITECTURE.md` — Claude Code token consumption architecture, component breakdown, leverage points
- `.planning/research/PITFALLS.md` — Measurement pitfalls (JSONL undercount, cache misconceptions, thinking token invisibility)

### Project context
- `.planning/PROJECT.md` — Project goals and constraints
- `.planning/REQUIREMENTS.md` — Full v1 requirements with MEAS-01 through MEAS-08 and REV-01

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code

### Established Patterns
- None — patterns will be established in this phase

### Integration Points
- Anthropic count_tokens API (external)
- Claude Code statusbar JSON payload (local)
- Claude Code JSONL session logs at ~/.claude/projects/*/sessions/ (local, with known accuracy issues)
- ccusage CLI tool (external, to be installed)
- DuckDB (external, to be installed)

</code_context>

<specifics>
## Specific Ideas

- Research found that JSONL logs undercount by 100-174x — this must be prominently documented in methodology
- The Piebald-AI repo catalogs all 110+ Claude Code prompt strings with token counts — useful reference for system prompt mapping
- ccusage handles aggregation by daily/monthly/session/5-hour-block — leverage existing aggregation logic
- Statusbar JSON payload is the reliable real-time source — research validated across multiple independent sources

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-measurement-foundation*
*Context gathered: 2026-04-05*
