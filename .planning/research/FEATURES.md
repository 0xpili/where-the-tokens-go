# Feature Landscape: Claude Code Token Optimization Techniques

**Domain:** LLM token consumption reduction for Claude Code
**Researched:** 2026-04-05
**Overall confidence:** HIGH (corroborated across official docs, community experiments, and multiple independent sources)

---

## Table Stakes

Features/techniques that any serious Claude Code user should know. Missing these means leaving 30-50% of token budget on the table.

### TS-1: Context Clearing Between Tasks (`/clear`)

| Attribute | Detail |
|-----------|--------|
| **What** | Use `/clear` to reset context when switching to unrelated work |
| **Why Expected** | Every message re-sends the entire conversation history. Stale context from Task A wastes tokens on every subsequent message about Task B. Cost compounds, not adds. |
| **Complexity** | Low |
| **Measured Impact** | Prevents exponential context growth; exact savings vary by session length |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official docs (code.claude.com/docs/en/costs) |

### TS-2: Strategic Compaction (`/compact`)

| Attribute | Detail |
|-----------|--------|
| **What** | Manually trigger conversation summarization at logical breakpoints, ideally at ~60% context utilization rather than waiting for auto-compaction at ~95% |
| **Why Expected** | Auto-compaction at 95% capacity produces worse summaries because the model has less headroom for reasoning. Manual compaction at 60% preserves more nuance. |
| **Complexity** | Low |
| **Measured Impact** | A 400K-token conversation typically compresses to 50K-80K tokens. Custom compaction instructions (e.g., `/compact Focus on code samples and API usage`) improve what survives. |
| **Dependencies** | TS-9 (CLAUDE.md compaction instructions) |
| **Source confidence** | HIGH -- Official docs + multiple community measurements |

### TS-3: Model Selection and Routing

| Attribute | Detail |
|-----------|--------|
| **What** | Use Sonnet for ~80% of tasks (routine implementation, code generation). Reserve Opus for complex architectural decisions and multi-step reasoning. Use Haiku for subagent tasks. Switch with `/model`. |
| **Why Expected** | Opus costs ~5x more per token than Sonnet. Most coding tasks don't need Opus-level reasoning. |
| **Complexity** | Low |
| **Measured Impact** | ~20% cost reduction from model selection alone (source: WentuoAI guide) |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official recommendation |

### TS-4: Suppressing Output Verbosity

| Attribute | Detail |
|-----------|--------|
| **What** | Direct Claude to skip preambles, explanations, and pleasantries. Instructions like "No explanations, just the code" or "Skip the preamble" in prompts or CLAUDE.md. |
| **Why Expected** | By default Claude explains its reasoning in detail. This is helpful when learning but expensive when shipping. |
| **Complexity** | Low |
| **Measured Impact** | 30-50% reduction in output tokens on coding tasks. The claude-token-efficient CLAUDE.md repo measured ~63% output reduction (120 words to 30 words) with identical code quality. |
| **Dependencies** | TS-9 (CLAUDE.md configuration) |
| **Source confidence** | HIGH -- Multiple independent measurements agree |

### TS-5: `.claudeignore` for File Exclusion

| Attribute | Detail |
|-----------|--------|
| **What** | Exclude build artifacts, dependencies, caches, media files, and lock files from Claude's context. Works like `.gitignore`. |
| **Why Expected** | Without it, Claude may read `node_modules/`, `.next/`, `dist/`, lock files, etc. when exploring a codebase. |
| **Complexity** | Low |
| **Measured Impact** | 30-40% context reduction in a typical Next.js project from excluding `.next/` alone |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official feature, widely measured |

### TS-6: Specific Prompts Over Vague Requests

| Attribute | Detail |
|-----------|--------|
| **What** | "Add input validation to the login function in auth.ts" beats "improve this codebase." Include file paths, line numbers, function names. Answer 5W1H (What, Where, How, When, Who) before sending. |
| **Why Expected** | Vague requests trigger broad scanning (reading many files). Specific requests let Claude work efficiently with minimal file reads. |
| **Complexity** | Low |
| **Measured Impact** | 15-25% reduction in total tokens (60-80% reduction in tool result tokens specifically) |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official best practice + community consensus |

