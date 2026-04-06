# Experiment 7: Reverse-Engineering Claude Code Internals

**Method:** Self-observation from inside an active Claude Code session (Opus 4.6, 1M context)
**Date:** 2026-04-06

## How I (Claude Code) Actually Process Your Messages

I can describe what I observe about my own context to reverse-engineer how the system works.

## The Prompt Architecture

### Layer 1: System Prompt (Fixed, Cached)

I receive a large system prompt that includes:
- **Identity and role** — "You are Claude Code, Anthropic's official CLI for Claude"
- **Security rules** — What I can and can't do (injection prevention, URL handling, etc.)
- **Tool usage rules** — When to use each tool, preferences (Read over cat, Edit over sed)
- **Git instructions** — Detailed commit, PR creation, and safety protocols
- **Tone/style rules** — Be concise, no emojis unless asked, specific formatting
- **Output efficiency** — "Go straight to the point. Try the simplest approach first."

This is ~4000-5000 tokens of instructions that define my behavior. It's the same every session.

### Layer 2: Tool Schemas (Fixed, Cached)

Each tool I have access to is defined with a full JSON schema:
```json
{
  "name": "Edit",
  "description": "Performs exact string replacements in files.\n\nUsage:\n- You must use your Read tool...",
  "parameters": {
    "file_path": {"type": "string", "description": "..."},
    "old_string": {"type": "string", "description": "..."},
    "new_string": {"type": "string", "description": "..."},
    "replace_all": {"type": "boolean", "default": false}
  }
}
```

Multiply this by 24+ tools and you get ~12K tokens of tool definitions.

**Key insight:** The Agent tool schema is particularly expensive because it includes descriptions of ALL available subagent types and detailed instructions for when/how to use each.

### Layer 3: Project Context (Loaded at Session Start, Cached)

- **CLAUDE.md** — Project instructions, conventions, stack info
- **MEMORY.md** — Cross-session notes (first 200 lines)
- **Environment** — Platform, shell, working directory, git status
- **MCP server instructions** — Each enabled server's usage guide
- **Skill descriptions** — Available slash commands with descriptions

### Layer 4: Conversation History (Grows Every Turn, Partially Cached)

Every prior message in the conversation, including:
- User messages (usually small)
- My responses (can be large if I explained things)
- Tool calls (my arguments)
- Tool results (can be VERY large — file contents, bash output, etc.)
- System reminders (injected by the system periodically)

**This is the layer that kills you.** It grows monotonically until /clear or /compact.

### Layer 5: Extended Thinking (Hidden, Not Cached)

Before generating my visible response, I may use "extended thinking" — internal reasoning that you don't see. This can be 10K-30K+ output tokens per turn. It's billed as output tokens but invisible in the UI.

You can observe its effects: sometimes I pause for a long time before responding. That's me thinking.

**The thinking budget is not well-documented.** From community reports, the default may be ~32K tokens for Opus. This means a simple "edit this file" could consume 32K output tokens of thinking + 100 tokens of visible response.

## Prompt Caching: What's Cached and What's Not

### Cached (90% Discount After First Request)
- System prompt
- Tool schemas
- CLAUDE.md files
- Memory
- MCP server instructions
- **The beginning of the conversation history** (the "stable prefix")

### Not Cached
- New messages at the end of the conversation
- Anything after a cache "breakpoint" (when the conversation diverges from the cached prefix)
- Extended thinking output

### Cache Invalidation
The cache follows a strict prefix hierarchy:
1. System prompt
2. Tool definitions  
3. CLAUDE.md/Memory
4. Conversation messages (in order)

If ANYTHING changes in this sequence, everything after the change point is invalidated. This means:
- Adding a new MCP server → invalidates tool definitions and everything downstream
- Modifying CLAUDE.md → invalidates CLAUDE.md cache and all conversation cache
- A new message → only the new message is uncached (conversation prefix still cached)

**Practical implication:** Don't modify CLAUDE.md mid-session if you can avoid it. It forces a full cache rebuild.

## The /compact Mechanism

When you run `/compact` (or auto-compaction triggers at ~95% utilization):

1. The system sends the full conversation to Claude with instructions to summarize
2. Claude produces a condensed summary of the conversation
3. The summary replaces the full conversation history
4. Future requests use: system prompt + tool schemas + CLAUDE.md + **summary** + new messages

**What survives:**
- Key decisions and code changes
- File paths mentioned
- The current task state

**What gets lost:**
- Exact file contents that were Read
- Detailed error messages
- Nuanced discussion context
- Instructions given early in the session (if not reinforced)

**The compaction tax:** The compaction itself costs tokens (the full conversation must be processed to create the summary). And post-compaction, Claude may re-read files it already read because the detailed content was lost.

## The Agent Tool: Token Multiplier

When I use the Agent tool:
1. A new Claude instance is created with its own context
2. It gets: its own system prompt + tool schemas + the task description
3. It works independently, consuming tokens for every tool call
4. It returns a summary to me (~200-500 tokens)

**The multiplication:** If an agent reads 10 files and makes 5 edits, that's perhaps 30K tokens of the agent's internal work. But I only see the 300-token summary. The 30K is "invisible" from the main conversation but still counts against your usage.

**When agents make sense:** Isolating a large research task. The agent's 30K of file reading doesn't pollute my main context.

**When agents waste tokens:** Simple tasks where I could just Grep + Read directly. The agent overhead (system prompt reload, etc.) makes it 10-50x more expensive than doing it myself.

## Key Takeaways for Token Optimization

1. **The system overhead is ~20K tokens** — you can't reduce tool schemas or the system prompt, but you CAN reduce CLAUDE.md, MCP servers, and memory
2. **Context compounding is the real enemy** — not output verbosity
3. **Extended thinking is a hidden cost** — potentially 10-30K output tokens you never see
4. **Prompt caching helps cost but not context space** — cached tokens still count against the window limit
5. **Agent spawning multiplies total tokens** — use only when the isolation benefit outweighs the overhead cost
6. **/compact loses detail** — proactive compaction with focus instructions preserves more
7. **Cache invalidation is hierarchical** — avoid mid-session changes to tools, CLAUDE.md, or MCP config
