# Experiment 13: Dense Mode vs Cave Talk — The Empirical Test

**Method:** Side-by-side response generation across 6 tasks × 4 styles, with token measurement
**Date:** 2026-04-07

---

## Why This Experiment

In Experiment 02, I dismissed cave talk as "a meme" — saving 30 tokens out of 35K-245K total per turn, a rounding error. In Experiment 09, I proposed "dense mode" as a readable alternative and estimated 40-60% output reduction. Both were theoretical.

Then [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) published actual benchmarks claiming ~65% average output token reduction. They have real numbers. I had estimates and dismissals.

Time to put data behind the claims. I generated responses to 6 realistic Claude Code tasks in 4 styles — Normal, Caveman Full, Caveman Ultra, and Dense Mode — and measured everything.

## Setup

**4 styles tested:**

| Style | Rules |
|-------|-------|
| Normal | Default verbose Claude response |
| Caveman Full | Drop articles, fragments OK, `[thing] [action] [reason]` pattern |
| Caveman Ultra | Maximum compression — abbreviations, arrows, one word when possible |
| Dense Mode | Arrow notation for flows, key:value for attributes, no articles/filler, 1 sentence per concept |

**6 tasks** spanning the range of Claude Code work: React debugging explanation, JWT bug fix, architecture discussion, security code review, Docker implementation, and a refactor-then-test workflow. Mix of prose-heavy, code-heavy, and tool-heavy to test where compression diverges.

Full test cases and raw data: [experiments/dense-vs-cave/](../experiments/dense-vs-cave/)

---

## Finding 1: Caveman's 65% Claim Is Inflated For Coding Tasks

| Style | Average Reduction | Range |
|-------|------------------|-------|
| Caveman Full | 54% | 47-61% |
| Caveman Ultra | 77% | 65-84% |
| Dense Mode | 59% | 52-62% |

Caveman Full hits 54%, not the claimed 65%. The gap: their benchmarks skew toward pure prose tasks (explain a concept, describe an architecture). In Claude Code, responses include code blocks that are preserved unchanged across all styles. A Docker build task is 70% code — you can't compress a `Dockerfile`.

For prose-heavy tasks (React explanation, microservices discussion), caveman full does hit 50-60%. For code-heavy tasks, it drops to 47-50%. The claimed 65% is real — for a different workload mix than typical Claude Code usage.

## Finding 2: Dense Mode Beats Caveman Full

This surprised me. Dense mode averages 59% reduction vs caveman full's 54%. Five percentage points more compression while being more readable.

Why: Caveman removes articles and uses fragments but keeps conversational structure. Dense mode restructures — arrow notation (`A → B → C`) replaces entire sentences, key:value pairs replace paragraphs of explanation. It's compressing at the structural level, not just the word level.

**Same task (JWT bug fix), three styles:**

Normal (328 tokens):
> "This is a classic clock skew issue. The `exp` claim in your JWT is being compared against the server's current time, and there's likely a mismatch between the clock on the machine that issued the token and the machine that's validating it."

Caveman Full (153 tokens):
> "Clock skew issue. Token issuer clock and validator clock not synced. Even few seconds drift cause 'expired' on fresh tokens."

Dense Mode (124 tokens):
> "Cause: clock skew between token issuer and validator. Server clock slightly ahead → fresh tokens appear expired."

Dense mode is shorter *and* clearer. The arrow notation carries the causal chain that caveman's fragments lose.

## Finding 3: Code-Dominated Responses Cap Savings at ~20%

Tasks 5 (Docker) and 6 (refactor+test) show the smallest gaps between all styles. The reason: code blocks, which are preserved unchanged in every style, dominate the output.

A Docker multi-stage build response is ~70% Dockerfile. Caveman ultra gets 65% total reduction, but only by brutally compressing the 30% that is commentary. Dense mode gets 52% by the same mechanism — the code floor limits how much any text compression can achieve.

**This validates Experiment 02's core thesis.** For tool-heavy Claude Code workflows — read files, edit code, run tests — the visible text response IS a small fraction of total output. Compression techniques matter most for explanation-heavy interactions.

## Finding 4: Caveman Ultra Drops Safety Context

Information completeness scores (5 = all actionable info, 1 = critical info missing):

| Style | Avg Score | Notable Losses |
|-------|-----------|---------------|
| Normal | 5.0 | None |
| Caveman Full | 4.8 | Minor: dropped 1 of 7 security findings |
| Caveman Ultra | 4.0 | Dropped progression paths, security explanations, causal reasoning |
| Dense Mode | 5.0 | None |

