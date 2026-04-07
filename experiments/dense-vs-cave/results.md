# Results: Dense Mode vs Cave Talk

**Date:** 2026-04-07
**Method:** Word count × 1.3 as token proxy (BPE tokenizers average ~1.3 tokens/word for English technical text)

---

## Output Token Comparison (6 Tasks × 4 Styles)

| Task | Type | Normal | Caveman Full | Caveman Ultra | Dense Mode |
|------|------|--------|-------------|---------------|------------|
| 1. React re-render | Prose | 296 | 142 | 57 | 125 |
| 2. JWT middleware fix | Code-heavy | 328 | 153 | 64 | 124 |
| 3. Micro vs mono | Prose | 354 | 181 | 55 | 147 |
| 4. Security review | Mixed | 393 | 155 | 65 | 152 |
| 5. Docker build | Code-heavy | 308 | 164 | 107 | 148 |
| 6. Refactor + tests | Tool-heavy | 255 | 101 | 77 | 100 |
| **Average** | | **322** | **149** | **71** | **133** |

## Reduction vs Normal (%)

| Task | Caveman Full | Caveman Ultra | Dense Mode |
|------|-------------|---------------|------------|
| 1. React re-render | 52% | 81% | 58% |
| 2. JWT middleware fix | 53% | 80% | 62% |
| 3. Micro vs mono | 49% | 84% | 58% |
| 4. Security review | 61% | 83% | 61% |
| 5. Docker build | 47% | 65% | 52% |
| 6. Refactor + tests | 60% | 70% | 61% |
| **Average** | **54%** | **77%** | **59%** |

### Key Observations

1. **Caveman Full averages 54% reduction** — below the repo's claimed 65%. The gap is explained by code blocks: our tasks include actual code (preserved unchanged in all styles), while their benchmarks skew toward pure prose tasks.

2. **Caveman Ultra averages 77% reduction** — impressive, but at significant readability and information cost (see below).

3. **Dense Mode averages 59% reduction** — actually *outperforms* Caveman Full by 5 percentage points on average. The arrow notation and key:value patterns compress more efficiently than just dropping articles.

4. **Code-heavy tasks cap compression** — Tasks 5 and 6 show the smallest gaps between styles because code blocks (unchanged) dominate the output. The commentary compresses, the code doesn't.

5. **Dense mode matches or beats caveman full on every task.** The only style that significantly beats dense mode is caveman ultra, which sacrifices readability.

---

## Information Completeness (1-5 scale)

5 = all actionable info present | 1 = critical info missing

| Task | Normal | Caveman Full | Caveman Ultra | Dense Mode |
|------|--------|-------------|---------------|------------|
| 1. React re-render | 5 | 5 | 4 | 5 |
| 2. JWT middleware fix | 5 | 5 | 4 | 5 |
| 3. Micro vs mono | 5 | 5 | 3 | 5 |
| 4. Security review | 5 | 4 | 3 | 5 |
| 5. Docker build | 5 | 5 | 5 | 5 |
| 6. Refactor + tests | 5 | 5 | 5 | 5 |
| **Average** | **5.0** | **4.8** | **4.0** | **5.0** |

### Notable Information Losses

**Caveman Ultra, Task 3 (Microservices):** Lost the progression path (profile → optimize → cache → modules → microservices). Just says "fix monolith." A junior dev gets no guidance on *how*.

**Caveman Ultra, Task 4 (Security review):** Compressed "timing attack on password comparison via short-circuit `==`" to "timing attack — `==` leaks info." Missing: *what* it leaks, *why* it matters, the connection to bcrypt's constant-time comparison. A security novice wouldn't understand the fix.

**Caveman Full, Task 4:** Dropped the username enumeration point and the input validation DoS vector. Minor but present.

**Dense Mode:** No information loss detected across any task. Arrow notation compresses structure, not content.

---

## Readability (1-5 scale)

5 = reads naturally | 1 = requires mental parsing

