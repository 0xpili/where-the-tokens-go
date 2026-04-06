# Requirements: Token Optimization Research for Claude Code

**Defined:** 2026-04-05
**Core Value:** Discover and validate concrete, measurable techniques that let Claude Code users stretch their usage limits further without losing quality

## v1 Requirements

### Measurement & Methodology

- [x] **MEAS-01**: Establish reliable token counting using Anthropic's count_tokens API for component-level measurement
- [x] **MEAS-02**: Capture statusbar JSON payload during real Claude Code sessions for accurate per-turn token tracking
- [ ] **MEAS-03**: Measure baseline overhead: system prompt, tool schemas, CLAUDE.md, memory, MCP — from a clean session
- [ ] **MEAS-04**: Measure per-tool token cost (Read, Edit, Bash, Grep, Glob, Write, Agent) with controlled inputs
- [x] **MEAS-05**: Use `/cost` and `/context` commands to validate measurements during live sessions
- [x] **MEAS-06**: Set up ccusage for session-level aggregation (with documented accuracy caveats)
- [ ] **MEAS-07**: Design before/after experiment methodology: identical tasks, different strategies, session-level totals compared
- [ ] **MEAS-08**: Set up DuckDB for cross-session statistical analysis of token consumption patterns

### Context Management

- [ ] **CTX-01**: Measure impact of `/clear` between unrelated tasks vs. continuing in same session
- [ ] **CTX-02**: Measure impact of `/compact` at different utilization thresholds (60% vs 80% vs auto at 95%)
- [ ] **CTX-03**: Measure impact of `.claudeignore` on context size with varying exclusion patterns
- [ ] **CTX-04**: Measure impact of specific file references vs. letting Claude search
- [ ] **CTX-05**: Test and measure the read-once hook (prevent re-reading files already in context)
- [ ] **CTX-06**: Test and measure subagent delegation patterns (verbose research routed to subagents)
- [ ] **CTX-07**: Test custom compaction instructions in CLAUDE.md for better context survival
- [ ] **CTX-08**: Test skills-based lazy loading for reducing initial context overhead

### Output Reduction

- [ ] **OUT-01**: Measure impact of verbosity suppression via CLAUDE.md instructions
- [ ] **OUT-02**: Controlled cave talk experiment: same coding task, normal vs. compressed response style
- [ ] **OUT-03**: Probe and measure extended thinking budget (default, actual usage, control via instructions)
- [ ] **OUT-04**: Measure token differences across models (Opus vs Sonnet vs Haiku) for identical tasks

### Reverse Engineering

- [ ] **REV-01**: Map complete system prompt structure with token counts per component
- [ ] **REV-02**: Map compaction behavior: what survives at different utilization levels, what gets lost
- [ ] **REV-03**: Probe prompt cache mechanics: invalidation hierarchy, TTL behavior, hit rate patterns
- [ ] **REV-04**: Measure extended thinking defaults, actual spend, and available control mechanisms

### Deliverables

- [ ] **DEL-01**: Comprehensive research report (.md) with methodology, experiments, findings, and measurements
- [ ] **DEL-02**: Practical actionable guide with techniques ranked by effort-vs-impact
- [ ] **DEL-03**: Reproducible experiment descriptions so readers can validate findings
- [ ] **DEL-04**: Before/after measurements for each tested technique

## v2 Requirements

### Advanced Techniques

- **ADV-01**: Automated token budgeting tool that tracks and alerts on consumption patterns
- **ADV-02**: Custom CLAUDE.md generator optimized for minimal token overhead
- **ADV-03**: Benchmark suite for continuous regression testing of token optimization strategies

### Community

- **COM-01**: Interactive web dashboard for visualizing token consumption patterns
- **COM-02**: Community-contributed technique catalog with upvoted effectiveness ratings

## Out of Scope

| Feature | Reason |
|---------|--------|
| Building Claude Code extensions/plugins | Research only — no product development |
| Techniques that degrade output quality | Core constraint — optimization must not hurt performance |
| Cross-LLM comparisons (GPT, Gemini, etc.) | Focused on Claude Code specifically |
| Pricing/cost optimization | Focus on token counts, not dollars |
| Modifying Claude Code internals | User-accessible techniques only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MEAS-01 | Phase 1 | Complete |
| MEAS-02 | Phase 1 | Complete |
| MEAS-03 | Phase 1 | Pending |
| MEAS-04 | Phase 1 | Pending |
| MEAS-05 | Phase 1 | Complete |
| MEAS-06 | Phase 1 | Complete |
| MEAS-07 | Phase 1 | Pending |
| MEAS-08 | Phase 1 | Pending |
| REV-01 | Phase 1 | Pending |
| CTX-01 | Phase 2 | Pending |
| CTX-02 | Phase 2 | Pending |
| CTX-03 | Phase 2 | Pending |
| CTX-04 | Phase 2 | Pending |
| CTX-05 | Phase 2 | Pending |
| CTX-06 | Phase 2 | Pending |
| CTX-07 | Phase 2 | Pending |
| CTX-08 | Phase 2 | Pending |
| OUT-01 | Phase 2 | Pending |
| OUT-02 | Phase 2 | Pending |
| OUT-03 | Phase 2 | Pending |
| OUT-04 | Phase 2 | Pending |
| REV-02 | Phase 2 | Pending |
| REV-03 | Phase 2 | Pending |
| REV-04 | Phase 2 | Pending |
| DEL-01 | Phase 3 | Pending |
| DEL-02 | Phase 3 | Pending |
| DEL-03 | Phase 3 | Pending |
| DEL-04 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0

---
*Requirements defined: 2026-04-05*
*Last updated: 2026-04-05 after roadmap phase mapping*
