# CLAUDE.md Compression Test

**Subject:** A real-world GSD-generated CLAUDE.md — 165 lines, ~10,984 bytes, ~2,400 words, ~3,120 est. tokens
**Date:** 2026-04-07

The test subject is a real CLAUDE.md from an API QA testing project — a typical example of GSD-generated bloat: stack manifests, alternatives tables, empty placeholder sections, workflow enforcement, and source citations. Perfect test subject.

---

## Original (Baseline)

165 lines | ~2,400 words | ~3,120 est. tokens

Key sections and their approximate token cost:
- Repo layout + contributing + API details + rules: ~350 tokens (useful)
- GSD Project section: ~180 tokens (partially useful — restates constraints already in repo layout)
- GSD Stack section: ~1,600 tokens (massive — includes tool comparisons, alternatives, jq patterns, sources)
- GSD Conventions: ~20 tokens (empty placeholder)
- GSD Architecture: ~20 tokens (empty placeholder)
- GSD Workflow enforcement: ~100 tokens (GSD-specific, not useful outside GSD)
- GSD Developer profile: ~30 tokens (empty placeholder)

**Observation:** ~1,770 tokens (~57%) are stack manifests, tool comparisons, empty placeholders, and GSD workflow boilerplate that Claude either doesn't need or can infer from the repo.

---

## Variant A: Caveman Compress

**Rules applied:** Strip articles, filler, hedging. Preserve code blocks, URLs, headings, technical terms. Keep all sections.

```markdown
# API QA Testing

Repo stores manual QA test runs for REST API endpoints.

## Repo layout

- `alice/`, `bob/`, `carol/`, `dave/` — one folder per tester
- Inside each: one subfolder per round (e.g. `round-1/`, `round-2/`)
- Each round folder contains test scripts, outputs, notes

## Contributing test round

1. Go to your folder (e.g. `alice/`)
2. Create new round folder: `round-N/`
3. Add test files — curl scripts, response JSON, notes
4. Include `notes.md` if bugs found
5. Commit and push

## API details

- Base URL: `https://api.example.com/v1/resources`
- Auth: `X-API-Key` header (own key per tester, never commit)
- Endpoints: `/list`, `/detail`

## Rules

- Never commit API keys — use `***` placeholder
- Keep results in own folder
- Name rounds sequentially: `round-1`, `round-2`, etc.
- Save raw JSON with descriptive filenames

## Project

API QA — Alice Round 1. Independent QA sweep of REST endpoints. Tests schema correctness, filtering, sorting/pagination, edge cases.

Core Value: Find bugs before production.

Constraints: API key never committed, scope `alice/round-1/` only, results as `notes.md` with curl + observations.

## Technology Stack

### Core
| Technology | Purpose |
|------------|---------|
| curl 8.x | HTTP requests — team standard, scriptable, reproducible |
| jq 1.8.1 | JSON parsing, filtering, validation |
| Bash/Zsh | Shell scripting for test sequences |
| Git | Version control for test artifacts |

### Supporting
| Library | Purpose |
|---------|---------|
| direnv 2.x | Per-directory env vars — load API keys via `.envrc` |
| diff | Compare JSON responses across runs |
| tee | Save responses while viewing |

### jq Patterns
```bash
# Check field type across items
jq '[.[].active | type] | unique' response.json
# Verify sort order
jq '[.[].score] | . == sort | reverse' response.json
# Check pagination overlap
jq -s '.[0] == .[1] | not' page1.json page2.json
```

### Alternatives
| Recommended | Alternative | When |
|-------------|-------------|------|
| curl+jq | HTTPie | Single tester prefers readable syntax |
| curl+jq | Bruno | GUI needed for exploration |
| curl+jq | Postman | Never — killed free tier, cloud-dependent |
| bash | Python+requests | When jq one-liners become unreadable |

### Avoid
| Tool | Why |
|------|-----|
| Postman | Cloud-dependent, killed free tier |
| Selenium/Playwright | Browser tools, not API testing |
| Jest/Mocha/pytest | Overkill for manual QA |