Caveman ultra compressed the security review from 393 to 65 tokens — 83% reduction. But it dropped the *why* behind each vulnerability. "Timing attack — `==` leaks info" doesn't tell you what it leaks, why it matters, or how bcrypt solves it. A developer who doesn't already understand timing attacks gets a checklist, not understanding.

The microservices response compressed from 354 to 55 tokens. The actionable progression path (profile → optimize → cache → extract modules → microservices only at 30+ engineers) became "fix monolith." That's not advice, it's a bumper sticker.

Dense mode achieved 59% reduction with zero information loss across all 6 tasks. The compression comes from structure, not from cutting content.

## Finding 5: The Compounding Math Changes Everything

Experiment 02 measured cave talk savings per turn: ~30 tokens, negligible. But responses persist in conversation history and get re-sent every turn. Over a 30-turn session:

| Style | Avg tokens/response | Cumulative context cost (30 turns) | Saved vs Normal |
|-------|--------------------|------------------------------------|-----------------|
| Normal | 322 | 149,730 | — |
| Caveman Full | 149 | 69,285 | 80K |
| Dense Mode | 133 | 61,845 | 88K |

**88K tokens saved by dense mode over 30 turns.** That's not a rounding error. That's equivalent to avoiding 5-8 unnecessary file reads — one of the "Tier 2" optimizations from Experiment 06.

As a fraction of total session cost (500K-2M tokens): dense mode saves 4-18%. Not the 30-60% you get from `/clear` between tasks, but solidly in the range of other recommended optimizations like `.claudeignore` and batching requests.

**Experiment 02 was wrong about compounding.** Per-turn savings are negligible. Compounded savings are not.

## Finding 6: Don't Compress Your CLAUDE.md — Minimize It

I tested three approaches on a real 165-line, ~3,120-token CLAUDE.md (GSD-generated, with stack manifests, alternatives tables, and placeholder sections):

| Approach | Tokens | Reduction | What it does |
|----------|--------|-----------|-------------|
| Caveman Compress | 1,105 | 65% | Strips prose within every section |
| Dense Mode Compress | 300 | 90% | Restructures and merges sections |
| Minimal Rewrite | 46 | 99% | Removes sections Claude can infer |

Over 50 turns, the difference between caveman compress (55,250 cumulative tokens) and minimal rewrite (2,300 cumulative tokens) is 53,000 tokens. That's 10 file reads worth of waste.

Caveman compress optimizes *how* sections are written. Minimal rewrite asks *whether those sections should exist*. A 165-line file with stack manifests, tool comparison tables, and jq pattern libraries is information Claude can derive from the repo in a single Read. Paying 1,105 tokens per turn for cached knowledge is waste regardless of how concise the prose is.

The right CLAUDE.md strategy isn't compression — it's elimination.

---

## Updated Verdict

**Experiment 02 was half right.** Cave talk genuinely compresses output — 54% for full mode, 77% for ultra. That's real. But 02 was wrong to dismiss it as irrelevant because it only measured per-turn impact. When you account for context compounding over a full session, 54-59% output reduction translates to 80-88K tokens saved — meaningful optimization in the same tier as `.claudeignore` and request batching.

**But 02 was right about the bigger picture.** Even with compounding, output reduction is 4-18% of total session cost. Context management (`/clear`, `/compact`) at 30-60% savings still dwarfs it. And tool overhead (Experiment 05) is still the elephant in the room.

**Dense mode is the practical winner.** Same compression as caveman (actually 5% better), zero information loss, reads like a senior engineer's Slack messages instead of broken English. If you're going to pick a compression strategy for daily use, dense mode is the one.

## Actionable Takeaway

Add to CLAUDE.md:
```
Response format: arrow notation for flows, key:value for attributes.
No articles, no filler. One sentence per concept.
```

This gives you ~59% output reduction, zero information loss, and professional readability. It compounds to 80-90K tokens saved over a 30-turn session.

But remember the hierarchy:
1. `/clear` between tasks (30-60% total savings)
2. Batch requests, be specific about files (15-30%)
3. Lean CLAUDE.md + disabled unused MCP servers (5-15%)
4. Dense mode responses (4-18% via compounding)

Dense mode is tier 4. Don't skip tiers 1-3 to optimize tier 4.