### TS-7: Plan Mode (Shift+Tab)

| Attribute | Detail |
|-----------|--------|
| **What** | Toggle plan mode before implementation. Claude explores the codebase and proposes an approach for approval before writing code. |
| **Why Expected** | Eliminates the biggest source of token waste: trial-and-error execution. Getting the plan wrong and rewriting costs far more than getting the plan right first. |
| **Complexity** | Low |
| **Measured Impact** | 20-30% token reduction by preventing expensive re-work |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official feature, widely recommended |

### TS-8: Escape and Rewind for Course Correction

| Attribute | Detail |
|-----------|--------|
| **What** | Single Escape stops current response. Double Escape (or `/rewind`) opens rewind menu to restore a previous checkpoint (code + conversation state). |
| **Why Expected** | When Claude heads in the wrong direction, every additional token spent is waste. Stopping early and rewinding is always cheaper than letting it finish and then correcting. |
| **Complexity** | Low |
| **Measured Impact** | Prevents entire wrong-direction responses (potentially thousands of tokens per occurrence). Rewind itself costs zero tokens. |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official feature (checkpointing docs) |

### TS-9: Lean CLAUDE.md Configuration

| Attribute | Detail |
|-----------|--------|
| **What** | Keep CLAUDE.md under 200 lines / 2,000 tokens. Include only: project summary, tech stack, code style conventions, essential rules. Move detailed workflows to Skills or separate docs. |
| **Why Expected** | CLAUDE.md loads as part of the system prompt on every single message. Every token in CLAUDE.md is a tax on every interaction. If CLAUDE.md exceeds 10-15% of context, it needs trimming. |
| **Complexity** | Low |
| **Measured Impact** | 5-10% reduction per conversation. One optimization case reduced startup tokens from 2,100 to 800 (62% reduction in overhead). |
| **Dependencies** | D-7 (Skills as alternative) |
| **Source confidence** | HIGH -- Official recommendation + multiple community guides |

### TS-10: Disable Unused MCP Servers

| Attribute | Detail |
|-----------|--------|
| **What** | Run `/mcp` to see configured servers, disable any not actively used. Audit with `/context` to see what consumes space. |
| **Why Expected** | Each MCP server injects tool definitions into context. A typical server with 10-15 tools adds 1,500-4,000 tokens per turn. Multiple servers can consume 18K+ tokens before you type a word. |
| **Complexity** | Low |
| **Measured Impact** | 5-10% overall reduction. One user recovered 31.7K tokens (from 49% to 34% context usage) by addressing MCP overhead. |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official docs + MindStudio measurements |

### TS-11: Prefer CLI Tools Over MCP Servers

| Attribute | Detail |
|-----------|--------|
| **What** | Use `gh` instead of GitHub MCP, `aws` instead of AWS MCP, `gcloud` instead of GCP MCP. CLI tools run via Bash and add zero per-tool schema overhead. |
| **Why Expected** | MCP servers inject full tool schemas. CLI tools are invoked via Bash with no schema overhead. They're both faster and cheaper. |
| **Complexity** | Low |
| **Measured Impact** | Eliminates 1,500-8,000 tokens of MCP overhead per server replaced |
| **Dependencies** | TS-10 |
| **Source confidence** | HIGH -- Official recommendation (code.claude.com/docs/en/costs) |

### TS-12: Extended Thinking Budget Control

| Attribute | Detail |
|-----------|--------|
| **What** | Reduce extended thinking for simple tasks with `/effort` or `MAX_THINKING_TOKENS=8000`. Thinking tokens are billed as output tokens. Default budgets can be tens of thousands of tokens per request. |
| **Why Expected** | Extended thinking is enabled by default and significantly improves complex tasks, but for simple edits or routine work, the thinking overhead is pure waste. |
| **Complexity** | Low |
| **Measured Impact** | ~5% savings per conversation turn from effort level adjustment. Thinking budgets can be 10K-32K+ tokens per request. |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official docs |

