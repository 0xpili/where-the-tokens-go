# Architecture: Claude Code Token Consumption

**Domain:** Claude Code token consumption structure and optimization leverage points
**Researched:** 2026-04-05
**Overall Confidence:** HIGH (sourced from official docs, interactive context window visualization, GitHub issues, and community measurements)

## Executive Summary

Claude Code's token consumption follows a layered architecture where every API request re-sends a growing context. The system is structured as: **fixed overhead (system prompt + tool schemas) + growing conversation (messages + tool results) + hidden costs (extended thinking + compaction + background processes)**. The critical insight is that token costs compound -- each turn re-processes everything that came before, making early decisions about what enters context the highest-leverage optimization point.

Total per-request input tokens = cached prefix (system prompt + tool schemas + CLAUDE.md) + conversation history (all prior messages and tool results) + new user message. Output tokens = extended thinking budget + visible response + tool call arguments. Every tool result feeds back into input tokens on the next turn.

---

## Component Architecture

### Layer 1: Fixed Overhead (Re-sent Every Request)

These components form a stable prefix that gets prompt-cached. They cost full price on the first request and 10% on subsequent requests within the cache TTL.

| Component | Tokens | Confidence | Notes |
|-----------|--------|------------|-------|
| **System prompt** (core instructions) | ~4,200 | HIGH | Behavioral instructions, security rules, output formatting. From official context window visualization. Conditionally assembled from 110+ instruction fragments. |
| **Built-in tool schemas** | ~11,600 | HIGH | 24+ tool definitions with names, descriptions, JSON parameter schemas. Each tool is a "small manual." From /context command measurements. |
| **Environment info** | ~280 | HIGH | Working directory, platform, shell, OS, git status. From visualization data. |
| **CLAUDE.md files** (all levels) | ~320-2,100+ | HIGH | Global (~320) + project (~1,800). Loaded every session. Every token here costs on every request. |
| **Auto memory (MEMORY.md)** | ~680 | HIGH | First 200 lines or 25KB. Claude's cross-session notes. |
| **Skill descriptions** | ~450 | MEDIUM | One-line descriptions of available skills. NOT re-injected after compaction. |
| **MCP tool names (deferred)** | ~120 | HIGH | Only names when tool search is enabled (default). Full schemas load on demand. |

**Total fixed overhead (minimal setup):** ~18,000-20,000 tokens
**Total fixed overhead (with MCP servers):** 25,000-50,000+ tokens

**Key measurement:** The /context command from a real session showed:
- System prompt: 6.2k tokens (0.6%)
- System tools: 11.6k tokens (1.2%)
- MCP tools: 1.2k active + 5.9k deferred (0.7%)
- Memory files: 3.3k tokens (0.3%)
- Skills: 333 tokens (0.0%)

**Confidence source:** Official context window interactive visualization at code.claude.com/docs/en/context-window provides exact token counts per component.

### Layer 2: MCP Server Overhead (Variable, Per-Server)

MCP tool definitions stack on top of the fixed overhead. With tool search enabled (default since 2025), only tool names are loaded upfront, and full schemas are loaded on demand.

| MCP Configuration | Additional Tokens | Confidence |
|-------------------|-------------------|------------|
| Lightweight server (5-10 tools) | 1,000-2,000 | HIGH |
| Medium server (10-15 tools) | 1,500-4,000 | HIGH |
| Heavy server (GitHub, Playwright) | 5,000-10,000+ | MEDIUM |
| Typical 4-server setup | ~7,000 | HIGH |
| Heavy 5+ server setup | 30,000-50,000+ | MEDIUM |

**Tool deferral behavior:** With `ENABLE_TOOL_SEARCH=auto` (default), the threshold triggers at 10% of context window. Setting `ENABLE_TOOL_SEARCH=auto:5` lowers to 5%, deferring more aggressively. Setting `ENABLE_TOOL_SEARCH=false` loads everything upfront.

Individual MCP tool examples (from /mcp output):
- Gmail create_draft: 820 tokens
- Gmail search_messages: 660 tokens
- Browser screenshot: 370 tokens

### Layer 3: Conversation History (Accumulating)

Every request re-sends the full conversation. This is where context compounding occurs.

