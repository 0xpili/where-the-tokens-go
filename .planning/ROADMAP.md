# Roadmap: Token Optimization Research for Claude Code

## Overview

This research project moves through three phases following scientific methodology: establish measurement instruments and baselines, run controlled experiments across all technique categories, then synthesize findings into publishable deliverables. Every technique claim will be backed by measured data. The measurement foundation must be solid before any experiment runs, and all experiments must complete before the report can draw conclusions.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Measurement Foundation** - Establish reliable token counting, baseline overhead measurements, and experiment methodology
- [ ] **Phase 2: Controlled Experiments** - Run all context management, output reduction, and reverse engineering experiments with measured results
- [ ] **Phase 3: Synthesis & Deliverables** - Analyze findings and produce the publishable research report and practical guide

## Phase Details

### Phase 1: Measurement Foundation
**Goal**: Researchers can reliably count tokens at component level, have measured baseline overhead, and have a validated experiment methodology ready to use
**Depends on**: Nothing (first phase)
**Requirements**: MEAS-01, MEAS-02, MEAS-03, MEAS-04, MEAS-05, MEAS-06, MEAS-07, MEAS-08, REV-01
**Success Criteria** (what must be TRUE):
  1. Token counts can be obtained for arbitrary content using the Anthropic count_tokens API, and results are reproducible across runs
  2. Per-turn token usage from real Claude Code sessions can be captured via statusbar JSON, with known accuracy bounds
  3. Baseline overhead is measured and documented: system prompt, tool schemas, CLAUDE.md, memory, and MCP components each have a token count
  4. A before/after experiment template exists that controls for variables and produces comparable session-level totals
  5. Session data can be aggregated and queried in DuckDB for cross-session statistical analysis
**Plans**: TBD

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD
- [ ] 01-03: TBD

### Phase 2: Controlled Experiments
**Goal**: Every proposed token optimization technique has been tested with controlled experiments producing measured before/after results
**Depends on**: Phase 1
**Requirements**: CTX-01, CTX-02, CTX-03, CTX-04, CTX-05, CTX-06, CTX-07, CTX-08, OUT-01, OUT-02, OUT-03, OUT-04, REV-02, REV-03, REV-04
**Success Criteria** (what must be TRUE):
  1. Each context management technique (clear, compact, claudeignore, file references, read-once hook, subagent delegation, compaction instructions, skills lazy loading) has measured before/after token counts from identical tasks
  2. Each output reduction technique (verbosity suppression, cave talk, thinking budget control, model selection) has measured before/after token counts from identical tasks
  3. Compaction behavior is documented: what survives and what gets lost at different context utilization levels
  4. Prompt cache mechanics are documented: invalidation hierarchy, TTL behavior, and hit rate patterns observed
  5. All experiment results include methodology notes sufficient for a reader to reproduce the test
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD
- [ ] 02-03: TBD

### Phase 3: Synthesis & Deliverables
**Goal**: Research findings are synthesized into a publishable report and a practical guide that readers can act on immediately
**Depends on**: Phase 2
**Requirements**: DEL-01, DEL-02, DEL-03, DEL-04
**Success Criteria** (what must be TRUE):
  1. A comprehensive research report exists with clear methodology, experiment descriptions, measured findings, and conclusions
  2. A practical guide exists with techniques ranked by effort-vs-impact, so readers know what to try first
  3. Every experiment in the report includes reproducible descriptions (task, setup, measurement method, results)
  4. Every claimed technique has before/after measurements showing its actual impact

**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Measurement Foundation | 0/3 | Not started | - |
| 2. Controlled Experiments | 0/3 | Not started | - |
| 3. Synthesis & Deliverables | 0/2 | Not started | - |