---

## Differentiators

Novel, creative, or surprising techniques that go beyond common knowledge. These separate expert users from casual ones.

### D-1: Subagent Delegation for Context Isolation

| Attribute | Detail |
|-----------|--------|
| **What** | Delegate verbose operations (test runs, log processing, documentation fetching, dependency audits) to subagents. Verbose output stays in the subagent's context; only a summary returns to main conversation. |
| **Why Valuable** | A test suite run might generate 10,000-50,000 tokens of output. Subagent isolation keeps this out of your main context window. The subagent can use a cheaper model (Haiku/Sonnet) while main runs Opus. |
| **Complexity** | Medium |
| **Measured Impact** | Prevents 10K-50K tokens from polluting primary conversation per verbose operation |
| **When Effective** | 3+ file explorations, cross-file searches, test execution. NOT effective for 1-2 file reads (startup overhead outweighs savings). |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official feature + documented patterns |

### D-2: Tiered Documentation Architecture

| Attribute | Detail |
|-----------|--------|
| **What** | Structure project docs in three tiers: Tier 1 (Always Loaded, <800 tokens) = project name, critical rules, quick start; Tier 2 (On Demand, 500-1,500 tokens) = component docs, API refs, loaded via Skills; Tier 3 (Never Loaded, 0 tokens) = complete specs, changelogs, accessed via links only. |
| **Why Valuable** | Most projects dump everything into CLAUDE.md. Tiered architecture means Claude only pays for context that's relevant to the current task. |
| **Complexity** | Medium |
| **Measured Impact** | 60% reduction in startup tokens. One measurement: startup tokens from 2,100 to 800, relevant context from ~30% to ~85%. |
| **Dependencies** | TS-9 (lean CLAUDE.md), D-7 (Skills) |
| **Source confidence** | MEDIUM -- Single detailed article (Jpranav, Medium) with reproducible methodology |

### D-3: Read-Once Hook (Prevent Redundant File Reads)

| Attribute | Detail |
|-----------|--------|
| **What** | A PreToolUse hook that tracks file reads within a session and blocks re-reads of unchanged files. Optionally returns diffs for changed files instead of full content. Cache entries expire after 20 minutes (configurable) to handle compaction. |
| **Why Valuable** | Claude frequently re-reads files it has already loaded, especially during iterative development. A 200-line file costs ~2,000 tokens every time it's read. If only 3 lines changed, reading only the diff costs ~30 tokens. |
| **Complexity** | Medium |
| **Measured Impact** | 60-90% reduction in Read tool token usage. Per iteration: ~30 tokens instead of ~2,000 (80-95% reduction). Data from 107 sessions shows consistent savings. |
| **Dependencies** | Requires hook infrastructure (settings.json configuration) |
| **Source confidence** | HIGH -- Open-source implementation with measured results across 107 sessions |

### D-4: Output Preprocessing Hooks (Filter Before Claude Sees It)

| Attribute | Detail |
|-----------|--------|
| **What** | Custom hooks that filter tool output before it enters Claude's context. Example: a PreToolUse hook that modifies test runner commands to pipe through `grep -A 5 -E '(FAIL\|ERROR)'` and `head -100`, so Claude only sees failures instead of full test output. |
| **Why Valuable** | A full test suite output might be 10,000+ tokens. Filtering to failures-only could be 200 tokens. This is preprocessing that Claude doesn't need to do itself. |
| **Complexity** | Medium |
| **Measured Impact** | Reduces context from "tens of thousands of tokens to hundreds" (official docs) |
| **Dependencies** | Requires hook infrastructure |
| **Source confidence** | HIGH -- Official recommendation with example code (code.claude.com/docs/en/costs) |

### D-5: Session Handoff Documents

