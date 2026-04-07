# Experiment: Dense Mode vs Cave Talk

Empirical comparison of output compression techniques for Claude Code sessions.

## Files

- `test-cases.md` — 6 prompts × 4 response styles (Normal, Caveman Full, Caveman Ultra, Dense Mode) with token estimates
- `compression-test.md` — CLAUDE.md compression comparison using a real 165-line GSD-generated file
- `results.md` — Aggregated data, analysis tables, and composite scorecard

## Methodology

Each prompt answered in 4 styles. Token estimates via word count × 1.3. Information completeness and readability scored 1-5. Context compounding calculated using the model from Experiment 03.

Caveman rules sourced from [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman). Dense mode rules from Experiment 09.

## Key Result

Dense mode (59% reduction, 5.0 completeness, 4.5 readability) beats caveman full (54% reduction, 4.8 completeness, 4.3 readability) on every metric. Caveman ultra compresses more (77%) but loses information and readability.

For CLAUDE.md: don't compress, minimize. A 4-line rewrite beats a 100-line caveman-compressed version.
