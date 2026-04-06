# Experiment 1: System Prompt Overhead — What Gets Sent Every Turn

**Method:** Direct observation from inside a Claude Code session (Opus 4.6, 1M context)
**Date:** 2026-04-06

## What I Can See In My Own Context

Every single API call to me includes these components, re-sent on every turn:

### Fixed Overhead (sent every request, prompt-cached after first)

1. **Core system prompt** — Behavioral instructions, security rules, output formatting, tool usage guidelines, tone/style rules, git commit instructions, PR creation instructions. This is substantial — several thousand tokens of instructions I receive on every conversation.

2. **Tool definitions** — Full JSON schemas for every built-in tool:
   - Read, Write, Edit, Glob, Grep, Bash, Agent, Skill, ToolSearch, AskUserQuestion
   - Each includes: name, description, parameter JSON schema with types, constraints, enums
   - These are essentially "small manuals" — the Edit tool alone has a multi-paragraph description
   - **Estimated: 24+ tool definitions, ~11-15K tokens total**

3. **Environment info** — Working directory, platform (darwin), shell (zsh), OS version, model info, git repo status, Claude Code version info. Small but present. ~200-300 tokens.

4. **CLAUDE.md files** — Loaded every session:
   - Global ~/.claude/CLAUDE.md (if exists)
   - Project ./CLAUDE.md (GSD generated one — includes project context, workflow rules)
   - Every token in CLAUDE.md costs on every single request
   - **Current project CLAUDE.md: needs measurement**

5. **Auto memory (MEMORY.md)** — First 200 lines loaded every session. Currently small (1 entry).

6. **MCP server instructions** — In this session, I can see:
   - Figma MCP server instructions (lengthy — URL parsing, design-to-code workflow, multiple tools)
   - Gmail, Google Calendar, Notion authenticators
   - KnowledgeFlow plugin tools
   - **These are loaded even though this project has nothing to do with Figma or Gmail**

7. **Deferred tool list** — Names of ~30+ deferred MCP tools (loaded as names only, full schemas fetched on demand via ToolSearch). This is relatively efficient but still present.

8. **Skill descriptions** — Long list of available skills (/gsd:*, /knowledgeflow:*, etc.). Each has a 1-2 line description. ~50+ skills listed. ~2-3K tokens.

9. **System reminders** — Injected periodically:
   - Current date/timestamp
   - TodoWrite reminders
   - File modification notifications
   - IDE context (opened files, selections)

### Growing Overhead (accumulates every turn)

10. **Full conversation history** — Every prior message (user + assistant) plus every tool call and result. This is the big one. By turn 30, this dominates everything.

11. **Tool results** — Every Read, Grep, Glob, Bash result stays in context. A single `Read` of a large file can add thousands of tokens that persist for the rest of the session.

## Key Observations

### The MCP Problem
I currently have Figma, Gmail, Google Calendar, Notion, and KnowledgeFlow MCP servers configured. Their instructions are loaded into my context on **every single request** even though this project is a pure research/writing task. This is pure waste.

**Actionable finding:** Disable MCP servers you're not using for the current project. Each server adds 500-3000+ tokens of instructions to every request.

### The CLAUDE.md Tax
Every token in CLAUDE.md files costs on every request. The GSD-generated CLAUDE.md includes workflow enforcement rules, project context, and conventions. For a heavy session with 50+ turns, a 2000-token CLAUDE.md means 100K+ tokens of cumulative overhead just from that file.

**Actionable finding:** Keep CLAUDE.md lean. Move detailed instructions to files that are read on-demand rather than loaded every turn.

### The Skill Description Bloat
I can see 50+ skill descriptions loaded into my context. Most are GSD workflow commands. If you're not using GSD or only using a few skills, this is overhead.

### Tool Schemas Are Heavy
24+ built-in tool schemas at ~500 tokens each = ~12K tokens. You can't reduce this (they're built-in), but it means your "empty" conversation already starts at ~15-20K tokens before you type anything.

## What This Means For Daily Users

The **minimum tax** for opening Claude Code is roughly:
- ~4K system prompt
- ~12K tool schemas
- ~1-3K CLAUDE.md
- ~1-3K MCP servers (varies wildly — could be 0 or 50K+)
- ~1-3K skills, memory, environment
- **Total: ~20-25K tokens before you say "hello"**

This is prompt-cached (90% cost discount after first request), but it still counts against your context window limit.

## Recommendations (from this observation)

1. **Audit your MCP servers** — Disable any you're not actively using
2. **Keep CLAUDE.md minimal** — Every word costs on every turn
3. **Be aware of the ~20K baseline** — Your first message is never "free"
4. **Tool schemas are fixed cost** — You can't change this, but know it exists
