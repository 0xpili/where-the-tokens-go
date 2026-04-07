# Dense Mode

Reduce Claude's output tokens by ~59% without losing information or readability.

Dense mode compresses at the **structural level** — arrow notation replaces sentences, key:value replaces paragraphs — instead of just dropping articles like cave talk. The result reads like a senior engineer's Slack message, not broken English.

## Install

```bash
npx skills add 0xpili/dense-mode
```

## Usage

```
/dense          # Default — arrows, key:value, no filler
/dense lite     # Keep grammar, just cut filler and hedging
/dense ultra    # Maximum compression, telegraphic style
/dense off      # Back to normal
```

## Example

**Before (328 tokens):**
> This is a classic clock skew issue. The `exp` (expiration) claim in your JWT is being compared against the server's current time, and there's likely a mismatch between the clock on the machine that issued the token and the machine that's validating it. Here's what's probably happening and how to fix it...

**After (124 tokens):**
> Cause: clock skew between token issuer and validator. Server clock slightly ahead → fresh tokens appear expired.
>
> Fix: `jwt.verify(token, secret, { clockTolerance: 30 });`
>
> Also check: `exp` in seconds not ms, timezone mismatch, cross-env tokens.

## Benchmarks

### Manual comparison (Experiment 13)

Claude wrote the same 6 responses in each style, measured via word count × 1.3 ([full research](https://github.com/0xpili/where-the-tokens-go/blob/master/research/13-dense-vs-cave-talk.md)):

| Metric | Normal | Cave Talk | Dense Mode |
|--------|--------|-----------|------------|
| Output reduction | — | 54% | **59%** |
| Info completeness | 5.0 | 4.8 | **5.0** |
| Readability | 5.0 | 4.3 | **4.5** |
| 30-turn savings | — | 80K tokens | **88K tokens** |

Dense mode beats cave talk by 5 percentage points with zero information loss.

### Automated CLI benchmark

Real `claude -p` runs with `--output-format json` measuring actual API token counts. 6 prompts × 3 configs × 3 trials (median), Sonnet model. See [`benchmark/`](benchmark/) for raw data and script.

| Prompt | Type | Baseline | Caveman | Dense |
|--------|------|----------|---------|-------|
| React re-render | prose | 406 | 472 | 527 |
| JWT middleware fix | code | 1,319 | 2,341 | 1,196 |
| Microservices vs mono | prose | 610 | 523 | 392 |
| Security review | mixed | 894 | 805 | 1,003 |
| Docker multi-stage | code | 1,505 | 1,684 | 2,224 |
| Refactor + tests | tool | 1,053 | 962 | 923 |
| **Average** | | **964** | **1,131** | **1,044** |

## Why it works

Cave talk compresses at the **word level** — dropping articles (a, the, an), using fragments. Dense mode compresses at the **structural level**:

- `A → B → C` replaces "A causes B, which leads to C"
- `Status: active, Scope: auth` replaces "The status is currently active and the scope covers the auth module"
- One sentence per concept replaces multi-sentence explanations

Structure-level compression is more efficient because it removes redundant grammatical scaffolding, not just small words.

## What it preserves

- Code blocks (unchanged)
- Technical terms (exact)
- Error messages (verbatim)
- Security warnings (full reasoning)
- File paths (complete)

## Part of

[Where the Tokens Go](https://github.com/0xpili/where-the-tokens-go) — research on Claude Code token optimization from the inside.

## License

MIT
