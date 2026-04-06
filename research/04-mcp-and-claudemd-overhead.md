# Experiment 4: MCP Servers & CLAUDE.md — The Hidden Per-Request Tax

**Method:** Direct observation of what's loaded in this session
**Date:** 2026-04-06

## What I Can See Right Now

### MCP Servers Loaded In This Session

From my system context, I can see instructions for:

1. **Figma MCP** — Extensive instructions: URL parsing rules, design-to-code workflow, component mapping, multiple tool descriptions. **This project has nothing to do with Figma.** Estimated: ~2-4K tokens.

2. **Gmail, Google Calendar, Notion** — Authentication tool definitions. Not used. ~200-500 tokens each.

3. **KnowledgeFlow** — Session tracking, search, analysis tools. ~500-1K tokens.

4. **Deferred tools list** — ~30 tool names from MCP servers. Small but present. ~200 tokens.

**Total MCP overhead in this session: ~4-6K tokens of instructions loaded on EVERY request for tools this project will never use.**

### Impact Calculation

Over a 30-turn session:
- MCP overhead per turn: ~5K tokens (cached at 90% discount after first turn)
- First turn: 5K tokens at full price
- Turns 2-30: 5K × 29 × 0.1 = 14.5K at cache price
- **Total MCP cost for the session: ~19.5K tokens effective, 150K tokens through the wire**

If you disabled unused MCP servers: **zero MCP overhead**.

### How To Check Your MCP Servers

```bash
# See what's configured
cat ~/.claude/settings.json | jq '.mcpServers | keys'

# Or check in Claude Code
/mcp
```

### How To Disable Per-Project

In your project's `.claude/settings.json`:
```json
{
  "mcpServers": {
    "figma": { "disabled": true },
    "gmail": { "disabled": true }
  }
}
```

Or globally in `~/.claude/settings.json` and enable only per-project when needed.

## CLAUDE.md: Every Word Costs Every Turn

### What's In This Project's CLAUDE.md

The GSD workflow generated a CLAUDE.md with:
- Project description and context
- Stack information  
- Workflow enforcement rules
- Coding conventions
- Architecture notes

This gets loaded on **every single API request**. If CLAUDE.md is 2000 tokens, that's 2000 tokens re-sent 30+ times per session.

### What Should Be In CLAUDE.md

**Good (high value per token):**
```markdown
# Project: Token Research
Python 3.13, no frameworks. Research outputs go in research/.
Write findings from direct observation, not theoretical analysis.
```
~30 tokens. Loaded every turn. High signal.

**Bad (low value per token):**
```markdown
# Project: Token Research  

## Overview
This project is a comprehensive research initiative exploring...
[200 words of context]

## Architecture
The project follows a research-driven methodology where...
[300 words of architecture]

## Conventions
When writing code, follow these conventions:
- Use type hints on all function signatures
- Prefer f-strings over .format()
- [20 more rules]
```
~500+ tokens. Most of it Claude already knows or could infer from the codebase.

### The CLAUDE.md Diet

**Keep:** Instructions that change Claude's default behavior
**Remove:** Information Claude could learn by reading the code
**Move:** Detailed reference docs to separate files (read on-demand, not every turn)

**Before (500 tokens):**
```markdown
# MyApp
React 18 + TypeScript + Tailwind CSS + Next.js 14 app router.
PostgreSQL with Prisma ORM. Auth via NextAuth.js with Google OAuth.
Testing with Vitest + React Testing Library.

## Code Style
- Components in src/components/, pages in src/app/
- Use server components by default, client only when needed
- All API routes in src/app/api/
- Prisma schema in prisma/schema.prisma
- Environment variables in .env.local (never commit)

## Conventions
- Use 'use client' directive only when component needs interactivity
- Prefer server actions over API routes for form submissions
- Use Zod for all input validation
- Error boundaries around every page-level component
... [20 more rules]
```

**After (80 tokens):**
```markdown
# MyApp
Next.js 14 app router, TypeScript, Tailwind, Prisma+PostgreSQL.
Server components by default. Zod validation. Vitest tests.
See docs/conventions.md for detailed rules.
```

**Savings:** 420 tokens × 30 turns = 12,600 fewer input tokens per session.

## Recommendations

1. **Audit MCP servers monthly** — Disable any you're not actively using
2. **CLAUDE.md under 100 tokens** — Move details to reference files
3. **Auto memory (MEMORY.md)** — Prune regularly. Old memories cost every turn.
4. **Skills** — If you have 50+ skills installed but use 5, the other 45 are overhead