| Attribute | Detail |
|-----------|--------|
| **What** | Before ending a session, request a structured summary (under 300 words): decisions made, work completed, outstanding issues, next steps. Start the next session by pasting this handoff instead of re-explaining everything. |
| **Why Valuable** | Reconstructs useful context in a fraction of the tokens needed for re-explanation. A full conversation history might be 100K tokens; a handoff document is 500 tokens with 80% of the useful context. |
| **Complexity** | Low |
| **Measured Impact** | ~45K tokens saved per session transition (tokens that would otherwise go to auto-compaction or re-explanation) |
| **Dependencies** | None |
| **Source confidence** | MEDIUM -- Multiple community sources, no controlled measurements |

### D-6: LSP / Code Intelligence Plugins

| Attribute | Detail |
|-----------|--------|
| **What** | Install language server plugins for your programming language. Gives Claude precise symbol navigation (go-to-definition, find-references, hover info) instead of text-based search. |
| **Why Valuable** | A grep-based reference search might scan 10-15 files (~10K tokens). LSP `findReferences` returns exact matches in ~500 tokens. Also provides automatic type error reporting after edits without running a compiler. |
| **Complexity** | Medium |
| **Measured Impact** | 75% fewer tokens than grep-style analysis. 900x speed improvement (50ms vs 45 seconds). |
| **Dependencies** | Language-specific LSP server must be available |
| **Source confidence** | HIGH -- Official feature (Claude Code v2.0.74+), multiple independent measurements |

### D-7: Skills for On-Demand Context Loading

| Attribute | Detail |
|-----------|--------|
| **What** | Move specialized instructions (PR review protocols, database migration guides, deployment workflows) from CLAUDE.md to Skills. Skills load only when invoked, not on every message. |
| **Why Valuable** | CLAUDE.md loads on every interaction. Skills load on-demand. If you have 5 specialized workflows at 1,000 tokens each, that's 5,000 tokens taxed every message if in CLAUDE.md, vs 1,000 tokens only when relevant if in Skills. |
| **Complexity** | Medium |
| **Measured Impact** | One framework recovered ~15,000 tokens per session (82% improvement) by moving from CLAUDE.md to progressive skill loading. Another measurement showed 54% initial context reduction using lazy-loaded skills. |
| **Dependencies** | TS-9 (lean CLAUDE.md) |
| **Source confidence** | HIGH -- Official recommendation + quantified case study (John Lindquist gist) |

### D-8: Edit/Rewind Instead of Follow-Up Corrections

| Attribute | Detail |
|-----------|--------|
| **What** | When Claude's response is slightly wrong, edit your original message and regenerate instead of sending a follow-up correction. The old exchange disappears from history entirely. |
| **Why Valuable** | Follow-up corrections stack onto conversation history permanently. Claude re-reads all of it on every subsequent message. Edits replace the bad exchange, keeping token count flat. |
| **Complexity** | Low |
| **Measured Impact** | Claims of 80-90% reduction over long sessions. This is likely overstated in isolation, but the principle is sound: each unnecessary turn adds to every future turn's cost. |
| **Dependencies** | None |
| **Source confidence** | MEDIUM -- Community consensus, specific percentage claims are likely exaggerated |

### D-9: MCP Tool Consolidation and Description Trimming

| Attribute | Detail |
|-----------|--------|
| **What** | For custom MCP servers: consolidate similar tools into fewer parameterized tools, and aggressively trim tool descriptions. Example: 4 web search tools become 1 with a `provider` parameter. Trim descriptions from 87 tokens to 12 tokens. |
| **Why Valuable** | MCP tool schemas are included in every message. Fewer tools with shorter descriptions = less overhead per turn. |
| **Complexity** | Medium-High (requires modifying MCP servers) |
| **Measured Impact** | Measured 60% reduction in MCP context usage (14,214 to 5,663 tokens) by consolidating 20 tools into 8 with trimmed descriptions. Saved 8,551 tokens per turn. |
| **Dependencies** | TS-10 (MCP awareness) |
| **Source confidence** | HIGH -- Detailed measurement by Scott Spence with before/after numbers |

### D-10: Session-Start Hooks for Dynamic Context