| Component | Typical Token Cost | Accumulation Pattern |
|-----------|-------------------|---------------------|
| **User messages** | 40-200 per message | Additive (small) |
| **Claude's text responses** | 200-1,200 per response | Additive (moderate) |
| **File reads (Read tool)** | 1,100-2,400 per file | Additive (large -- file contents stay in history) |
| **Grep/search results** | 600 per search | Additive |
| **Bash command output** | 180-1,200+ per command | Additive (can be very large for test output) |
| **Edit tool results** | 400-600 per edit | Additive |
| **Hook output** | 100-120 per hook fire | Additive (enters via additionalContext field) |
| **Path-scoped rules** | 290-380 per rule triggered | Loaded when matching files are accessed |
| **Skill content** | Variable (full content on invocation) | Loaded once when skill is used |

**Compounding example from official visualization (single bug-fix task):**

| Action | Tokens Added | Cumulative |
|--------|-------------|------------|
| System overhead | ~8,000 | 8,000 |
| User prompt | 45 | 8,045 |
| Read auth.ts | 2,400 | 10,445 |
| Read tokens.ts | 1,100 | 11,545 |
| Rule: api-conventions.md | 380 | 11,925 |
| Read middleware.ts | 1,800 | 13,725 |
| Read auth.test.ts | 1,600 | 15,325 |
| Rule: testing.md | 290 | 15,615 |
| grep "refreshToken" | 600 | 16,215 |
| Claude's analysis | 800 | 17,015 |
| Edit auth.ts | 400 | 17,415 |
| Hook: prettier | 120 | 17,535 |
| Edit auth.test.ts | 600 | 18,135 |
| Hook: prettier | 100 | 18,235 |
| npm test output | 1,200 | 19,435 |
| Summary response | 400 | 19,835 |

That is one simple task consuming ~20K tokens. A follow-up question re-sends ALL of it plus new content.

**Real-world session accumulation:**
- Typical 1-hour session: 50,000-100,000 tokens of conversation history
- Five file reads across a session: ~10,000 tokens re-sent on every subsequent request
- Multi-segment session (with compaction): ~490K useful work tokens across ~645K total

### Layer 4: Extended Thinking (Hidden Output Tokens)

Extended thinking is enabled by default and is billed as output tokens. These tokens are invisible in the terminal but consume quota.

| Parameter | Value | Confidence |
|-----------|-------|------------|
| Default thinking budget | ~31,999 tokens per request | MEDIUM |
| Maximum thinking budget | 63,999 tokens (64K output models) | HIGH |
| Billing | Full thinking tokens as output tokens | HIGH |
| Persistence | Thinking blocks cached alongside other content in subsequent turns, counted as input tokens when read from cache | HIGH |

**Cost impact:** If thinking generates 10K tokens and the visible response is 500 tokens, you are billed for 10,500 output tokens. On Opus 4.6 at $25/MTok output, that single request's thinking costs ~$0.26.

**Control mechanisms:**
- `/effort` command to lower effort level
- `MAX_THINKING_TOKENS=8000` environment variable
- Disable thinking entirely in `/config`

### Layer 5: Compaction Mechanics

Compaction is the lossy summarization that keeps conversations within the context window.

