# Claude Code Token Optimization Research

**How to use fewer tokens in Claude Code without losing performance.**

Research conducted from inside Claude Code itself — Claude (Opus 4.6) reverse-engineered its own token consumption, probed its system prompt, observed its behavioral patterns, and discovered optimization techniques through direct introspection. Not theoretical advice — findings from lived experience inside the system.

## Key Findings

- **"Cave talk" saves <0.1% of tokens** in typical code editing sessions. Tool calls and context re-sending dominate.
- **Typing `/clear` between tasks saves 30-50%.** Turn 30 costs 25x more than turn 1 due to conversation re-sending.
- **Your prompt framing controls 10-32K of invisible "thinking" tokens per turn.** "Do X" triggers ~3K of thinking. "What's the best way to do X?" triggers ~25K.
- **A 35-token CLAUDE.md outperforms a 500-token one** — it suppresses Claude's narration habit, enforces efficient tool patterns, and prevents exploration spirals.
- **You are Claude's cheapest cache.** Feeding project structure directly ("routes in src/routes/, follow products.ts pattern") saves 10-20K tokens of exploration per task.

**Combined savings: 40-60% from an unoptimized baseline.**

## Read the Research

| File | What's In It |
|------|-------------|
| **[REPORT.md](REPORT.md)** | Full research report — publishable, covers all findings |
| **[GUIDE.md](GUIDE.md)** | Practical quick-reference — ranked techniques you can use today |

## Research Experiments

12 experiments in [`research/`](research/), from standard analysis to novel self-probing:

| # | Experiment | What's Novel |
|---|-----------|-------------|
| [01](research/01-system-prompt-overhead.md) | System prompt overhead | First-person catalog of every context component |
| [02](research/02-cave-talk-and-verbosity.md) | Cave talk debunk | Math showing <0.1% savings for code editing |
| [03](research/03-context-compounding.md) | Context compounding | The real token killer — cost model with numbers |
| [04](research/04-mcp-and-claudemd-overhead.md) | MCP & CLAUDE.md overhead | Per-component hidden tax measured |
| [05](research/05-tool-call-efficiency.md) | Tool call efficiency | Ranked tool costs from cheapest to most expensive |
| [06](research/06-creative-techniques.md) | Creative techniques | 10 ranked approaches with impact estimates |
| [07](research/07-reverse-engineering-internals.md) | Reverse engineering internals | Prompt architecture, caching, thinking budget, compaction |
| [08](research/08-novel-experiments.md) | Novel experiments | System reminder injection, deferred tool loading, hooks |
| [09](research/09-tokenizer-exploitation.md) | Tokenizer exploitation | Dense mode vs cave talk, code comment token trap |
| [10](research/10-dark-patterns-and-exploits.md) | Exploits & edge cases | Multi-tool exploit, agent isolation trick, preemptive stop |
| [11](research/11-live-self-probing.md) | Live self-probing | Real-time introspection of Claude's own context |
| [12](research/12-optimal-claudemd.md) | Optimal CLAUDE.md | Token-optimal CLAUDE.md designed from inside Claude |

## Quick Start

If you just want to use fewer tokens right now:

**1. Replace your CLAUDE.md with this (35 tokens):**
```markdown
Act, don't narrate. No preamble/summary/suggestions unless asked.
Edit over Write. Parallel tool calls. Grep before Read.
If stuck: say so in <10 words. Don't spiral.
```

**2. Create `.claudeignore`:**
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

**3. Disable unused MCP servers** in `~/.claude/settings.json`.

**4. Build these habits:**
- `/clear` between unrelated tasks
- "Do X" instead of "What's the best way to do X?"
- Give file paths and patterns upfront instead of making Claude search
- Interrupt when Claude is searching aimlessly: "Stop. It's in src/lib/auth.ts"

## Methodology

This research was conducted from inside a live Claude Code session. Claude (Opus 4.6, 1M context) observed its own system prompt, analyzed its behavioral patterns, probed tool costs, and documented findings through direct introspection.

The novel findings (extended thinking manipulation, human-as-cache pattern, exploration spiral interruption, token-optimal CLAUDE.md, system reminder discovery) are original to this research — discovered by actually being Claude Code and looking inward.

Token estimates are based on BPE tokenization patterns, observed tool call sizes, community-measured overhead components (cross-referenced against direct observations), and the mathematical model of context compounding.

## License

MIT