| Attribute | Detail |
|-----------|--------|
| **What** | Use `.claude/hooks/session-start.sh` to dynamically inject context based on project state (git branch, database connectivity, directory context) rather than static CLAUDE.md docs. |
| **Why Valuable** | Static documentation includes everything regardless of current task. Dynamic hooks can inject only what's relevant to the current working context (e.g., different docs for feature branches vs main). |
| **Complexity** | Medium |
| **Measured Impact** | Part of the tiered documentation strategy; contributes to the 60% startup token reduction |
| **Dependencies** | D-2 (tiered documentation) |
| **Source confidence** | MEDIUM -- Single detailed source, compelling approach but limited independent validation |

### D-11: Custom Compaction Instructions in CLAUDE.md

| Attribute | Detail |
|-----------|--------|
| **What** | Add explicit compaction preservation rules to CLAUDE.md: "When compacting, always preserve the full list of modified files, test commands, architectural decisions, and user preferences." |
| **Why Valuable** | Default compaction can lose critical context: user preferences, repeated error warnings, architectural decisions. Lost context leads to repeated mistakes (one documented case: 70K tokens wasted rebuilding a feature that had already failed 3 times). |
| **Complexity** | Low |
| **Measured Impact** | Prevents 70K+ token waste per repeated mistake. The language-switching bug (Pattern 6) adds 20% overhead per message. |
| **Dependencies** | TS-2 (compaction), TS-9 (CLAUDE.md) |
| **Source confidence** | HIGH -- Documented in community issue #13579 with specific measurements |

### D-12: Reference by Line Number, Not Re-Pasting

| Attribute | Detail |
|-----------|--------|
| **What** | Say "In `auth.ts`, lines 42-58" instead of pasting the code block again. Claude already has the file in context from a prior read. |
| **Why Valuable** | Re-pasting code that's already in context doubles the token cost for that content. Line references cost ~20 tokens; re-pasting 50 lines costs ~500 tokens. |
| **Complexity** | Low |
| **Measured Impact** | Eliminates redundant token consumption proportional to code block size |
| **Dependencies** | None |
| **Source confidence** | MEDIUM -- Community best practice, logically sound |

### D-13: Prompt Caching Awareness (Prefix Stability)

| Attribute | Detail |
|-----------|--------|
| **What** | Understand that Claude Code uses prefix-based prompt caching automatically. Static content (system prompt, tool definitions, CLAUDE.md) at the start of the request is cached. Changes anywhere in the prefix invalidate everything after it. By the 20th turn, 95%+ of input tokens are served from cache. |
| **Why Valuable** | While users cannot directly control caching, understanding it informs decisions: keeping CLAUDE.md stable (not editing mid-session), minimizing MCP server changes mid-conversation, and understanding that longer conversations actually become cheaper per-turn due to caching. |
| **Complexity** | Low (awareness), Medium (acting on it) |
| **Measured Impact** | Without caching, a long Opus session can cost $50-100 in input tokens. With caching, $10-19. Cache hit rates of 95%+ after 20 turns. |
| **Dependencies** | None |
| **Source confidence** | HIGH -- Official documentation + Thariq (Claude Code builder) confirmation |

### D-14: Incremental Test-Then-Continue Workflow

| Attribute | Detail |
|-----------|--------|
| **What** | Write one file/module, test it immediately, then continue to the next. Don't generate all code first and test at the end. |
| **Why Valuable** | Building-without-testing was measured as the third most expensive token-wasting pattern. 34 modules generated then tested = 124K tokens wasted when nothing loads. Incremental testing catches issues at ~2K tokens instead of ~124K. |
| **Complexity** | Low (habit change) |
| **Measured Impact** | 92% potential savings on affected workflows (124K tokens waste documented) |
| **Dependencies** | TS-7 (plan mode) |
| **Source confidence** | HIGH -- Documented in community issue #13579 with measurements across 20+ sessions |

### D-15: "Cave Talk" / Caveman Response Style