| Parameter | Value | Confidence |
|-----------|-------|------------|
| Auto-compaction trigger | ~83.5% of context window | HIGH |
| Compaction buffer (reserved) | ~33,000 tokens (16.5% of 200K window) | HIGH |
| Usable context before compaction | ~167,000 tokens (200K window) | HIGH |
| Context freed per compaction | 60-70% | MEDIUM |
| Compaction summary size | 11,000-19,000 tokens | MEDIUM |
| Compaction cost per event | ~$0.22-$0.47 (Opus pricing) | MEDIUM |
| Override | `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (can only trigger earlier, not later) | HIGH |

**What survives compaction:**
- System prompt (exists outside conversation, always re-injected)
- CLAUDE.md content (always re-injected)
- High-level decisions and recent code changes
- Key code snippets

**What is lost:**
- Verbatim earlier exchanges
- Nuanced reasoning chains
- Specific variable names and exact error messages from early in session
- Skill descriptions (NOT re-injected after compaction)
- Detailed instructions from early conversation turns

**Compaction and caching interaction:** The compaction request reuses the identical prefix (system prompt + tools + CLAUDE.md). Only the conversation portion changes. This means the ~18K fixed prefix is served from cache ($0.009 on Opus) rather than reprocessed ($0.09 on Opus). After compaction, the new conversation must create a fresh cache entry.

### Layer 6: Prompt Caching Architecture

Prompt caching is the single most important cost optimization in Claude Code's architecture.

**How it works:**
1. The API checks if a prompt prefix up to a cache breakpoint matches a recent request
2. Cache hit: reuse the KV cache (90% cost reduction on those tokens)
3. Cache miss: process fully, then cache the prefix for future requests

**Cache structure in Claude Code:**

```
[Tools definitions] -----> breakpoint 1
[System prompt]     -----> breakpoint 2  
[Conversation msgs] -----> breakpoint 3 (moves forward each turn)
[New user message]  -----> not cached
```

**Cache invalidation hierarchy:**

| What Changes | Tools Cache | System Cache | Messages Cache |
|---|---|---|---|
| Tool definitions | INVALID | INVALID | INVALID |
| System prompt changes | OK | INVALID | INVALID |
| Conversation grows | OK | OK | NEW breakpoint |

**Cache TTLs:**
- 5-minute ephemeral (default): 1.25x base input price to write, 0.1x to read
- 1-hour extended: 2x base input price to write, 0.1x to read
- Cache refreshed at no additional cost on hit within TTL

**Pricing impact (Opus 4.6):**
| Token Type | Price/MTok |
|---|---|
| Base input | $5.00 |
| 5-min cache write | $6.25 |
| 1-hour cache write | $10.00 |
| Cache read | $0.50 (90% savings) |
| Output | $25.00 |

**Minimum cacheable tokens:** 4,096 (Opus 4.6), 2,048 (Sonnet 4.6)

**20-block lookback window:** The cache system checks at most 20 positions per breakpoint. For conversations growing beyond 20 blocks per turn, a second breakpoint closer to new content is needed to maintain cache hits.

### Layer 7: Subagent / Agent Tool Token Multiplication

The Agent tool spawns a subagent with its own isolated context window. This is both a token multiplier and a token optimization tool.

**What a subagent gets (its own context window):**
- Its own system prompt (~900 tokens, shorter than parent's)
- Project CLAUDE.md (own copy, ~1,800 tokens)
- MCP tools + skills (~970 tokens)
- Task prompt from parent (~120 tokens)
- Does NOT inherit: conversation history, parent's auto memory

**Token multiplication pattern:**
- Each subagent opens a full new context window
- All fixed overhead is duplicated (but shares cached prefix for efficiency)
- Multi-agent workflows: 4-7x more tokens than single-agent sessions
- Agent Teams (experimental): ~15x standard usage (~7x in plan mode)

**Token savings pattern (from official visualization):**
- Subagent reads 6,100 tokens of files in its own context
- Returns only 420-token summary to parent context
- Net savings: 5,680 tokens kept OUT of the main conversation
- The savings compound on every subsequent turn in the main session

**Recursion prevention:** Subagents cannot spawn other subagents by default (Agent tool excluded from their tool set).

### Layer 8: Background Token Usage

Claude Code consumes tokens even when you are not actively interacting.

| Background Process | Token Cost | Confidence |
|-------------------|------------|------------|
| Conversation summarization (for `--resume`) | Small | HIGH |
| Command processing (`/cost`, `/stats`) | Small | MEDIUM |
| AutoDream memory management (between sessions) | Small | MEDIUM |
| Total background cost per session | ~$0.04 | HIGH |

---

## Data Flow: How Tokens Accumulate Through a Conversation

### Session Startup (Before First Message)

```
Context Window (200K or 1M):
+-----------------------------------------------+
| System Prompt         ~4,200 tokens   [CACHED] |
| Tool Schemas         ~11,600 tokens   [CACHED] |
| Environment Info        ~280 tokens   [CACHED] |
| Auto Memory (MEMORY.md) ~680 tokens   [CACHED] |
| CLAUDE.md files       ~2,100 tokens   [CACHED] |
| Skill Descriptions      ~450 tokens   [CACHED] |
| MCP Tool Names          ~120 tokens   [CACHED] |
+-----------------------------------------------+
| TOTAL OVERHEAD:      ~19,430 tokens            |
| (+ MCP full schemas if loaded: +7K-50K)       |
+-----------------------------------------------+
| FREE SPACE: ~180,570 tokens (200K window)      |
| FREE SPACE: ~980,570 tokens (1M window)        |
+-----------------------------------------------+
| COMPACTION BUFFER:   ~33,000 tokens [RESERVED] |
+-----------------------------------------------+
```

### Turn 1: User Prompt + Claude's Agentic Work

```
API Request #1:
  INPUT: 19,430 (overhead) + 45 (user prompt) = 19,475 tokens
  Cached: ~19,430 (prefix hit, 90% discount)
  Fresh:  45 tokens (user message)

