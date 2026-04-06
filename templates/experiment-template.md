# Experiment: [EXPERIMENT_ID] - [Name]

## Metadata
| Field | Value |
|-------|-------|
| Experiment ID | [e.g., CTX-01-clear-impact] |
| Date | YYYY-MM-DD |
| Requirement | [e.g., CTX-01] |
| Claude Code version | [e.g., 2.1.92] |
| Model | [e.g., claude-sonnet-4-6] |
| MCP servers | [none / list] |
| CLAUDE.md | [hash or "default" or "none"] |
| Memory (MEMORY.md) | [present/absent, token count] |

## Hypothesis
[What we expect to observe. Must be falsifiable.]

## Task Description
[Exact task given to Claude Code. Must be identical for control and treatment.
Per D-08: Before/after experiments use identical task replay.]

## Control Variables (per D-11)
| Variable | Value | Why Controlled |
|----------|-------|----------------|
| Model | [same for both] | Different models have different token patterns |
| Claude Code version | [same for both] | System prompt changes across versions |
| MCP servers | [same for both] | MCP tools add overhead |
| CLAUDE.md content | [same for both, except if that IS the variable] | Affects system prompt size |
| Cache state | [cold start for both / documented] | Cache affects costs, not context size |
| Session state | [fresh session for both] | Per D-06: clean session |

## Setup

### Control Session
- Strategy: [baseline/default behavior]
- Session setup steps:
  1. [Step-by-step setup]

### Treatment Session
- Strategy: [the optimization being tested]
- Session setup steps:
  1. [Step-by-step setup]

## Raw Data (per D-09: session-level totals compared)

### Control
| Metric | Value | Source |
|--------|-------|--------|
| Total input tokens | | statusbar JSON / /cost |
| Total output tokens | | statusbar JSON / /cost |
| Total cache creation | | statusbar JSON |
| Total cache read | | statusbar JSON |
| Session duration (ms) | | statusbar JSON |
| Turns to completion | | count of statusbar entries |
| Compaction events | | /context monitoring |
| Peak context usage (%) | | statusbar JSON |

### Treatment
| Metric | Value | Source |
|--------|-------|--------|
| Total input tokens | | statusbar JSON / /cost |
| Total output tokens | | statusbar JSON / /cost |
| Total cache creation | | statusbar JSON |
| Total cache read | | statusbar JSON |
| Session duration (ms) | | statusbar JSON |
| Turns to completion | | count of statusbar entries |
| Compaction events | | /context monitoring |
| Peak context usage (%) | | statusbar JSON |

## Cross-Validation (per MEAS-05)
- /cost output (control): [copy]
- /cost output (treatment): [copy]
- /context output at start (control): [copy]
- /context output at end (control): [copy]
- /context output at start (treatment): [copy]
- /context output at end (treatment): [copy]

## Measurement Sources (per D-14: raw data preserved)
- Statusbar captures (control): data/experiments/[EXPERIMENT_ID]/control/
- Statusbar captures (treatment): data/experiments/[EXPERIMENT_ID]/treatment/
- DuckDB experiment ID: [EXPERIMENT_ID]

## Analysis

### Token Comparison
| Metric | Control | Treatment | Delta | % Change |
|--------|---------|-----------|-------|----------|
| Input tokens | | | | |
| Output tokens | | | | |
| Cache creation | | | | |
| Cache read | | | | |
| Total tokens | | | | |

### Confounding Variables Check
- [ ] No compaction events in either session (or documented if present)
- [ ] No cache TTL gaps > 5 min (or documented if present)
- [ ] Task completed fully in both sessions
- [ ] Same number of tool invocations (or documented difference)

## Conclusions
[What we learned. Was hypothesis confirmed or rejected?]
[Magnitude of effect, if any.]
[Confidence level and limitations.]

## Per D-10: Reproducibility
To reproduce this experiment:
1. Use Claude Code version [X]
2. Use model [X]
3. [Setup steps]
4. Run identical task: "[exact task text]"
5. Measure using statusbar JSON capture