| Attribute | Detail |
|-----------|--------|
| **What** | Instruct Claude to respond in extremely terse language: "Me talk short. No explain. Tool first. Result first." Originally went viral as a 16-year-old's discovery. Available as a Claude Code skill (JuliusBrussee/caveman). |
| **Why Valuable** | Dramatically reduces output verbosity. "I executed the web search tool" (8 tokens) becomes "Tool work" (2 tokens). |
| **Complexity** | Low |
| **Measured Impact** | Claims of 75% output token reduction. However, effectiveness is debated: the caveman prompt itself adds ~50+ input tokens per conversation, and agent tool-call turns (which are the majority of tokens) are unaffected by response style. Real-world savings may be much lower than headline numbers suggest. |
| **Dependencies** | None |
| **Source confidence** | MEDIUM -- Viral claim with some contradicting evidence. Dickson Tsai (Anthropic) tested and found "agent turns far outweigh the final output." |

---

## Anti-Features

Things that seem like they would save tokens but actually don't work, hurt quality, or cost more than they save.

### AF-1: Massive CLAUDE.md as "One-Time Context Loading"

| Anti-Feature | Detail |
|--------------|--------|
| **What it looks like** | "If I put everything in CLAUDE.md, Claude never needs to ask or explore!" |
| **Why it fails** | CLAUDE.md loads into every single message. A 5,000-token CLAUDE.md costs 5,000 tokens on every turn. Over a 50-turn conversation, that's 250,000 tokens of overhead. Additionally, research suggests models attend less reliably to information buried in very long contexts, so stuffing the window can actively reduce output quality. |
| **What to do instead** | Keep CLAUDE.md under 200 lines. Move detailed workflows to Skills (D-7) or tiered docs (D-2). |
| **Source confidence** | HIGH |

### AF-2: Loading Maximum Context Upfront

| Anti-Feature | Detail |
|--------------|--------|
| **What it looks like** | "Let me paste the entire codebase / all related files so Claude has full context!" |
| **Why it fails** | Large file inclusions consume tokens that could be used for conversation and output. They dilute Claude's attention across irrelevant content. The "lost in the middle" phenomenon means information in the middle of very long contexts is attended to less reliably. |
| **What to do instead** | Let Claude explore on-demand via tools. Provide file paths and let Claude read only what's needed. Use `.claudeignore` for irrelevant content. |
| **Source confidence** | HIGH |

### AF-3: Dozens of MCP Servers "Just In Case"

| Anti-Feature | Detail |
|--------------|--------|
| **What it looks like** | "I'll connect every useful MCP server so Claude can do anything!" |
| **Why it fails** | Even with deferred tool definitions, each MCP server adds overhead. 20K+ tokens of MCP overhead means only 20K tokens left for actual work before context is "cooked." Every tool schema is in every message. Adding one MCP tool can invalidate the prompt cache for the entire conversation. |
| **What to do instead** | Project-level MCP configs. Disable servers not needed for current task. Prefer CLI tools. Consolidate tools where possible (D-9). |
| **Source confidence** | HIGH |

### AF-4: Parallel Agent Swarms Without Coordination

| Anti-Feature | Detail |
|--------------|--------|
| **What it looks like** | "I'll spawn 7 agents to work in parallel for maximum speed!" |
| **Why it fails** | Without coordination, agents duplicate work, create merge conflicts, and produce unusable code. The #2 most expensive token-wasting pattern: 7 agents produced 9,339 lines of unusable code for 410K tokens. Sequential single-agent approach would have cost 29K tokens. |
| **What to do instead** | Use 1 agent sequentially > 7 agents in parallel. If parallelizing, ensure zero file overlap and independent domains. Test after each module. |
| **Source confidence** | HIGH -- Documented as 300K tokens wasted (93% potential savings) |

### AF-5: Over-Compacting / Compacting Too Aggressively

| Anti-Feature | Detail |
|--------------|--------|
| **What it looks like** | "I'll compact every few turns to keep context minimal!" |
| **Why it fails** | Each compaction loses nuance. User preferences, repeated error warnings, and architectural decisions get lost. One documented case: user warned "WebSocket failed 3x, don't build!" across 50 sessions. After compaction, Claude rebuilt WebSocket -- wasting 70K tokens on the same mistake. Also, compaction itself costs tokens (the summarization request). |
| **What to do instead** | Compact at ~60% utilization, not constantly. Use custom compaction instructions (D-11) to preserve critical context. Put persistent rules in CLAUDE.md (survives all compaction). |
| **Source confidence** | HIGH |