Claude works (multiple tool calls within single turn):
  Read file A:     +2,400 tokens (result stored in history)
  Read file B:     +1,100 tokens
  Grep search:       +600 tokens
  Edit file:         +400 tokens
  Test output:     +1,200 tokens
  Claude response:   +800 tokens (output tokens)
  Thinking:       +10,000 tokens (output tokens, invisible)

Context after Turn 1: 19,475 + 6,500 = ~25,975 input tokens
```

### Turn 2: Follow-up (Context Compounding)

```
API Request #2:
  INPUT: 19,430 (overhead, CACHED)
       + 6,545 (Turn 1 history: prompt + all tool results + response)
       +    40 (new user message)
       = 26,015 tokens

  Cached: ~19,430 (prefix) + potentially some of Turn 1 if within lookback window
  Fresh:  40 tokens minimum (new message)
```

### Turn N: Approaching Compaction

```
API Request at ~167K tokens (83.5% of 200K):
  INPUT: 19,430 (overhead, CACHED)
       + 147,570 (accumulated conversation history)
       = ~167,000 tokens

  AUTO-COMPACTION TRIGGERS:
    1. Sends entire conversation to model for summarization
    2. Summary generated: ~11,000-19,000 tokens
    3. Old messages dropped, replaced with summary
    4. Session continues with reduced context

  Context after compaction: 19,430 + ~15,000 (summary) = ~34,430 tokens
  Freed space: ~132,570 tokens
  Lost: Verbatim details, early reasoning, specific variable names
```

### Subagent Fork Pattern

```
Main Context (unchanged):
  +-- Accumulated conversation: ~80,000 tokens
  +-- Subagent call: +80 tokens (spawn request)
  +-- Subagent result: +420 tokens (summary returned)
  TOTAL ADDED TO MAIN: 500 tokens

Subagent Context (separate, temporary):
  +-- System prompt: ~900 tokens
  +-- CLAUDE.md: ~1,800 tokens
  +-- MCP/skills: ~970 tokens
  +-- Task prompt: ~120 tokens
  +-- File reads: ~6,100 tokens
  +-- Subagent's own thinking: ~10,000 output tokens
  TOTAL SUBAGENT: ~9,890 input + ~10,000+ output
  (All discarded when subagent completes)
