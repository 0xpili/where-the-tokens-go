# Experiment 3: Context Compounding — The Real Token Killer

**Method:** Analysis of this actual session's behavior
**Date:** 2026-04-06

## The Core Problem

Every message in Claude Code re-sends the ENTIRE conversation history. This means:

- Turn 1: 20K (system) + your message = ~21K input tokens
- Turn 5: 20K (system) + 4 prior turns (~40K) + your message = ~61K input tokens  
- Turn 10: 20K (system) + 9 prior turns (~120K) + your message = ~141K input tokens
- Turn 20: 20K (system) + 19 prior turns (~350K) + your message = ~371K input tokens
- Turn 30: 20K (system) + 29 prior turns (~600K+) + your message = ~621K input tokens

**The cost of turn 30 is ~30x the cost of turn 1.** Not 30x total — 30x PER TURN.

## This Session As A Case Study

This session has been running the full GSD new-project workflow. Let me trace what happened:

### What entered my context and NEVER left:

1. **The entire workflow files** — I read new-project.md (~1200 lines), discuss-phase.md (~1000 lines), plan-phase.md (~860 lines), execute-phase.md (~850 lines). That's ~4000 lines of workflow instructions, each staying in context.

2. **All the research agent returns** — 4 parallel researchers returned findings. Each return was ~500-1000 tokens. Plus the synthesizer. All in context.

3. **Every tool call and result** — Every Bash command, every Read, every Write, every AskUserQuestion + response. All still here.

4. **The planner and checker returns** — Large structured outputs with requirement coverage tables.

5. **The executor returns** — 3 executor agents returned completion summaries.

6. **System reminders** — TodoWrite reminders, file modification notices, timestamps. Injected repeatedly.

### The compounding effect in practice:

Early in this session, asking me a question cost ~25K input tokens.
Now, asking me a question costs **significantly more** because all of the above is re-sent.

This is why `/clear` between tasks is the **single most impactful** thing you can do.

## Practical Strategies

### 1. Clear Between Tasks — Non-Negotiable
```
/clear
```
Starting a new logical task? Clear first. The 20K of system overhead to reload is trivial compared to carrying 200K+ of stale context.

**Rule of thumb:** If the next thing you're going to ask is unrelated to what you just did, `/clear`.

### 2. Compact Before You Need To
```
/compact
```
Or with focus:
```
/compact Focus on the database schema decisions and API endpoints
```

Auto-compaction triggers at ~95% context utilization. By then, the model has very little headroom to produce a quality summary. Compacting at ~60% gives much better results.

**Custom compaction instructions** matter: telling `/compact` what to prioritize preserving means the important context survives and the noise gets dropped.

### 3. Batch Your Work

**Bad (3 round trips, 3x context resend):**
```
> Add error handling to login.ts
> Now add logging to login.ts  
> And add input validation to login.ts
```

**Good (1 round trip):**
```
> In src/auth/login.ts: add error handling, logging, and input validation
```

Each round trip resends the full conversation. Fewer messages = dramatically fewer total tokens.

### 4. Be Specific About Files

**Bad (triggers search):**
```
> Fix the authentication bug
```
Claude will: Grep for "auth" → Read multiple files → Read CLAUDE.md for context → Eventually find the right file → Edit it. That's 5-10 tool calls, each adding to context.

**Good (direct hit):**
```
> Fix the null check in src/auth/login.ts:42
```
Claude will: Read the file → Edit line 42. Two tool calls.

### 5. Use Read with Line Ranges

**Bad:**
```
> Read the whole utils file
```
Could add 5000 tokens to context for a 200-line file.

**Good:**
```
> Read src/utils.ts lines 40-60
```
Adds ~100 tokens. The rest never enters context.

## The Compounding Math

If you send 30 messages in a session and each tool result averages 500 tokens:

**Without clearing:**
- Total input tokens: 20K + 21K + 22K + ... + 35K = ~825K just from system + growing history
- Plus tool results accumulating: adds another ~200-400K
- **Total session: ~1-1.2M input tokens**

**With /clear every 10 messages (3 mini-sessions):**
- Session 1: 20K + 21K + ... + 25K = ~225K
- Session 2: 20K + 21K + ... + 25K = ~225K  
- Session 3: 20K + 21K + ... + 25K = ~225K
- **Total session: ~675K input tokens — 35-45% savings**

**With /clear every 5 messages (6 mini-sessions):**
- Each: 20K + 21K + 22K + 23K + 24K = ~110K
- **Total session: ~660K input tokens — ~40-50% savings**

The math shows diminishing returns below 5-message sessions because the fixed 20K reload cost starts dominating.

## Sweet Spot

**Clear every 5-10 messages, or whenever you switch tasks.** This balances:
- The cost of reloading system context (~20K per clear)
- The cost of carrying stale context (grows linearly per turn)
- The loss of conversational continuity (you lose prior context)