### AF-6: Caveman Prompts for Agent-Heavy Workflows

| Anti-Feature | Detail |
|--------------|--------|
| **What it looks like** | "Cave talk saves 75% of tokens! I'll use it everywhere!" |
| **Why it fails** | The viral 75% claim applies only to Claude's text responses. In Claude Code, the majority of tokens are tool calls, file reads, and tool results -- none of which are affected by response style. The caveman system prompt itself adds ~50+ input tokens per message. For agent-heavy workflows (which is most Claude Code usage), the savings on output text are dwarfed by tool token consumption. |
| **What to do instead** | Use output verbosity suppression (TS-4) for direct, professional conciseness. Focus optimization efforts on context management and tool efficiency, which is where the real token volume lives. |
| **Source confidence** | MEDIUM -- Contradicting evidence between viral claims and Anthropic engineer testing |

### AF-7: Requesting Full File Rewrites for Small Changes

| Anti-Feature | Detail |
|--------------|--------|
| **What it looks like** | Not explicitly requesting it, but letting Claude default to full file output when only a few lines changed. |
| **Why it fails** | For a 300-line file where 15 lines change, full rewrite outputs all 300 lines. Diff-style output uses ~5% of those tokens. The Edit tool uses shorter old_string anchors. Write tool outputs the entire file. |
| **What to do instead** | Claude Code's Edit tool is already diff-based. Ensure CLAUDE.md instructs "Avoid full file rewrites when partial changes work" and "Use targeted edits." |
| **Source confidence** | HIGH |

### AF-8: Single-Query Verbosity Reduction (Net Token Loss)

| Anti-Feature | Detail |
|--------------|--------|
| **What it looks like** | "I'll install a token-efficient CLAUDE.md for every project, even one-off questions!" |
| **Why it fails** | The CLAUDE.md file itself adds input tokens per message. For single queries or very short sessions, the overhead of the efficiency instructions exceeds the savings on output. The break-even point requires multiple interactions with significant output. |
| **What to do instead** | Only use verbosity-reduction CLAUDE.md configs for high-output-volume workflows. For quick questions, the overhead is net negative. |
| **Source confidence** | MEDIUM -- Noted in claude-token-efficient repo README |

### AF-9: Vague "Brevity" as Optimization

| Anti-Feature | Detail |
|--------------|--------|
| **What it looks like** | Sending very short, vague prompts thinking "fewer input tokens = optimization." E.g., "make this better." |
| **Why it fails** | Vague prompts trigger broad scanning, clarification questions, and speculative implementations. "Make this better" costs more total tokens than "Add input validation to the login function in auth.ts, lines 42-58" because the latter requires zero exploration. |
| **What to do instead** | Invest tokens in specific, detailed prompts (TS-6). Upfront clarity costs 50 extra input tokens but saves 5,000 tokens of unnecessary exploration and re-work. |
| **Source confidence** | HIGH -- Universal consensus across all sources |

---

## Feature Dependencies

```
TS-9 (Lean CLAUDE.md) --> D-7 (Skills for on-demand loading)
                      --> D-2 (Tiered documentation)
                      --> D-11 (Custom compaction instructions)
                      --> TS-4 (Verbosity suppression via CLAUDE.md)

TS-2 (Compaction)     --> D-11 (Custom compaction instructions)

TS-10 (MCP cleanup)   --> TS-11 (CLI over MCP)
                      --> D-9 (MCP tool consolidation)

D-2 (Tiered docs)     --> D-10 (Session-start hooks)
                      --> D-7 (Skills)

TS-7 (Plan mode)      --> D-14 (Incremental test workflow)

D-1 (Subagents)       --> TS-3 (Model routing -- use cheaper models for subagents)

Hook infrastructure   --> D-3 (Read-once hook)
                      --> D-4 (Output preprocessing hooks)
                      --> D-10 (Session-start hooks)
```

---

