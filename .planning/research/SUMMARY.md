# Research Summary: Claude Code Token Optimization

**Synthesized:** 2026-04-05
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

---

## Executive Summary

Claude Code's token consumption follows a compounding architecture: every API request re-sends a growing conversation context on top of a fixed overhead of ~18-20K tokens (system prompt + tool schemas + CLAUDE.md + memory). This means token costs grow quadratically with conversation length — making context management the single highest-leverage optimization area.

Realistic combined savings of **40-55% from an unoptimized baseline** are achievable through a layered strategy: context management (biggest impact), output reduction, prompt engineering, and creative techniques. The "cave talk" approach, while viral, is likely overrated for Claude Code specifically — agent tool-call turns (the majority of token usage) are unaffected by response style.

---

## Key Findings by Area

### Stack (How to Measure)

- **Anthropic Token Count API** (`/v1/messages/count_tokens`) is the only authoritative source for Claude 3+ token counts
- **Claude Code JSONL logs undercount by 100-174x** — they use streaming placeholders, never updated to real values. The statusbar JSON payload is the reliable source
- **ccusage + DuckDB** is the recommended analysis stack for processing session data
- **Claude Agent SDK** provides programmatic experiment orchestration with per-step token tracking
- **Local tokenizers** (`@anthropic-ai/tokenizer`) are only accurate for Claude 1/2; use for relative comparisons only

### Architecture (Where Tokens Go)

| Component | Tokens per Request | Cacheable? |
|-----------|-------------------|------------|
| System prompt | ~4,200 | Yes (90% discount) |
| Built-in tool schemas (24+) | ~11,600 | Yes (90% discount) |
| CLAUDE.md files | ~320-2,100+ | Yes (90% discount) |
| Memory (MEMORY.md) | ~680 | Yes (90% discount) |
| MCP servers | 1,000-50,000+ | Yes (90% discount) |
| Conversation history | Grows every turn | Partially |
| Extended thinking | ~32K output tokens/request | No |

**Critical insight:** Context compounding is the dominant cost driver. By turn 10, 100K+ tokens of history are re-sent per request. By turn 30, each request costs ~31x more than turn 1.

### Techniques (What to Do)

**Tier 1 — Highest Impact (30-60% savings):**
- Context clearing between tasks (`/clear`)
- Strategic compaction at ~60% utilization (`/compact`)
- Subagent delegation for research tasks (6K input → 420-token summary)
- `.claudeignore` for irrelevant files (30-40% context reduction)
- Thinking budget control (prevents default ~32K thinking per request)

**Tier 2 — Significant Impact (15-30% savings):**
- Model selection routing (Opus only for complex tasks, Sonnet for 80%)
- Suppressing output verbosity (30-50% output reduction)
- Plan Mode before coding (20-30% reduction)
- Specific file references in prompts (reduces search overhead)

**Tier 3 — Moderate Impact (5-15% savings):**
- CLAUDE.md optimization (every token costs on every request)
- MCP server management (disable unused servers)
- Batch operations (one complex prompt vs. many simple ones)
- Compact custom instructions for compaction

**Tier 4 — Creative/Experimental:**
- "Cave talk" / compressed response styles (overrated for agent turns)
- Token-aware prompt compression
- Skills-based lazy loading (54-82% initial context reduction)
- Read-once hook (60-90% reduction in Read tool tokens, validated across 107 sessions)

### Anti-Features (What NOT to Do)

1. **Uncoordinated parallel agents** — 300K tokens wasted in documented cases
2. **Over-compacting** — 70K tokens wasted repeating lost context
3. **Massive CLAUDE.md files** — 5K+ tokens taxed on every interaction
4. **Trusting JSONL logs for measurement** — 100x undercount
5. **Prompt caching ≠ context space savings** — cached tokens still count against window
6. **Overly terse prompts that cause retries** — net token increase
7. **Optimizing output tokens while ignoring input compounding** — rounding error in long sessions

---

## Recommended Research Phases

1. **Measurement Foundation** — Establish reliable token counting methodology, measure baseline overhead, validate measurement tools
2. **Technique Validation** — Test highest-impact techniques with controlled experiments (same task, different strategies)
3. **Deep Analysis & Creative Approaches** — Reverse-engineer compaction behavior, test unconventional techniques, probe tokenizer patterns
4. **Report & Guide** — Synthesize findings into publishable report + actionable guide

---

## Open Questions

- Exact token cost per tool invocation (Read, Edit, Bash, Write, Grep, Glob, Agent)
- Default extended thinking budget per model (community says ~32K for Opus)
- Compaction algorithm behavior: what survives at different utilization levels
- Whether deferred MCP tool loading meaningfully changes overhead
- Cache TTL in Claude Code (5-minute vs 1-hour)
- The "10% thinking budget delivery" claim (GitHub #20350) — measurement issue or real bug?

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|-----------|-------|
| Token architecture | HIGH | Official docs + interactive visualization |
| Measurement methodology | HIGH | Multiple sources confirm JSONL undercount |
| Table stakes techniques | HIGH | Official docs + community validation |
| Creative techniques (cave talk etc.) | MEDIUM | Contradicting evidence; needs controlled testing |
| Compaction internals | MEDIUM | Parameters documented, exact algorithm unknown |
| Extended thinking costs | MEDIUM | Default budget sourced from community, not official |
