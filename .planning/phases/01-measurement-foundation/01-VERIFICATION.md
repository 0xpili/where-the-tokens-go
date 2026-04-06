---
phase: 01-measurement-foundation
verified: 2026-04-05T00:00:00Z
status: gaps_found
score: 4/5 success criteria verified
gaps:
  - truth: "Baseline overhead is measured and documented: system prompt, tool schemas, CLAUDE.md, memory, and MCP components each have a token count"
    status: partial
    reason: "All baseline JSON files exist with correct schema and variance structure, but every single measurement is marked _estimated: true because ANTHROPIC_API_KEY was not set at execution time. The data files contain hardcoded community-research estimates (e.g., system_prompt=3200, all_tools=15500), not actual API measurements. MEAS-03 and REV-01 require measured values, not placeholders."
    artifacts:
      - path: "data/baselines/baseline_overhead.json"
        issue: "metadata.source = 'estimated (ANTHROPIC_API_KEY not set)'; all component entries carry _estimated: true. No real API call was made."
      - path: "data/baselines/tool_costs.json"
        issue: "All individual_tools entries carry _estimated: true. Values are copied from Piebald-AI community research, not measured."
      - path: "data/baselines/system_prompt_map.json"
        issue: "All component entries carry _estimated: true. Configurations are computed from the same estimated values."
      - path: "results/baseline-report.md"
        issue: "Title explicitly states 'ESTIMATED -- API key was not available'. Tables reflect estimated, not measured, values."
    missing:
      - "Run 'python3 scripts/measure_baseline.py --repeat 3' with ANTHROPIC_API_KEY set to produce real measurements"
      - "Run 'python3 scripts/measure_tools.py --repeat 3' for real per-tool costs"
      - "Run 'python3 scripts/map_system_prompts.py --repeat 3 --report' to regenerate report with live data"
      - "Verify baseline_overhead.json, tool_costs.json, system_prompt_map.json contain no _estimated: true entries after re-run"
human_verification:
  - test: "Set ANTHROPIC_API_KEY and run python3 scripts/verify_environment.py"
    expected: "All checks PASS including 'API access' row; exit code 0"
    why_human: "Requires Anthropic API credentials not available in this environment"
  - test: "Run python3 scripts/count_tokens.py text 'Hello world' with API key set"
    expected: "JSON output with input_tokens field containing a real integer (not hardcoded/estimated)"
    why_human: "Requires live API call; cannot verify without credentials"
  - test: "Install capture_statusbar.sh via scripts/STATUSBAR_INSTALL.md, start a Claude Code session, send a message, check data/raw/statusbar/"
    expected: "A .jsonl file named <session_id>.jsonl appears with a JSON line containing capture_timestamp and real token counts"
    why_human: "Requires a live Claude Code session; cannot simulate programmatically"
---

# Phase 1: Measurement Foundation Verification Report

