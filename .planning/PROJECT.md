# Token Optimization Research for Claude Code

## What This Is

A deep-dive research project exploring techniques to reduce token consumption when using Claude Code without sacrificing output quality or performance. The project involves reverse-engineering Claude's tokenization, system prompt mechanics, tool call overhead, and context window behavior — then running real experiments to measure which strategies actually save tokens. The deliverable is a publicly shareable research report plus a practical guide.

## Core Value

Discover and validate concrete, measurable techniques that let Claude Code users stretch their usage limits further without losing the quality of Claude's responses.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Deep analysis of Claude's tokenizer behavior (what costs more/fewer tokens)
- [ ] Reverse-engineering of Claude Code system prompt structure and overhead
- [ ] Analysis of tool call token costs (Read, Edit, Bash, Grep, Glob, Write, Agent, etc.)
- [ ] Investigation of context window mechanics (compaction, caching, conversation length)
- [ ] Catalog of input token reduction techniques (prompt engineering, context management)
- [ ] Catalog of output token reduction techniques (response style, instruction tuning)
- [ ] Creative/unconventional approaches (cave talk, custom instructions, compressed prompts)
- [ ] Real experiments comparing token usage: same task, different strategies, measured results
- [ ] Comprehensive research report (.md) — publishable quality with methodology and findings
- [ ] Practical actionable guide — ranked techniques with effort-vs-impact assessment

### Out of Scope

- Building tools or extensions that modify Claude Code internals — research only
- Techniques that meaningfully degrade output quality — the whole point is maintaining performance
- Comparing Claude to other LLMs — this is about optimizing Claude Code specifically
- Pricing analysis or cost calculations — focus is on token counts, not dollars

## Context

- Claude Code users hit usage limits (token caps) during heavy sessions
- A viral tweet demonstrated "cave talk" (asking Claude to respond like a caveman) as a creative way to reduce output tokens
- Claude Code has significant system-level overhead: system prompts, tool schemas, MCP server instructions, conversation history
- The cl100k_base / Claude tokenizer has specific behaviors around whitespace, code, natural language, and special characters
- Claude Code's architecture includes context compaction, prompt caching, and tool result handling — all of which affect token economy
- This research could benefit the broader Claude Code community if published

## Constraints

- **Methodology**: Findings must be backed by actual experiments or observable evidence, not just theoretical reasoning
- **Quality bar**: Report must be publishable — clear writing, structured findings, reproducible experiments
- **Scope**: Focus on techniques available to end users (prompt strategies, CLAUDE.md configs, workflow patterns) — not internal API changes

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Deep reverse-engineering approach | User wants to understand the mechanics, not just surface tips | — Pending |
| Real experiments with measurements | Theoretical advice is cheap; measured results are valuable | — Pending |
| Dual deliverable (report + guide) | Research depth for credibility + practical guide for adoption | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-05 after initialization*