## Domain-Specific Testing
| Concern | Check |
|---------|-------|
| Data staleness | `updatedAt` vs current time, flag >1hr |
| Math accuracy | Derived fields match source values |
| Cross-source | Spot-check vs authoritative source |
| Edge cases | Zero-value records, boundary conditions |
| Type consistency | `jq 'type'` checks (found bool-vs-int bug) |
```

**Result: ~100 lines | ~850 words | ~1,105 est. tokens**
**Reduction: 65% token reduction (3,120 → 1,105)**

---

## Variant B: Dense Mode Compress

**Rules applied:** Arrow notation, key:value pairs, no articles, no filler, one sentence per concept. Merge redundant sections. Remove placeholder sections entirely.

```markdown
# API QA Testing

QA test runs for REST API endpoints.

## Structure
Testers: `alice/`, `bob/`, `carol/`, `dave/` → each has `round-N/` subfolders → curl scripts + JSON responses + `notes.md`

## API
- URL: `https://api.example.com/v1/resources`
- Auth: `X-API-Key` header (never commit — use `***` placeholder)
- Endpoints: `/list`, `/detail`

## Rules
Own folder only. Sequential round naming. Descriptive JSON filenames. No committed keys.

## Current Scope
Alice Round 1 → schema correctness, filtering, sorting/pagination, edge cases on `/list` + `/detail`.

## Stack
Core: curl + jq + bash. Supporting: direnv (.envrc for keys), diff (cross-run comparison), tee (save+view).

## Key jq Patterns
```bash
jq '[.[].active | type] | unique' r.json              # type check
jq '[.[].score] | . == sort | reverse' r.json         # sort verify
jq -s '.[0] == .[1] | not' p1.json p2.json            # pagination overlap
```

## Domain Checks
Staleness: `updatedAt` >1hr = stale. Math: derived fields match sources. Cross-validate vs authoritative data. Edge cases: zero-value, boundary conditions. Types: jq type-check all fields (bool-vs-int bug precedent).
```

**Result: ~35 lines | ~230 words | ~300 est. tokens**
**Reduction: 90% token reduction (3,120 → 300)**

---

## Variant C: Minimal Rewrite (Experiment 12 Approach)

**Rules applied:** Remove everything Claude can infer from the repo itself. Keep only what's non-obvious or behavioral.

```markdown
# API QA Testing
API: `https://api.example.com/v1/resources` with `X-API-Key` header.
Never commit API keys. Stay in `alice/round-N/` only.
Results as notes.md with inline curl + observations.
```

**Result: 4 lines | ~35 words | ~46 est. tokens**
**Reduction: 99% token reduction (3,120 → 46)**

Claude can infer: repo layout (from ls), stack (from existing scripts), jq patterns (from existing round files), testing methodology (from notes.md files), domain knowledge (built-in). Only the API URL, auth method, key rule, and scope constraint are genuinely non-derivable.

---

## Comparison Table

| Variant | Lines | Words | Est. Tokens | Reduction | Info Preserved |
|---------|-------|-------|-------------|-----------|----------------|
| Original | 165 | 2,400 | 3,120 | — | 100% (much redundant) |
| Caveman Compress | ~100 | ~850 | ~1,105 | 65% | ~95% (trimmed prose) |
| Dense Mode Compress | ~35 | ~230 | ~300 | 90% | ~85% (merged + trimmed) |
| Minimal Rewrite | 4 | ~35 | ~46 | 99% | ~40% explicit, ~95% effective* |

*Minimal rewrite preserves only ~40% of the explicit information, but ~95% of the effective information because Claude can derive the rest from the repo.

## Compounding Impact

Over a 50-turn session, CLAUDE.md loads every request:

| Variant | Tokens x 50 turns | Cumulative overhead |
|---------|-------------------|-------------------|
| Original | 156,000 | baseline |
| Caveman Compress | 55,250 | -100,750 saved |
| Dense Mode Compress | 15,000 | -141,000 saved |
| Minimal Rewrite | 2,300 | -153,700 saved |

The gap between caveman compress and minimal rewrite is ~53,000 tokens over 50 turns — roughly equivalent to reading 10 medium source files.