```

---

## Key Leverage Points (Ranked by Impact)

### Tier 1: Highest Impact (save 30-60% of tokens)

| Leverage Point | Mechanism | Estimated Savings | Confidence |
|---|---|---|---|
| **Prompt caching prefix stability** | Keep tools + system prompt + CLAUDE.md stable to maximize cache hits. Any change invalidates downstream caches. | 90% reduction on ~18K+ tokens per request | HIGH |
| **Proactive context clearing (/clear between tasks)** | Stale context compounds. Clearing between unrelated tasks eliminates re-sending irrelevant history. | 50-80% reduction on accumulated conversation | HIGH |
| **Subagent delegation for research-heavy work** | File reads stay in subagent's context; only summary returns. Prevents 5-10K tokens per research task from entering main context. | 80-90% reduction on research/exploration tokens | HIGH |
| **MCP tool deferral (ENABLE_TOOL_SEARCH)** | Load only tool names, not full schemas. Default behavior, but tunable. | 5,000-40,000 tokens saved vs loading all schemas | HIGH |

### Tier 2: Significant Impact (save 10-30% of tokens)

| Leverage Point | Mechanism | Estimated Savings | Confidence |
|---|---|---|---|
| **Reduce CLAUDE.md size** | Every token in CLAUDE.md is re-sent on every request. Move reference content to skills. | 500-2,000 tokens per request (compounding) | HIGH |
| **Extended thinking budget control** | Lower `MAX_THINKING_TOKENS` or use `/effort` for simple tasks. Default ~32K output tokens per request. | 10,000-25,000 output tokens per request | HIGH |
| **Model selection (Sonnet vs Opus)** | Sonnet is 40% cheaper per input token and has smaller minimum cache threshold (2,048 vs 4,096). | 40% cost reduction, roughly equivalent capability for most coding tasks | HIGH |
| **Disable unused MCP servers** | Each idle server still contributes tool names and potentially full schemas to context. | 1,000-10,000 tokens per disabled server | HIGH |
| **Hooks for preprocessing** | Filter large outputs (logs, test results) before they enter context. | 90%+ reduction on specific tool outputs (e.g., 10K log -> 200 token grep) | MEDIUM |

### Tier 3: Moderate Impact (save 5-15% of tokens)

| Leverage Point | Mechanism | Estimated Savings | Confidence |
|---|---|---|---|
| **Specific prompts** | "Fix auth.ts" reads 1 file; "improve the codebase" reads 20. Each file read persists in context. | 5,000-20,000 tokens per task | MEDIUM |
| **Path-scoped rules instead of CLAUDE.md** | Rules only load when matching files are accessed, not on every request. | 200-500 tokens per rule moved out of CLAUDE.md | HIGH |
| **Skills instead of CLAUDE.md for reference content** | Skills load on-demand; CLAUDE.md loads every request. | Variable, depends on content volume | HIGH |
| **Early compaction (/compact with focus)** | Manual compaction while there's headroom produces better summaries than auto-compaction at 83.5%. | Better summary quality = fewer correction loops | MEDIUM |
| **CLI tools over MCP** | `gh`, `aws`, `gcloud` add zero per-tool token overhead vs MCP equivalents. | 1,000-10,000 tokens per replaced MCP server | HIGH |

### Tier 4: Minor but Cumulative Impact

| Leverage Point | Mechanism | Estimated Savings | Confidence |
|---|---|---|---|
| **Compact instructions in CLAUDE.md** | Guide what compaction preserves. "When compacting, focus on X" | Indirect: better compaction = fewer lost-context loops | MEDIUM |
| **disable-model-invocation on manual skills** | Skill descriptions stay out of context entirely until invoked. | ~450 tokens of skill listing saved per request | HIGH |
| **Shorter output instructions** | "cave talk" and similar terse-response prompts reduce output tokens. | 20-50% output token reduction per response | LOW |
| **Code intelligence plugins (LSP)** | One go-to-definition replaces grep + reading 3 candidate files. | 2,000-5,000 tokens per navigation action | MEDIUM |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Letting Context Rot
**What:** Working on multiple unrelated tasks in one session without clearing.
**Why bad:** Each new task's context compounds on stale history. By task 3, you're re-sending 100K+ tokens of irrelevant context on every request.
**Instead:** `/clear` between tasks. Use `/rename` first if you want to resume later.

### Anti-Pattern 2: Large CLAUDE.md as Knowledge Base
**What:** Putting API docs, style guides, architecture descriptions all in CLAUDE.md.
**Why bad:** Every line is re-sent on every request, whether relevant or not. A 500-line CLAUDE.md costs ~5,000 tokens per request.
**Instead:** Keep CLAUDE.md under 200 lines. Move reference content to skills (load on demand) or path-scoped rules (load when relevant files are accessed).

### Anti-Pattern 3: Installing MCP Servers "Just in Case"
**What:** Configuring 5+ MCP servers for potential future use.
**Why bad:** Even with deferral, tool names consume context. Heavy servers can add 10K+ tokens each when their tools are actually used.
**Instead:** Enable MCP servers per-session as needed. Prefer CLI tools (`gh`, `aws`) which have zero per-tool token overhead.

### Anti-Pattern 4: Vague Research Prompts in Main Context
**What:** "Read through the codebase and understand how auth works" in your main session.
**Why bad:** Claude reads 10-20 files. Each file read (1-3K tokens) stays in your conversation history permanently (until compaction).
**Instead:** Delegate research to a subagent. It reads the files in its own context and returns only a summary.

### Anti-Pattern 5: Ignoring Extended Thinking Budget
**What:** Using default ~32K thinking budget for simple tasks like "rename this variable."
**Why bad:** Claude may use 10-20K output tokens for thinking on a task that needs 500 tokens of visible output.
**Instead:** Use `/effort low` for simple tasks. Set `MAX_THINKING_TOKENS=8000` for routine work.

---

## Scalability Considerations

| Context Window | Total | Fixed Overhead | Usable (pre-compaction) | Compaction Buffer |
|---|---|---|---|---|
| 200K (standard) | 200,000 | ~19,430 | ~147,570 | ~33,000 |
| 1M (GA since March 2026) | 1,000,000 | ~19,430 | ~797,570 | ~183,000 (estimated) |

The 1M context window (available on Opus 4.6 and Sonnet 4.6 at no pricing premium) dramatically changes the compaction dynamics. Sessions that previously required 3-4 compaction cycles can run to completion without any compaction, preserving all detail. However, the token cost per request scales with history size -- a 500K context request costs 5x what a 100K request costs (minus caching).

| Concern | Short Session (10 turns) | Medium Session (50 turns) | Long Session (200+ turns) |
|---|---|---|---|
| Context size | ~30-50K | ~100-167K (hits compaction on 200K) | Multiple compaction cycles or requires 1M window |
| Cache efficiency | High (stable prefix) | High (prefix cached, growing conversation) | Medium (compaction resets conversation cache) |
| Information loss | None | Low (if manual compaction used) | High (multiple lossy summaries) |
| Subagent value | Low (context not scarce) | Medium | Critical (preserves main context) |

---

## Sources

### Official Documentation (HIGH confidence)
- [How Claude Code Works](https://code.claude.com/docs/en/how-claude-code-works) - Agentic loop, tools, context window
- [Manage Costs Effectively](https://code.claude.com/docs/en/costs) - Token usage patterns, optimization strategies
- [Explore the Context Window](https://code.claude.com/docs/en/context-window) - Interactive visualization with exact token counts per component
- [Extend Claude Code (Features Overview)](https://code.claude.com/docs/en/features-overview) - Context costs by feature
- [Tools Reference](https://code.claude.com/docs/en/tools-reference) - Complete tool list
- [Create Custom Subagents](https://code.claude.com/docs/en/sub-agents) - Subagent architecture and context isolation
- [Compaction API](https://platform.claude.com/docs/en/build-with-claude/compaction) - Server-side compaction parameters
- [Prompt Caching API](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) - Cache mechanics, TTLs, invalidation
- [Building with Extended Thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) - Thinking budget and billing

### Community Measurements (MEDIUM confidence)
- [Where Do Your Claude Code Tokens Actually Go?](https://dev.to/slima4/where-do-your-claude-code-tokens-actually-go-we-traced-every-single-one-423e) - Multi-segment session analysis: ~14,328 token system overhead, 76% efficiency, 166.5K wasted of 644.8K total
- [Claude Code /context Command Token Breakdown](https://www.jdhodges.com/blog/claude-code-context-slash-command-token-usage/) - Real session measurement: 6.2K system prompt + 11.6K system tools + 1.2K MCP + 3.3K memory = ~22.3K overhead
- [Context Buffer Management](https://claudefa.st/blog/guide/mechanics/context-buffer-management) - Buffer reduction from 45K to 33K tokens, compaction trigger at 83.5%
- [MCP Server Token Costs Breakdown](https://www.jdhodges.com/blog/claude-code-mcp-server-token-costs/) - Per-server token measurements

### GitHub Issues (MEDIUM confidence)
- [Issue #3406: Built-in tools + MCP descriptions 10-20K overhead](https://github.com/anthropics/claude-code/issues/3406) - Measurement: 10,600 tokens for built-in tools alone, ~15K with 4 MCP servers
- [Issue #26158: Move behavioral instructions out of tool definitions](https://github.com/anthropics/claude-code/issues/26158) - ~16.5K tokens of tool definitions, significant portion is behavioral instructions not schema
- [Issue #11364: Lazy-load MCP tool definitions](https://github.com/anthropics/claude-code/issues/11364) - Feature request for deferred loading
- [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) - Extracted 110+ system prompt strings, 24 built-in tool descriptions, updated for v2.1.92
