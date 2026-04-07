# Where the Tokens Go

Someone tweeted that asking Claude to "talk like a caveman" saves tokens. That sounded wrong, so I had Claude reverse-engineer itself to find out what actually works.

Turns out cave talk saves 54% of output tokens — but output is only a fraction of total session cost. The real costs are invisible: every message resends the full conversation history, and Claude burns 10-32K tokens of hidden "thinking" you never see. And **dense mode** (arrow notation, key:value, no filler) beats cave talk: 59% reduction, zero information loss, professional readability.

This repo is the raw research. Claude (Opus 4.6) spent a session introspecting its own context window, measuring its tool call costs, probing its system prompt, and documenting what it found.

## What's here

```
REPORT.md                  Full write-up with all findings
GUIDE.md                   Cheat sheet — just the actionable stuff
research/01-*.md … 13-*.md Individual experiments and analysis
dense-mode-skill/          Installable skill for dense mode responses
experiments/               Raw test data (dense vs cave talk comparison)
```

## Findings that surprised me

**Cave talk saves tokens, but dense mode saves more.** [Experiment 13](research/13-dense-vs-cave-talk.md) tested [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) head-to-head against dense mode across 6 tasks. Dense mode wins on every metric: 59% output reduction (vs 54%), 5.0/5 info completeness (vs 4.8), and 88K tokens saved over 30 turns via compounding. It reads like a tech lead's Slack message, not broken English. There's an [installable skill](dense-mode-skill/) if you want to try it.

**Your phrasing controls an invisible cost.** "What's the best way to handle auth?" triggers ~25K tokens of internal deliberation. "Add JWT auth with 1hr expiry to login.ts" triggers ~3K. Same result. 8x less hidden spend.

**You are the cheapest optimization.** Every fact you give Claude about your project — file paths, patterns to follow, where things live — saves a tool call. Tool calls are expensive and their results persist in context forever. Your knowledge is free.

**A 35-token CLAUDE.md beats a 500-token one.** Because CLAUDE.md loads on every single API request, a bloated one costs thousands of tokens per session in overhead alone. The [optimal CLAUDE.md](research/12-optimal-claudemd.md) exploits Claude's own behavioral patterns in 3 lines.

**Turn 30 costs 25x more than turn 1.** Claude resends the entire conversation on every message. Context grows linearly but cost grows quadratically across a session. `/clear` between tasks is the single highest-impact habit.

## Quick start

Put this in your project's `CLAUDE.md`:

```
Act, don't narrate. No preamble/summary/suggestions unless asked.
Edit over Write. Parallel tool calls. Grep before Read.
If stuck: say so in <10 words. Don't spiral.
```

Create a `.claudeignore`:

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

Disable MCP servers you're not using (`~/.claude/settings.json`).

Then just build the habit of typing `/clear` between unrelated tasks. That alone gets you most of the way there.

## Dense mode skill

Want Claude to compress its responses by ~59% without losing information? Install the dense mode skill:

```bash
npx skills add 0xpili/dense-mode
```

Then use `/dense` in any session. Three levels: default (arrows + key:value), lite (just cut filler), ultra (maximum compression). See the [research](research/13-dense-vs-cave-talk.md) behind it.

## Experiments

| # | Topic | The interesting part |
|---|-------|---------------------|
| [01](research/01-system-prompt-overhead.md) | System prompt overhead | Catalog of everything loaded before you type a word (~20K tokens) |
| [02](research/02-cave-talk-and-verbosity.md) | Cave talk | Per-turn savings are small, but compounding makes it Tier 4 (not irrelevant) |
| [03](research/03-context-compounding.md) | Context compounding | Why turn 30 costs 25x more than turn 1 |
| [04](research/04-mcp-and-claudemd-overhead.md) | MCP & CLAUDE.md | Figma MCP adds ~3K tokens to every request even when unused |
| [05](research/05-tool-call-efficiency.md) | Tool call costs | Glob is ~100 tokens, Agent spawn is ~15-30K |
| [06](research/06-creative-techniques.md) | Practical techniques | 10 approaches ranked by actual impact |
| [07](research/07-reverse-engineering-internals.md) | Internals | Prompt cache hierarchy, thinking budget, compaction behavior |
| [08](research/08-novel-experiments.md) | Undocumented behaviors | System reminders injected invisibly, deferred tool loading |
| [09](research/09-tokenizer-exploitation.md) | Tokenizer patterns | Dense mode proposal — structural compression over word-level |
| [10](research/10-dark-patterns-and-exploits.md) | Exploits | Multi-tool parallelism, agent isolation trick, preemptive stop |
| [11](research/11-live-self-probing.md) | Self-probing | What Claude can actually observe about its own context |
| [12](research/12-optimal-claudemd.md) | Optimal CLAUDE.md | 3 lines designed from inside to exploit Claude's own defaults |
| [13](research/13-dense-vs-cave-talk.md) | Dense mode vs cave talk | Empirical test: dense mode beats caveman 59% vs 54%, zero info loss |

## How this was made

I ran `/gsd:new-project` in Claude Code and told it to research token optimization by experimenting on itself rather than writing API wrapper scripts. Claude spent the session reading its own system prompt, tracing where tokens go on each turn, and testing what actually reduces consumption in a real coding workflow.

The token estimates combine direct observation (what Claude can see in its own context), community measurements (Piebald-AI prompt catalog, ccusage analysis), and the mathematical model of how context compounds across turns.

## License

MIT
