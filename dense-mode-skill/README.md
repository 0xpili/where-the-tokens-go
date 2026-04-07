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

## How it compares

Tested across 6 Claude Code tasks ([full research](https://github.com/0xpili/where-the-tokens-go/blob/master/research/13-dense-vs-cave-talk.md)):

| Metric | Normal | Cave Talk | Dense Mode |
|--------|--------|-----------|------------|
| Output reduction | — | 54% | **59%** |
| Info completeness | 5.0 | 4.8 | **5.0** |
| Readability | 5.0 | 4.3 | **4.5** |
| 30-turn savings | — | 80K tokens | **88K tokens** |

Dense mode beats cave talk by 5 percentage points with zero information loss.

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
