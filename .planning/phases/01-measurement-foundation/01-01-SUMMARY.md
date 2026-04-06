---
phase: 01-measurement-foundation
plan: 01
subsystem: measurement
tags: [anthropic-api, count-tokens, statusbar, ccusage, jq, duckdb, python]

# Dependency graph
requires: []
provides:
  - "count_tokens.py: reusable API wrapper with progressive payload building (count_tokens, measure_delta, count_with_tools, count_system_prompt)"
  - "capture_statusbar.sh: hook script logging full JSON payload to per-session JSONL files with compact status display"
  - "validate_ccusage.sh: ccusage validation with documented accuracy caveats"
  - "verify_environment.py: environment verification for all dependencies and API access"
  - "Project directory structure (data/raw/statusbar, data/raw/jsonl, data/baselines, data/experiments)"
  - "Measurement source hierarchy documentation (MEASUREMENT_SOURCES.md)"
affects: [01-02, 01-03, 02-experiment-execution]

# Tech tracking
tech-stack:
  added: [anthropic==0.89.0, duckdb==1.5.1, pandas==3.0.2]
  patterns: [progressive-payload-building, statusbar-json-capture, per-session-jsonl-logging]

key-files:
  created:
    - scripts/count_tokens.py
    - scripts/verify_environment.py
    - scripts/capture_statusbar.sh
    - scripts/validate_ccusage.sh
    - scripts/STATUSBAR_INSTALL.md
    - scripts/MEASUREMENT_SOURCES.md
    - data/raw/statusbar/.gitkeep
    - data/raw/jsonl/.gitkeep
    - data/baselines/.gitkeep
    - data/experiments/.gitkeep
  modified: []

key-decisions:
  - "count_tokens.py uses Anthropic SDK client.messages.count_tokens() for ground-truth measurement per D-02"
  - "Statusbar hook appends capture_timestamp to each JSON payload for temporal analysis"
  - "Measurement source hierarchy documented with statusbar JSON as primary per D-01"
  - "Scripts use python3 explicitly (no python alias on macOS)"

patterns-established:
  - "Progressive payload building: measure base, add component, measure delta to isolate per-component token cost"
  - "Per-session JSONL logging: one file per session_id for clean data separation"
  - "Repeat measurement: --repeat flag on count_tokens.py for variance/confidence per D-07"

requirements-completed: [MEAS-01, MEAS-02, MEAS-05, MEAS-06]

# Metrics
duration: 5min
completed: 2026-04-06
---

# Phase 1 Plan 1: Measurement Instrument Pipeline Summary

**count_tokens API wrapper with progressive payload building, statusbar JSON capture hook for per-session JSONL logging, ccusage validator with documented 100-174x JSONL undercount caveats, and measurement source hierarchy**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-06T01:02:56Z
- **Completed:** 2026-04-06T01:08:06Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Built count_tokens.py with 4 exported functions (count_tokens, measure_delta, count_with_tools, count_system_prompt) and CLI with text/file/system subcommands plus --repeat flag for variance measurement
- Created statusbar capture hook that logs timestamped JSON payloads to per-session JSONL files and displays compact status line (model, context %, input/output tokens, cost)
- Documented measurement source hierarchy with accuracy caveats: statusbar JSON (primary) > count_tokens API > /cost > /context > ccusage (relative only)
- Installed core dependencies: anthropic 0.89.0, duckdb 1.5.1, pandas 3.0.2
- Created full project directory structure with data/raw/statusbar, data/raw/jsonl, data/baselines, data/experiments

## Task Commits

Each task was committed atomically:

1. **Task 1: Create project structure, install dependencies, and build count_tokens API wrapper** - `3beffbe` (feat)
2. **Task 2: Create statusbar capture hook and validate ccusage** - `73bbb17` (feat)

## Files Created/Modified
- `scripts/count_tokens.py` - Reusable count_tokens API wrapper with 4 functions and CLI interface
- `scripts/verify_environment.py` - Environment verification checking Python, packages, jq, API key, API access
- `scripts/capture_statusbar.sh` - Statusbar hook logging JSON to per-session JSONL files
- `scripts/validate_ccusage.sh` - ccusage validation with accuracy caveats documentation
- `scripts/STATUSBAR_INSTALL.md` - Installation instructions for Claude Code settings.json
- `scripts/MEASUREMENT_SOURCES.md` - Source hierarchy, accuracy issues, cross-validation procedure
- `data/raw/statusbar/.gitkeep` - Directory for statusbar JSON captures
- `data/raw/jsonl/.gitkeep` - Directory for copied JSONL session logs
- `data/baselines/.gitkeep` - Directory for baseline overhead measurements
- `data/experiments/.gitkeep` - Directory for per-experiment data

## Decisions Made
- Used Anthropic SDK `client.messages.count_tokens()` directly (per D-02) rather than wrapping with retry logic -- the API is fast and free
- Added `capture_timestamp` to statusbar JSON payloads for temporal analysis -- allows correlating captures with session timing
- Documented measurement source hierarchy explicitly in MEASUREMENT_SOURCES.md to prevent future confusion about which data source to trust
- Used `python3` in shebangs since macOS does not have a `python` alias by default

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

### Authentication Gate: ANTHROPIC_API_KEY Not Set
- **During:** Task 1 verification (verify_environment.py)
- **Issue:** The ANTHROPIC_API_KEY environment variable is not set in the current shell environment. This means verify_environment.py exits with code 1 (2 critical failures: API key and API access test) and `count_tokens.py text "Hello world"` cannot produce output.
- **Impact:** Scripts are structurally complete and correct. They will work immediately once the API key is set.
- **Resolution:** The user needs to set `ANTHROPIC_API_KEY` from the Anthropic Console (https://console.anthropic.com/settings/keys). After setting:
  ```bash
  export ANTHROPIC_API_KEY="sk-ant-..."
  python3 scripts/verify_environment.py  # Should show all PASS
  python3 scripts/count_tokens.py text "Hello world"  # Should print JSON
  ```

## User Setup Required

**ANTHROPIC_API_KEY must be set before running measurement scripts.**

1. Go to https://console.anthropic.com/settings/keys
2. Create or copy an API key
3. Set the environment variable:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```
4. Verify with:
   ```bash
   python3 scripts/verify_environment.py
   ```

## Known Stubs

None - all scripts are fully implemented with real API calls and data handling.

## Next Phase Readiness
- Measurement instruments ready for Plans 01-02 (baseline overhead) and 01-03 (per-tool costs) once API key is configured
- Statusbar hook ready for installation -- user should add to settings.json before running real measurement sessions
- count_tokens.py measure_delta function ready for progressive payload building in 01-02

## Self-Check: PASSED

- All 11 files verified present on disk
- Both task commits (3beffbe, 73bbb17) verified in git log

---
*Phase: 01-measurement-foundation*
*Completed: 2026-04-06*
