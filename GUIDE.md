# Claude Code Token-Saving Guide

**Use fewer tokens. Keep full performance. Hit limits slower.**

---

## The One Thing to Remember

Claude Code resends your **entire conversation** on every message. Turn 30 costs 25x more than turn 1. Managing this is 10x more impactful than any prompting trick.

---

## Setup (5 minutes, do once)

### 1. Create .claudeignore
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
Stops Claude from searching/reading irrelevant files. **Saves 15-30%.**

### 2. Trim CLAUDE.md
Keep it under 100 tokens. Every word costs on every request.

```markdown
# MyProject
Next.js 14, TypeScript, Tailwind, Prisma. Vitest for tests.
Don't explain changes — just make them. Keep responses brief.
```

Move detailed docs to separate files Claude reads on demand. **Saves 5-15%.**

### 3. Disable unused MCP servers
```bash
# Check what's loaded
cat ~/.claude/settings.json | jq '.mcpServers | keys'
```
Disable servers you're not using for this project. Each adds 500-4000 tokens to every request. **Saves 5-15%.**

---

## Daily Habits

### 4. /clear between tasks (THE most impactful thing)
```
> Fix the login bug
[done]
> /clear
> Now add the payments API
```
Drops accumulated context. Fresh start at ~20K instead of 200K+. **Saves 30-50%.**

### 5. Be specific about files
```
# Expensive (search cascade)
> Fix the authentication bug

# Cheap (direct hit)  
> Fix the null check in src/auth/login.ts:42
```
**Saves 10-25%.**

### 6. Batch your requests
```
# Bad: 4 messages = 4x context resend
> Add error handling
> Add logging
> Add validation
> Run tests

# Good: 1 message = 1x context resend
> In src/auth/login.ts: add error handling, logging, and validation. Run tests. Don't explain each step.
```
**Saves 20-40%.**

### 7. /compact with focus
```
/compact Keep the schema decisions and test patterns. Drop search results.
```
Do this at ~60% context utilization, not at 95% when auto-compact fires. **Saves 10-20%.**

---

## When Doing Complex Work

### 8. Segment large tasks
```
Session 1: Plan the refactor → /clear
Session 2: Refactor auth module → /clear  
Session 3: Refactor user module → /clear
Session 4: Update tests
```

### 9. Interrupt search spirals
If Claude is reading file after file looking for something:
```
> Stop. It's in src/lib/auth.ts
```
Saves 10K-50K tokens per incident.

### 10. Read with line ranges
Tell Claude exactly what section you need:
```
> Read src/utils.ts lines 40-60
```
Instead of loading 500 lines (5000 tokens) into context.

---

## What Doesn't Work

| Myth | Reality |
|------|---------|
| Cave talk / "respond like caveman" | Saves <0.1% in code editing tasks |
| Removing "please" and "thanks" | 2 tokens. Not worth thinking about. |
| Shorter prompts | Your prompt: 20 tokens. System overhead: 20,000. |
| Shorter variable names | Tokenizer handles them similarly |

---

## Impact Summary

| What | Savings | Effort |
|------|---------|--------|
| /clear between tasks | 30-50% | None |
| Batch requests | 20-40% | Low |
| .claudeignore | 15-30% | One-time |
| Be specific about files | 10-25% | Habit |
| "Don't explain" in CLAUDE.md | 10-20% | One-time |
| Focused /compact | 10-20% | Low |
| Disable unused MCP servers | 5-15% | One-time |
| Session segmentation | 20-40% | Medium |

**Combined: 40-60% fewer tokens than unoptimized usage.**

---

*Research conducted from inside Claude Code (Opus 4.6, 1M context) by direct self-observation. Full report: [REPORT.md](REPORT.md)*
