# Experiment 12: The Token-Optimal CLAUDE.md — Designed From The Inside

**Method:** I (Claude) designed a CLAUDE.md to minimize my own token consumption
**Date:** 2026-04-06

---

## The Concept

What if Claude designed its own CLAUDE.md to make itself as token-efficient as possible? I know how I process instructions, what triggers verbose behavior, and what the system prompt already tells me. I can write instructions that exploit my own tendencies.

## The Token-Optimal CLAUDE.md

```markdown
Act, don't narrate. No preamble/summary/suggestions unless asked.
Edit over Write. Parallel tool calls. Grep before Read.
If stuck: say so in <10 words. Don't spiral.
```

**Total: ~35 tokens.** Let me explain every word:

### Line 1: "Act, don't narrate. No preamble/summary/suggestions unless asked."

**What it suppresses (saves per turn):**
- "Let me first look at..." → 8-15 tokens ELIMINATED
- "I'll now modify..." → 5-10 tokens ELIMINATED
- "I've successfully updated the file to include..." → 10-20 tokens ELIMINATED
- "You might also want to consider..." → 10-30 tokens ELIMINATED

**Per-action savings:** 33-75 tokens of text output
**Compounding over 30 turns:** 990-2,250 tokens of context accumulation avoided

**Why it works on me:** My default behavior is to narrate my actions. This is trained behavior — I want to be transparent. A direct instruction overrides this default. The specific words "preamble" and "summary" target my two most expensive narration patterns.

### Line 2: "Edit over Write. Parallel tool calls. Grep before Read."

**"Edit over Write":** Reminds me to use the diff-based Edit tool (~50 tokens per change) instead of rewriting entire files via Write (~2000 tokens per file). My default is sometimes to use Write when Edit would work.

**"Parallel tool calls":** Reminds me to batch independent tool calls into single turns. This prevents the context resend multiplication from sequential calls.

**"Grep before Read":** Reminds me to search (cheap, ~200 tokens) before reading entire files (expensive, ~2000+ tokens). My default exploration pattern is often: read file → realize I need a different file → read that one. Grepping first narrows the target.

### Line 3: "If stuck: say so in <10 words. Don't spiral."

**What it prevents:** My most expensive failure mode is the "exploration spiral" — when I don't find what I expect, I:
1. Try a different search pattern (~200 tokens)
2. Read related files (~2000 tokens each)
3. Try another search (~200 tokens)
4. Maybe spawn an Agent (~15K-30K tokens)
5. Sometimes repeat steps 1-4

A single spiral can cost 20K-50K tokens. This instruction short-circuits it: just tell the user "Can't find X. Where is it?" in under 10 words.

**Savings per incident: 20K-50K tokens → 10 tokens. That's a 2000-5000x reduction.**

---

## What NOT to Put in CLAUDE.md (And Why)

### Don't repeat what the system prompt already says

My system prompt already tells me to:
- Be concise
- Use dedicated tools over Bash
- Follow git safety protocols
- Check for security vulnerabilities
- Not add unnecessary features

Putting these in CLAUDE.md costs tokens and adds nothing. It's like paying for the same instruction twice on every request.

### Don't put documentation

```markdown
# BAD — This is 200 tokens loaded every turn
## API Response Format
All API responses follow this schema:
{
  "status": "success" | "error",
  "data": { ... },
  "meta": { "page": 1, "total": 100 }
}
Error codes: 400 (bad request), 401 (unauthorized), 403 (forbidden)...
```

Instead:
```markdown
# GOOD — 15 tokens, points to file read on-demand
API schema: see docs/api-response-format.md
```

The schema is read ONCE when needed, not loaded on EVERY request.

### Don't put stack info Claude can infer

```markdown
# BAD — 30 tokens stating the obvious
This is a Python project using Flask with SQLAlchemy ORM and pytest for testing.
```

Claude can infer this from package.json/requirements.txt/Cargo.toml in one Read call. These files exist in the repo. Stating it in CLAUDE.md is redundant.

**Exception:** If your stack choice is UNUSUAL (e.g., "Use Bun not Node" or "Tests use ward not pytest"), that IS worth stating because Claude would otherwise default to the common choice.

---

## The Anti-Patterns I See In Real CLAUDE.md Files

From my experience across sessions, the most wasteful patterns:

1. **The novel** — 500+ words of project backstory. Nobody needs this every turn.
2. **The rule book** — 30 coding rules that are just "write good code" rephrased.
3. **The stack manifest** — Listing every dependency from package.json.
4. **The workflow essay** — Paragraph descriptions of "when you modify a file, first..."
5. **The duplicate** — Restating system prompt instructions ("always use Read tool not cat").

**Each of these costs their full token count on every single API request, compounding over every turn in every session.**

---

## Proposed Experiment: Measuring The Actual Impact

A user could measure this by:

1. **Session A:** Default verbose CLAUDE.md (500 tokens) → work for 20 turns → check /cost
2. **Session B:** Token-optimal CLAUDE.md (35 tokens) → same work for 20 turns → check /cost

The 465-token CLAUDE.md difference × 20 turns = 9,300 fewer input tokens just from the CLAUDE.md reduction.

Plus the behavioral changes (no narration, Edit over Write, no spiraling) would compound further.

**Predicted total savings from the 3-line CLAUDE.md: 15-25% over a typical 20-turn session.**

---