## MVP Recommendation

For the research report, prioritize experimental validation in this order:

### Priority 1: Measure the Baseline (What does unoptimized Claude Code actually cost?)
1. **System prompt overhead** -- Measure exactly how many tokens the system prompt, tool definitions, CLAUDE.md, and MCP servers consume before any user interaction
2. **Tool call overhead per tool** -- Measure Read, Edit, Bash, Write, Grep, Glob, Agent tool invocation costs
3. **Compaction behavior** -- Measure what survives compaction and what's lost at different utilization levels

### Priority 2: Validate High-Impact Table Stakes
4. **TS-5** (.claudeignore impact) -- same task, with and without .claudeignore
5. **TS-4** (verbosity suppression) -- same task, with and without output instructions
6. **TS-7** (plan mode) -- same task, plan-first vs jump-in
7. **TS-12** (thinking budget) -- same task, different MAX_THINKING_TOKENS values

### Priority 3: Validate Differentiators
8. **D-3** (read-once hook) -- measure across iterative development sessions
9. **D-7** (skills vs CLAUDE.md) -- same instructions, loaded differently
10. **D-15** (cave talk) -- controlled test separating tool tokens from response tokens

### Defer
- **D-9** (MCP consolidation) -- requires custom MCP server work, not generalizable
- **D-10** (session-start hooks) -- compelling but niche

---

## Sources

### Official Documentation (HIGH confidence)
- [Manage costs effectively - Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Best Practices - Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Compaction - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [Prompt caching - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Output styles - Claude Code Docs](https://code.claude.com/docs/en/output-styles)
- [Checkpointing - Claude Code Docs](https://code.claude.com/docs/en/checkpointing)
- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Plugins reference - Claude Code Docs](https://code.claude.com/docs/en/plugins-reference)

### Community Measurements (MEDIUM-HIGH confidence)
- [7 Critical Token-Wasting Patterns (700K+ tokens saved)](https://github.com/anthropics/claude-code/issues/13579)
- [54% context reduction via lazy-loaded skills](https://gist.github.com/johnlindquist/849b813e76039a908d962b2f0923dc9a) -- John Lindquist
- [MCP context optimization: 60% reduction](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code) -- Scott Spence
- [claude-token-efficient CLAUDE.md: 63% output reduction](https://github.com/drona23/claude-token-efficient)
- [read-once hook: 107 sessions measured](https://dev.to/egorfedorov/update-my-claude-code-token-optimizer-now-blocks-redundant-reads-heres-the-data-from-107-27lj)
- [18 Token Management Hacks](https://www.mindstudio.ai/blog/claude-code-token-management-hacks) -- MindStudio
- [Tiered documentation: 60% reduction](https://medium.com/@jpranav97/stop-wasting-tokens-how-to-optimize-claude-code-context-by-60-bfad6fd477e5)
- [50% overall reduction guide](https://32blog.com/en/claude-code/claude-code-token-cost-reduction-50-percent)
- [45 Claude Code tips](https://github.com/ykdojo/claude-code-tips)
- [6 Ways I Cut My Claude Token Usage in Half](https://www.sabrina.dev/p/6-ways-i-cut-my-claude-token-usage)
- [Hidden MCP flag: 32K tokens recovered](https://paddo.dev/blog/claude-code-hidden-mcp-flag/)

### Prompt Caching Deep Dives (HIGH confidence)
- [How Prompt Caching Actually Works in Claude Code](https://www.claudecodecamp.com/p/how-prompt-caching-actually-works-in-claude-code)
- [Cache hit rate to 95%: 6 practical tips](https://blog.wentuo.ai/en/claude-code-prompt-caching-token-optimization-reduce-input-cost-guide-en.html)

### Cave Talk / Response Style (MEDIUM confidence -- debated)
- [Caveman skill repo](https://github.com/JuliusBrussee/caveman)
- [Dickson Tsai (Anthropic) test results](https://x.com/dickson_tsai/status/2040233121929658643)
- [MCP token overhead analysis](https://www.mindstudio.ai/blog/claude-code-mcp-server-token-overhead)
