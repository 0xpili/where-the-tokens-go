# Claude Code Token-Saving Guide

**Researched from inside Claude Code. Not blog advice — actual exploits.**

---

## The One Thing

Claude resends your **entire conversation** every turn. Turn 30 costs 25x more than turn 1. Everything below targets this.

---

## Setup (5 minutes)

### 1. Replace your CLAUDE.md with this:
```markdown
Act, don't narrate. No preamble/summary/suggestions unless asked.
Edit over Write. Parallel tool calls. Grep before Read.
If stuck: say so in <10 words. Don't spiral.
```
35 tokens. Suppresses Claude's narration habit (saves 90% of text output), enforces efficient tool patterns, and prevents exploration spirals (which burn 20-50K tokens).

### 2. Create .claudeignore:
```
node_modules/
dist/
build/
coverage/
*.min.js
*.map
package-lock.json
pnpm-lock.yaml
```

### 3. Disable unused MCP servers:
```bash
cat ~/.claude/settings.json | jq '.mcpServers | keys'
```
Each unused server adds 500-4000 tokens to **every request**. If you're not using Figma, disable it.

---

## The Novel Techniques (Things Nobody Else Tells You)

### 4. Be Claude's cache
You know your project. Claude doesn't. Feed it directly instead of making it explore:

```
# Expensive — Claude explores (5-10 tool calls, 10-20K tokens)
> Add a users REST endpoint

# Cheap — you provide the map (0 tool calls saved)
> Add GET /api/users endpoint.
> Express in src/server.ts, routes in src/routes/.
> Follow src/routes/products.ts pattern. Tests in tests/routes/.
```

**Every fact you give saves a tool call. Think of yourself as a human context cache.**

### 5. Instructions, not questions
Your phrasing controls Claude's hidden thinking budget (10-32K tokens/turn you never see):

```
# Heavy thinking (~25K hidden tokens)
> What's the best approach for error handling here?

# Light thinking (~3K hidden tokens)  
> Add try/catch for DB and auth errors. Return 500/401.
```

Same result. 8x less invisible token spend.

### 6. Interrupt search spirals
When Claude reads file after file looking for something — stop it:

```
> Stop. It's in src/lib/auth.ts
```

One message. Saves 20-50K tokens that Claude would burn exploring.

**Signs of a spiral:** Multiple Greps, reading files and then reading different files, "Let me try another approach."

### 7. One message, many files
Claude can read multiple files in parallel within one turn. Sequential reads re-send earlier files redundantly:

```
# Bad — 3 turns, file A sent 3x, file B sent 2x
> Read auth.ts
> Now read db.ts
> And config.ts

# Good — 1 turn, each file sent once
> Read auth.ts, db.ts, config.ts and explain the auth flow
```

### 8. "I'll read the diff"
Claude shows code changes twice by default — in the Edit call AND in the explanation:

```
# Double-pay for code tokens
> Add validation and explain what changed

# Single-pay
> Add validation. I'll read the diff myself.
```

---

## The Standard Habits (Still Important)

### 9. /clear between tasks
The single highest-impact habit. **30-50% savings.** If the next task is unrelated, clear first.

### 10. /compact with focus
```
/compact Keep schema decisions and API patterns. Drop search results.
```
At ~60% utilization, not 95% when auto-compact fires.

### 11. Batch requests
```
# Bad — 4 round-trips = 4x context resend
> Add error handling
> Add logging
> Add validation  
> Run tests

# Good — 1 round-trip
> In login.ts: add error handling, logging, validation. Run tests. No explanation.
```

### 12. Decision anchors (survive compaction)
Write dense decision summaries that persist through /compact:
```
> DECISIONS: JWT auth, Prisma+PG, /api/v1 prefix, 
> errors={error,code}, tests in __tests__/ with vitest.
```

---

## What Genuinely Doesn't Work

| Myth | Reality |
|------|---------|
| "Cave talk" / "talk like caveman" | <0.1% savings for code editing tasks. Tool calls dominate. |
| Removing "please" / "thanks" | 2 tokens. Not even worth thinking about. |
| Shorter prompts | Your prompt: ~20 tokens. System overhead: ~20,000. |
| Shorter variable names | Tokenizer handles identifiers efficiently |

---

## Impact Summary

| Technique | Savings | Type |
|-----------|---------|------|
| /clear between tasks | 30-50% | Habit |
| Be Claude's cache (feed structure) | 10-40K/session | Novel |
| Instructions not questions (thinking control) | 5-20K/turn | Novel |
| 3-line CLAUDE.md | 15-25%/session | Novel |
| Interrupt spirals | 20-50K/incident | Novel |
| Batch requests | 20-40% | Habit |
| Multi-file single message | 20-40% on reads | Novel |
| .claudeignore | 15-30% | Setup |
| Disable unused MCP | 5-15% | Setup |
| "I'll read the diff" | 2x per code change | Novel |
| Focused /compact | 10-20% | Habit |

**Combined: 40-60% fewer tokens. The novel techniques (4-8) are where the real edge is.**

---

*Researched from inside Claude Code (Opus 4.6, 1M context). Full report with 12 experiments: [REPORT.md](REPORT.md)*