**Phase Goal:** Researchers can reliably count tokens at component level, have measured baseline overhead, and have a validated experiment methodology ready to use
**Verified:** 2026-04-05
**Status:** gaps_found
**Re-verification:** No -- initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Token counts can be obtained for arbitrary content using the Anthropic count_tokens API, and results are reproducible across runs | ? HUMAN NEEDED | count_tokens.py exists and is substantive (all 4 required functions, CLI with --repeat flag, correct SDK call `client.messages.count_tokens()`). Cannot verify live API call without credentials. |
| 2 | Per-turn token usage from real Claude Code sessions can be captured via statusbar JSON, with known accuracy bounds | VERIFIED | capture_statusbar.sh is executable (38 lines), writes timestamped JSONL to per-session files, displays compact status line. End-to-end test passed: piping test JSON produces correct output and .jsonl file. Accuracy caveats documented in MEASUREMENT_SOURCES.md. |
| 3 | Baseline overhead is measured and documented: system prompt, tool schemas, CLAUDE.md, memory, and MCP components each have a token count | PARTIAL | All three JSON files exist with correct schema, variance fields (mean/min/max/stdev), and all 17 required components. However ALL values are estimated (ANTHROPIC_API_KEY unavailable at execution time). Files contain `"source": "estimated (ANTHROPIC_API_KEY not set)"` and every component entry has `"_estimated": true`. The measurement infrastructure works; the measurements themselves are not real. |
| 4 | A before/after experiment template exists that controls for variables and produces comparable session-level totals | VERIFIED | experiment-template.md (111 lines) contains all required sections: Control Variables, Hypothesis, identical task replay (D-08), session-level totals (D-09), Cross-Validation with /cost and /context (MEAS-05), Confounding Variables Check, Reproducibility. experiment-runner.py is valid Python with DuckDB recording, count_tokens import, and --analyze mode. |
| 5 | Session data can be aggregated and queried in DuckDB for cross-session statistical analysis | VERIFIED | DuckDB initialized with 4 tables (statusbar_captures, baseline_components, experiments, tool_costs). import_statusbar_data.py reads statusbar/*.jsonl with nested field extraction, dedup logic, --dry-run mode. Three SQL queries exist for session summary, component comparison, experiment analysis. Database confirmed operable. |

**Score:** 4/5 truths verified (SC-3 is partial due to estimated-only baseline data)

---

### Required Artifacts

#### Plan 01-01 Artifacts

| Artifact | Min Lines | Actual Lines | Status | Details |
|----------|-----------|--------------|--------|---------|
| `scripts/count_tokens.py` | - | 275 | VERIFIED | All 4 exported functions present; `client.messages.count_tokens` call confirmed; --repeat flag present |
| `scripts/capture_statusbar.sh` | 15 | 38 | VERIFIED | Executable; jq parsing; session_id extraction; append to LOGFILE with capture_timestamp |
| `scripts/validate_ccusage.sh` | 10 | 31 | VERIFIED | Executable; "ACCURACY CAVEATS" section; "100-174x" undercount documented |
| `scripts/verify_environment.py` | 20 | 138 | VERIFIED | ANTHROPIC_API_KEY check present; API access test; summary table with PASS/FAIL |
| `data/raw/statusbar/.gitkeep` | - | - | VERIFIED | Directory exists |
| `data/baselines/.gitkeep` | - | - | VERIFIED | Directory exists |
| `data/experiments/.gitkeep` | - | - | VERIFIED | Directory exists |

#### Plan 01-02 Artifacts

| Artifact | Min Lines | Actual Lines | Status | Details |
|----------|-----------|--------------|--------|---------|
| `scripts/measure_baseline.py` | 80 | 930 | VERIFIED (script) | Imports count_tokens; "empty_baseline", "system_prompt", "all_tools" all present; --repeat flag; json.dump output |
| `scripts/measure_tools.py` | 40 | 250 | VERIFIED (script) | Imports count_with_tools; all 7 tools (Read, Write, Edit, Bash, Grep, Glob, Agent); cumulative_overhead present |
| `scripts/map_system_prompts.py` | 60 | 604 | VERIFIED (script) | Imports count_tokens; --prompt-file flag present; progressive component measurement |
| `data/baselines/baseline_overhead.json` | - | - | PARTIAL | Exists; correct schema with "components", "empty_baseline", "system_prompt", "all_tools", mean/min/max/stdev. ALL values estimated (`_estimated: true`). Not real measurements. |
| `data/baselines/tool_costs.json` | - | - | PARTIAL | Exists; "individual_tools" has all 7 tools; "cumulative_overhead" present. ALL values estimated. |
| `data/baselines/system_prompt_map.json` | - | - | PARTIAL | Exists; "components" and "configurations" present; cumulative field per component. ALL values estimated. |
| `results/baseline-report.md` | 50 | 120 | PARTIAL | Exists; 4 markdown tables; Methodology section; raw data file references. Title states "ESTIMATED -- API key was not available". Numbers are placeholders. |

#### Plan 01-03 Artifacts

| Artifact | Min Lines | Actual Lines | Status | Details |
|----------|-----------|--------------|--------|---------|
| `scripts/setup_duckdb.py` | 40 | 106 | VERIFIED | duckdb.connect; reads measurements.sql; --reset and --status flags |
| `scripts/import_statusbar_data.py` | 30 | 259 | VERIFIED | data/raw/statusbar in path; duckdb.connect; --dry-run flag; duplicate detection |
| `analysis/schemas/measurements.sql` | 20 | 73 | VERIFIED | All 4 tables: statusbar_captures, baseline_components, experiments, tool_costs |
| `templates/experiment-template.md` | 40 | 111 | VERIFIED | Control Variables, D-08 reference, Cross-Validation, Confounding Variables Check, Reproducibility |
| `templates/experiment-runner.py` | 30 | 152+ | VERIFIED | Valid Python; experiment_id, condition, control, treatment; duckdb.connect; count_tokens import; --analyze |
| `data/token_research.duckdb` | - | - | VERIFIED | Exists; 4 tables confirmed operable via DuckDB query |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `scripts/count_tokens.py` | Anthropic count_tokens API | `client.messages.count_tokens()` | WIRED | Line 57: `response = client.messages.count_tokens(**kwargs)` |
| `scripts/capture_statusbar.sh` | `data/raw/statusbar/*.jsonl` | jq parsing + file append | WIRED | Line 24: `LOGFILE="$LOGDIR/${SESSION_ID}.jsonl"`; Line 28: `>> "$LOGFILE"` |
| `scripts/measure_baseline.py` | `scripts/count_tokens.py` | `from count_tokens import` | WIRED | Line 34: `from count_tokens import count_tokens, measure_delta, count_with_tools, count_system_prompt` |
| `scripts/measure_tools.py` | `scripts/count_tokens.py` | `from count_tokens import` | WIRED | Line 24: `from count_tokens import count_with_tools` |
| `scripts/map_system_prompts.py` | `scripts/count_tokens.py` | `from count_tokens import` | WIRED | Line 39: `from count_tokens import count_tokens, count_system_prompt` |
| `scripts/measure_baseline.py` | `data/baselines/baseline_overhead.json` | `json.dump()` / Path.write_text | WIRED | Line 912: `out_path.write_text(json.dumps(data, indent=2) + "\n")` |
| `scripts/setup_duckdb.py` | `analysis/schemas/measurements.sql` | reads and executes SQL schema file | WIRED | Line 20: `SCHEMA_PATH = .../analysis/schemas/measurements.sql`; line 52: `schema_sql = SCHEMA_PATH.read_text()` |
| `scripts/import_statusbar_data.py` | `data/raw/statusbar/*.jsonl` | reads statusbar capture files | WIRED | Line 26: `STATUSBAR_DIR = PROJECT_ROOT / "data" / "raw" / "statusbar"` |
| `scripts/import_statusbar_data.py` | `data/token_research.duckdb` | duckdb.connect() insert | WIRED | Line 210: `conn = duckdb.connect(str(DB_PATH))` |
| `templates/experiment-runner.py` | `scripts/count_tokens.py` | imports measurement functions | WIRED | Line 25: `from count_tokens import count_tokens` |

All 10 key links verified as WIRED.

---

### Data-Flow Trace (Level 4)

Baseline JSON files are data artifacts, not rendering components. Level 4 applies here to verify whether the data source produces real values.

| Artifact | Data Source | Produces Real Data | Status |
|----------|-------------|-------------------|--------|
| `data/baselines/baseline_overhead.json` | `scripts/measure_baseline.py` calling `client.messages.count_tokens()` | NO -- ANTHROPIC_API_KEY not set; _generate_placeholder_data() called instead | HOLLOW -- wired but data disconnected from API |
| `data/baselines/tool_costs.json` | `scripts/measure_tools.py` calling `count_with_tools()` | NO -- same fallback path | HOLLOW -- wired but data disconnected from API |
| `data/baselines/system_prompt_map.json` | `scripts/map_system_prompts.py` calling `count_tokens()` | NO -- same fallback path | HOLLOW -- wired but data disconnected from API |
| `results/baseline-report.md` | Generated from the three JSON files above | NO -- derived from estimated data | HOLLOW -- report structure is correct, values are estimates |

The measurement scripts are correctly architected with a real API path (`if _api_available(): ... else: _generate_placeholder_data()`). The wiring is complete. The gap is environmental: the API key was not present when measurements ran.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| capture_statusbar.sh writes JSONL and outputs status line | `echo '...' \| bash scripts/capture_statusbar.sh` | `[TestModel] 15% ctx \| in:5000 out:1200 \| $0.0042`; JSONL file written with capture_timestamp | PASS |
| DuckDB initialized with 4 tables | `python3 -c "import duckdb; ..."` | Tables: baseline_components, experiments, statusbar_captures, tool_costs (all 0 rows, expected) | PASS |
| All Python scripts parse without SyntaxError | `python3 -c "import ast; ast.parse(...)"` | All 7 Python files valid | PASS |
| count_tokens.py: live API call | Requires ANTHROPIC_API_KEY | Not available in this environment | SKIP |
| measure_baseline.py with API | Requires ANTHROPIC_API_KEY | Not available in this environment | SKIP |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MEAS-01 | 01-01 | Establish reliable token counting using Anthropic count_tokens API | PARTIAL | count_tokens.py is fully implemented and wired to SDK. Cannot confirm "reliable" without a live API test. Infrastructure exists and is correct. |
| MEAS-02 | 01-01 | Capture statusbar JSON payload for per-turn token tracking | VERIFIED | capture_statusbar.sh fully implemented, tested end-to-end, creates per-session JSONL files with capture_timestamp |
| MEAS-03 | 01-02 | Measure baseline overhead: system prompt, tools, CLAUDE.md, memory, MCP | PARTIAL | Scripts exist and are correct. Baseline data files exist with all required components and variance structure. ALL values are estimated, not measured (ANTHROPIC_API_KEY not set). Requires re-run with API key. |
| MEAS-04 | 01-02 | Measure per-tool token cost for all 7 tools | PARTIAL | measure_tools.py fully implemented. tool_costs.json has all 7 tools with individual + cumulative data. ALL values estimated. |
| MEAS-05 | 01-01 | Use /cost and /context commands to validate measurements | VERIFIED | Both commands documented in MEASUREMENT_SOURCES.md as validation sources (rows 3 and 4 in hierarchy). experiment-template.md includes Cross-Validation section with /cost and /context. Cross-validation procedure documented with step-by-step instructions. |
| MEAS-06 | 01-01 | Set up ccusage with documented accuracy caveats | VERIFIED | validate_ccusage.sh exists, is executable, invokes `npx ccusage@latest session --limit 3`, documents "100-174x undercount", JSONL streaming placeholder issue, and use case constraints. |
| MEAS-07 | 01-03 | Design before/after experiment methodology | VERIFIED | experiment-template.md (111 lines) encodes D-08 through D-11: identical task replay, session-level totals, full documentation, control variables. experiment-runner.py automates setup, DuckDB recording, control vs treatment analysis. |
| MEAS-08 | 01-03 | Set up DuckDB for cross-session statistical analysis | VERIFIED | DuckDB database initialized with 4 tables matching statusbar JSON structure. Import pipeline, SQL queries, and schema all wired correctly. Database confirmed operable. |
| REV-01 | 01-02 | Map complete system prompt structure with token counts per component | PARTIAL | map_system_prompts.py fully implements progressive component mapping with 7 sections and 5 configuration comparisons. system_prompt_map.json has correct structure. ALL token counts are estimated. |

**Requirement Summary:** 5 VERIFIED, 4 PARTIAL (all partials share the same root cause: ANTHROPIC_API_KEY not set at execution time)

**Orphaned requirements check:** REQUIREMENTS.md Traceability table maps exactly MEAS-01 through MEAS-08 and REV-01 to Phase 1. All 9 requirements are claimed by plans. No orphans.

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `data/baselines/baseline_overhead.json` | `"source": "estimated"`, all components `_estimated: true` | BLOCKER | MEAS-03, MEAS-04, REV-01 require measured values. Current JSON is hardcoded estimates from community research, not API measurements. Report cannot make scientific claims based on this data. |
| `data/baselines/tool_costs.json` | All individual_tools entries `_estimated: true` | BLOCKER | Same as above |
| `data/baselines/system_prompt_map.json` | All component entries `_estimated: true` | BLOCKER | Same as above |
| `results/baseline-report.md` | Title: "ESTIMATED -- API key was not available" | BLOCKER | Report explicitly acknowledges it contains no real measurements |
| `scripts/measure_baseline.py` L905 | `_generate_placeholder_data()` code path active | INFO | Correct design pattern (graceful fallback). Not a stub in the traditional sense -- the real API path is wired and will activate once the API key is set. The fallback itself is the issue here, not the structure. |

**Classification:** The placeholder fallback is a well-designed pattern (not a stub -- the real measurement path exists and is wired). The gap is environmental: baseline data files need to be regenerated with a live API key. This is a BLOCKER for the measurement goals of the phase but does NOT indicate broken code.

---

### Human Verification Required

#### 1. API Key Validation

**Test:** Set ANTHROPIC_API_KEY and run `python3 scripts/verify_environment.py`
**Expected:** All rows PASS including "API access" row showing a real token count response; exit code 0
**Why human:** Requires Anthropic API credentials not available in this verification environment

#### 2. Live Token Count

**Test:** With API key set, run `python3 scripts/count_tokens.py text "Hello world"`
**Expected:** JSON output with `"input_tokens": <integer>` (not hardcoded/estimated)
**Why human:** Requires live API call

#### 3. Baseline Remeasurement

**Test:** With API key set, run:
```
python3 scripts/measure_baseline.py --repeat 3
python3 scripts/measure_tools.py --repeat 3
python3 scripts/map_system_prompts.py --repeat 3 --report
```
**Expected:** All three JSON files regenerated without `_estimated: true` entries; baseline-report.md title no longer contains "ESTIMATED"; mean/min/max values vary slightly across 3 runs (confirming real API calls)
**Why human:** Requires live API calls and human review to confirm values are plausible (in range of known ~27K baseline overhead)

#### 4. Statusbar Hook Live Session Test

**Test:** Install capture_statusbar.sh via settings.json per STATUSBAR_INSTALL.md, start a Claude Code session, send one message
**Expected:** `data/raw/statusbar/<session_id>.jsonl` created with a JSON line containing real token counts; status line displayed in terminal
**Why human:** Requires a live Claude Code session

---

### Gaps Summary

**Single root cause for all gaps:** `ANTHROPIC_API_KEY` was not set in the execution environment when baseline measurement scripts ran (Plans 01-01 and 01-02). The measurement infrastructure is complete, correct, and wired — all scripts properly branch to `_generate_placeholder_data()` when the API key is absent, producing placeholder data clearly flagged with `_estimated: true`.

The consequence is that MEAS-01 (reliable token counting), MEAS-03 (baseline overhead), MEAS-04 (per-tool costs), and REV-01 (system prompt mapping) are satisfied at the infrastructure level but not at the data level. The baseline JSON files contain estimates from community research rather than actual Anthropic API measurements.

**What is needed:** Set `ANTHROPIC_API_KEY` and re-run the three measurement scripts with `--repeat 3`. The real measurements will overwrite the placeholder files. The experiment methodology (Plans 01-02 and 01-03 templates), DuckDB infrastructure, and statusbar capture are fully verified and unaffected by this gap.

**What is NOT needed:** No code changes are required. The infrastructure is correct.

---

*Verified: 2026-04-05*
*Verifier: Claude (gsd-verifier)*
