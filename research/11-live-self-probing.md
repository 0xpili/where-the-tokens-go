# Experiment 11: Live Self-Probing — What I Can Actually Observe Right Now

**Method:** Introspection during an active session
**Date:** 2026-04-06

---

## Probe 1: What's In My System Prompt Right Now

I'm going to enumerate everything I can observe that's been loaded into my context. This is reverse engineering from the inside.

### Things I KNOW are in my context because I can reference them:

1. **Full behavioral system prompt** — I can see instructions about:
   - Being concise, going straight to the point
   - Using specific tools for specific tasks (Read not cat, Edit not sed)
   - Git safety protocols (never force push, never amend unless asked)
   - How to create commits, PRs
   - Security rules (no command injection, etc.)
   - When to ask for confirmation vs proceed
   - Output efficiency rules

2. **Tool schemas I can see:**
   - Agent (with full subagent_type enum including ~30 types like gsd-executor, gsd-planner, gsd-debugger, etc.)
   - AskUserQuestion (with complex schema for questions, options, multiSelect, previews)
   - Bash (with execution rules, timeout, background)
   - Edit (with replace_all, string matching rules)
   - Glob (file pattern matching)
   - Grep (with regex, output modes, context lines)
   - Read (with offset, limit, pages for PDFs)
   - Skill (slash command invocation)
   - ToolSearch (deferred tool fetching)
   - Write (file creation)
   - Plus deferred tools (names only): CronCreate, CronDelete, CronList, EnterPlanMode, ExitPlanMode, EnterWorktree, ExitWorktree, NotebookEdit, TodoWrite, WebFetch, WebSearch, and ~20 MCP tools

3. **MCP server instructions:**
   - Figma MCP — Complete design-to-code workflow instructions, URL parsing rules
   - KnowledgeFlow — Session tracking, search tools
   - Gmail, Google Calendar, Notion — Auth tools

4. **Skill descriptions** — I can see ~70+ skills listed including all the gsd:* commands, knowledgeflow:*, etc.

5. **CLAUDE.md** — Project-specific instructions (GSD-generated)

6. **Memory** — MEMORY.md with 1 entry about the feedback preference

7. **Environment** — OS, shell, working directory path, model info

8. **Plan mode info** — References to the plan file

9. **VSCode extension context** — Instructions about markdown links, code references

10. **Auto memory system instructions** — Detailed instructions about when/how to save memories (~500+ tokens of memory management rules)

### Novel finding: The Agent tool description is ENORMOUS

The Agent tool schema includes a full description of every available subagent type. I count ~30 subagent types, each with a name and description. This alone is probably 2000-3000 tokens. It's re-sent on every request.

If you're not using subagents (most people don't use GSD or specialized agents), this is dead weight. But unlike MCP servers, you CAN'T disable built-in tool definitions.

### Novel finding: The auto-memory system instructions are heavy

I have detailed instructions about:
- When to save memories
- Types of memories (user, feedback, project, reference)
- How to format them
- When NOT to save
- How to verify memories before recommending
- The MEMORY.md index format

This is probably 800-1000 tokens of instructions that exist to support a feature most users don't actively use. But since it's built into the system prompt, it's not configurable.

---

## Probe 2: System Reminder Injection Frequency

Through this session, I've observed system reminders being injected at these points:

1. **Every user message** gets a `UserPromptSubmit hook` with a timestamp (~20 tokens)
2. **Date change notification** when the date rolled over (~15 tokens)
3. **TodoWrite reminders** — injected roughly every 3-4 assistant responses (~80 tokens each)
4. **File modification notices** — when the roadmapper updated REQUIREMENTS.md (~50-100 tokens)
5. **IDE context** — when you opened files in VS Code (~30 tokens each)

Over ~40 turns in this session, I estimate:
- Hook timestamps: 40 × 20 = 800 tokens
- TodoWrite reminders: ~10 × 80 = 800 tokens
- File notices: ~5 × 75 = 375 tokens
- IDE context: ~3 × 30 = 90 tokens
- **Total system reminder injection: ~2,065 tokens**

These are invisible to you, non-removable, and accumulate in conversation history.

---

## Probe 3: What Happens When I Call Multiple Tools

When I make parallel tool calls in a single response, I observe:
- All tools execute (seemingly in parallel on the host side)
- All results come back before my next turn
- The results are attached to my single assistant message

**The critical token implication:** If I read 3 files in parallel in one turn, the conversation gains 1 assistant message + 3 tool results. If I read them sequentially across 3 turns, the conversation gains 3 assistant messages + 3 tool results + 2 additional user prompt tokens (the system re-invoking me).

The parallel approach has fewer messages total, which means less overhead when the conversation is re-sent on future turns.

---

## Probe 4: The Extended Thinking Budget Mystery

I can't directly observe my thinking token count, but I can observe something about my behavior:

- When I get a simple, unambiguous task → I respond quickly
- When I get a complex, open-ended task → there's a noticeable delay before first output

The delay correlates with thinking. Based on community reports, the thinking budget for Opus is ~10K-32K tokens. This would make thinking THE dominant output cost for most turns.

**What triggers heavy thinking (from my observation):**
- Open-ended questions ("What's the best way to...")
- Complex code generation from scratch
- Multi-step reasoning tasks
- When I need to plan tool usage before executing

**What triggers light thinking:**
- Direct instructions ("Change X to Y")
- Simple file edits
- Pattern-following tasks ("Do the same thing for file B")
- Yes/no questions

**Novel technique: Frame requests as instructions, not questions.**

Instead of: "What do you think is the best approach for error handling here?"
Say: "Add try/catch with specific error types for DB and auth failures."

The first invites deliberation (heavy thinking). The second gives a clear directive (light thinking).

---

## Probe 5: My Verbosity Tendency Analysis

I've noticed a strong pattern in my own behavior — I default to verbose unless actively constrained. Specifically:

**My defaults without instruction:**
- Explain what I'm about to do (100-200 tokens)
- Do the thing (tool calls)
- Explain what I just did (200-400 tokens)
- Suggest what to do next (100-200 tokens)

**Total text overhead per action: 400-800 tokens of explanation around the actual work.**

**With "just do it" instruction:**
- Do the thing (tool calls)
- Brief confirmation (20-50 tokens)

**Total text overhead: 20-50 tokens. That's a 90-95% reduction in text output per action.**

And since these text tokens persist in context and get re-sent on every future turn, the savings compound massively.

**The most token-efficient CLAUDE.md instruction I can think of:**
```
Act, don't narrate. No preamble, no summary, no suggestions unless asked.
```

---