| Task | Normal | Caveman Full | Caveman Ultra | Dense Mode |
|------|--------|-------------|---------------|------------|
| 1. React re-render | 5 | 4 | 2 | 4 |
| 2. JWT middleware fix | 5 | 4 | 3 | 4 |
| 3. Micro vs mono | 5 | 4 | 2 | 4 |
| 4. Security review | 5 | 4 | 3 | 5 |
| 5. Docker build | 5 | 5 | 4 | 5 |
| 6. Refactor + tests | 5 | 5 | 4 | 5 |
| **Average** | **5.0** | **4.3** | **3.0** | **4.5** |

Dense mode reads like a senior dev's Slack message. Caveman full reads like hastily typed notes. Caveman ultra reads like... a caveman.

---

## Context Compounding Analysis

Using the model from Experiment 03: each response persists in context for all subsequent turns.

**Scenario: 30-turn coding session, average response tokens per style:**

| Style | Avg tokens/response | Tokens persisting over 30 turns* | Cumulative context cost |
|-------|--------------------|---------------------------------|------------------------|
| Normal | 322 | 322 × (30+29+28+...+1) = 322 × 465 | 149,730 |
| Caveman Full | 149 | 149 × 465 | 69,285 |
| Caveman Ultra | 71 | 71 × 465 | 33,015 |
| Dense Mode | 133 | 133 × 465 | 61,845 |

*Sum of 1 to 30 = 465 (each response is re-sent on all subsequent turns)

**Savings vs Normal over 30 turns:**
| Style | Tokens saved | % of Normal context cost |
|-------|-------------|------------------------|
| Caveman Full | 80,445 | 54% |
| Caveman Ultra | 116,715 | 78% |
| Dense Mode | 87,885 | 59% |

**But how much of total session cost is this?**

From Experiment 01: a 30-turn session costs roughly 500K-2M total tokens (input context resend + thinking + tool calls + output).

- 87,885 tokens saved by dense mode = **4-18% of total session cost**
- This is much larger than experiment 02's "0.08%" estimate, because experiment 02 only measured per-turn savings, not compounding

**Experiment 02 correction:** Cave talk isn't a rounding error when you account for compounding. 80-117K tokens of cumulative context savings is meaningful — equivalent to avoiding 5-10 unnecessary file reads.

---

## CLAUDE.md Compression Summary

(Full data in compression-test.md)

| Variant | Est. Tokens | Reduction | 50-turn overhead | Info (effective) |
|---------|-------------|-----------|-----------------|-----------------|
| Original (GSD-generated) | 3,120 | — | 156,000 | 100% |
| Caveman Compress | 1,105 | 65% | 55,250 | ~95% |
| Dense Mode Compress | 300 | 90% | 15,000 | ~85% |
| Minimal Rewrite | 46 | 99% | 2,300 | ~95% effective* |

*Minimal rewrite explicitly states only ~40% of original info, but Claude can derive the rest from the repo (stack from scripts, layout from ls, patterns from existing files).

**Key finding:** Caveman compress optimizes *prose within sections*. Dense mode compress *merges and restructures sections*. Minimal rewrite *removes entire unnecessary sections*. The approaches are orthogonal — each layer removes a different type of waste.

---

## Composite Scorecard

| Metric | Normal | Caveman Full | Caveman Ultra | Dense Mode |
|--------|--------|-------------|---------------|------------|
| Token reduction | 0% | 54% | 77% | 59% |
| Info completeness | 5.0 | 4.8 | 4.0 | 5.0 |
| Readability | 5.0 | 4.3 | 3.0 | 4.5 |
| 30-turn context savings | 0 | 80K | 117K | 88K |
| % of total session saved | 0% | 4-16% | 6-23% | 4-18% |
| Daily usability | High | Medium | Low | High |

**Winner: Dense Mode.** Best balance of savings, completeness, and readability. Saves 5% more than caveman full, loses zero information, and reads like a professional.

Caveman ultra wins on raw compression but fails the "would you actually use this daily" test.
