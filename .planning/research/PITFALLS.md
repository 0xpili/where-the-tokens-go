# Domain Pitfalls: Claude Code Token Optimization

**Domain:** LLM token optimization research (Claude Code specific)
**Researched:** 2026-04-05
**Overall confidence:** HIGH (multiple corroborating sources, GitHub issues, official docs)

---

## Critical Pitfalls

Mistakes that invalidate experiments, produce misleading data, or cause token waste far exceeding what they save.

---

### Pitfall 1: Measuring Tokens from JSONL Logs (The 100x Undercount)

**What goes wrong:** Researchers or tool authors read Claude Code's local JSONL conversation logs (`~/.claude/projects/*/`) to measure token usage. These logs undercount input tokens by 100-174x and output tokens by 10-17x. The `usage.input_tokens` field is a streaming placeholder -- 75% of entries are 0 or 1, never updated to the real value. Thinking tokens (60-70% of Opus output) are excluded entirely.

**Why it happens:** Claude Code has two separate data paths. JSONL logs are written during streaming with placeholder values. The statusbar receives finalized cumulative totals from actual API responses. Same API calls, same process, two recording mechanisms with very different fidelity.

**Consequences:** Any experiment measuring token counts from JSONL logs will produce wildly inaccurate results. A session that ccusage reports as 225K tokens may actually be 10.4M tokens. Comparative experiments ("technique A vs technique B") built on this data are meaningless.

**Warning signs:**
- Token counts seem suspiciously low relative to session duration
- Input token counts cluster around 0 or 1
- No thinking tokens appear in measurements
- Totals don't match the statusbar percentage

**Prevention:**
- Use the statusbar JSON payload (piped to statusline scripts) for cumulative totals
- Use `ccusage` with awareness that it reads flawed source data
- Cross-reference with `/context` command output during sessions
- For rigorous experiments, use the Claude API directly with proper `usage` response fields
- If using Claude Code sessions, capture statusbar data programmatically at each turn

**Detection:** Compare JSONL-derived totals against statusbar-reported totals. If they diverge by orders of magnitude, the JSONL data is unreliable.

**Research phase:** This must be addressed in the very first experimental phase. Every subsequent measurement depends on accurate token counting. Getting this wrong invalidates everything downstream.

**Confidence:** HIGH -- documented in multiple sources including a dedicated analysis at gille.ai and confirmed via GitHub issues (#22686).

**Sources:**
- [Claude Code JSONL Logs Undercount Tokens by 100x](https://gille.ai/en/blog/claude-code-jsonl-logs-undercount-tokens/)
- [Where Do Your Claude Code Tokens Actually Go?](https://dev.to/slima4/where-do-your-claude-code-tokens-actually-go-we-traced-every-single-one-423e)
- [GitHub Issue #22686: Output tokens incorrectly recorded in JSONL](https://github.com/anthropics/claude-code/issues/22686)

---

### Pitfall 2: Optimizing Output Tokens While Ignoring Context Compounding

**What goes wrong:** Researchers focus on reducing output verbosity (cave talk, terse instructions, response limits) while ignoring that input tokens compound across a session. Every message re-sends the entire conversation history. Turn 30 costs roughly 31x more in input tokens than turn 1, regardless of output brevity.

**Why it happens:** Output tokens are the visible part -- you see Claude's response getting shorter. Input tokens are invisible -- the growing context payload is hidden from the user. Additionally, output tokens cost 5x more per token than input tokens (e.g., $15 vs $3 per million on Sonnet 4), which makes output reduction feel high-leverage.

**Consequences:** A researcher might measure a 75% reduction in output tokens from cave talk but miss that the session's total cost barely changed because input tokens (context re-sends) dominate in longer sessions. Worse, the cave talk instruction itself adds input tokens to every turn.

**Warning signs:**
- Token savings are measured only on output
- Experiments don't account for session length
- Savings percentages are calculated per-message rather than per-session
- The "optimization" instruction itself is never counted as overhead

**Prevention:**
- Always measure total session tokens (input + output + thinking), not just output
- Track token counts per turn to observe compounding behavior
- Calculate the break-even point where instruction overhead exceeds output savings
- For cave talk / terse instructions: measure the instruction's own token cost vs. per-turn savings

**Detection:** If an experiment reports "75% token savings" but only measured output tokens, the finding is incomplete and likely misleading.

**Research phase:** Must be established as a measurement principle before any technique comparison experiments. The experimental framework needs to capture all token categories.

**Confidence:** HIGH -- context compounding is well-documented in official docs and multiple independent analyses.

**Sources:**
- [How Context Compounding Works in Claude Code](https://www.mindstudio.ai/blog/claude-code-context-compounding-explained-2)
- [Claude Code Isn't Eating Your Tokens. Your Workflow Is.](https://cybernerdie.medium.com/claude-code-isnt-eating-your-tokens-your-workflow-is-aeb4445176d3)
- [Manage costs effectively - Claude Code Docs](https://code.claude.com/docs/en/costs)

---

### Pitfall 3: Confusing Cache Cost Savings with Context Space Savings

**What goes wrong:** Users (and potentially researchers) assume that prompt caching reduces context window consumption. It does not. Cached tokens still count against the 200K (or 1M) context window limit. Caching reduces monetary cost (cache reads cost 10% of base input pricing) but does not free up context space.

**Why it happens:** The word "caching" implies reuse and efficiency, which intuitively suggests "less space used." Anthropic's documentation clarifies this, but the misconception persists in community discussions.

**Consequences:** Researchers might design experiments assuming cached content is "free" in terms of context pressure, leading to incorrect conclusions about when compaction triggers or how much effective context is available. Optimization strategies built on "just cache it" fail to address context window exhaustion.

**Warning signs:**
- Research assumes cached system prompts don't count toward context limits
- Experiments treat cache hits as having zero context footprint
- Strategies for avoiding compaction rely on caching rather than context reduction

**Prevention:**
- Clearly distinguish between "cost savings" (what caching provides) and "space savings" (what caching does NOT provide)
- Use `/context` to verify that cached content still appears in the token breakdown
- Design experiments with separate metrics for cost-per-token and context-space-consumed

**Detection:** If a strategy claims to "extend your context window" via caching, it's conflating two distinct concepts.

**Research phase:** Must be clarified in the foundational measurement phase. The distinction affects how every subsequent optimization is evaluated.

**Confidence:** HIGH -- explicitly stated in official docs: "caching saves money, not space."

**Sources:**
- [Where Do Your Claude Code Tokens Actually Go?](https://dev.to/slima4/where-do-your-claude-code-tokens-actually-go-we-traced-every-single-one-423e)
- [Prompt caching - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

---

### Pitfall 4: The Compaction Quality Cliff (Token Savings That Destroy Intelligence)

**What goes wrong:** Auto-compaction summarizes conversation history to free context space, but the summarization is lossy. Roughly 20-30% of original detail survives. Instructions established early in a conversation are lost first (recency bias). After compaction, Claude violates rules it followed perfectly, forgets coding conventions, repeats errors that established patterns prevented, and sometimes forgets which codebase it's working on.

**Why it happens:** Compaction prioritizes recency over importance. Early-session instructions, mid-conversation corrections, and refined working patterns vanish first. The summarization algorithm has no way to know which details are "critical" vs. "nice to have" without explicit guidance.

**Consequences:** Tasks that should take 1 hour take 5-6 hours due to constant regression. For token optimization research specifically: an experiment that crosses a compaction boundary produces inconsistent results because Claude's behavior changes after compaction. A "before vs. after" comparison may actually be measuring "pre-compaction vs. post-compaction" quality, not the technique being tested.

**Warning signs:**
- Claude suddenly violates rules it was following consistently
- Quality degrades mid-session for no apparent reason
- `/context` shows a recent compaction event
- Claude asks about things it previously knew

**Prevention:**
- Put critical instructions in CLAUDE.md (survives compaction; re-read from disk)
- Use `/compact <preservation instructions>` to guide what the summary retains
- Design experiments to complete within a single compaction cycle
- Use hooks (e.g., post_compact_reminder) to re-inject critical context after compaction
- If testing long sessions, note compaction events as confounding variables

**Detection:** Compare Claude's adherence to instructions before and after compaction events. If behavior changes, compaction is a confound.

**Research phase:** Must be accounted for in experiment design. Any experiment spanning multiple compaction cycles needs to control for this variable.

**Confidence:** HIGH -- extensively documented with 1,000+ affected users across GitHub issues (#1534, #13919) and multiple blog posts.

**Sources:**
- [Claude Saves Tokens, Forgets Everything](https://golev.com/post/claude-saves-tokens-forgets-everything/)
- [GitHub Issue #13919: Skills context lost after auto-compaction](https://github.com/anthropics/claude-code/issues/13919)
- [GitHub Issue #1534: Memory Loss After Auto-compact](https://github.com/anthropics/claude-code/issues/1534)
- [post_compact_reminder hook](https://github.com/Dicklesworthstone/post_compact_reminder)

---

### Pitfall 5: Subagent Token Multiplication (The Hidden 4-15x Multiplier)

**What goes wrong:** Claude Code's Task tool (subagent spawning) and Agent Teams create multiplicative token consumption. Each subagent opens its own context window with its own system prompt overhead. Multi-agent workflows use 4-7x more tokens than single-agent sessions. Agent Teams run at roughly 15x standard usage. One documented session spawned 49 subagents and consumed $8,000-$15,000 in a single run.

**Why it happens:** Subagents are invisible to the user in most cases. Claude Code decides autonomously when to spawn subagents for parallel work. There is no native per-agent cost breakdown, no trace view, and no way to see what running subagents are doing without examining raw outputs.

**Consequences:** A "simple" refactoring task might silently spawn multiple subagents, each burning through its own context window. Users on Pro plans have reported hitting usage limits in 15 minutes due to unexpected parallel subagent activity. For research: experiments comparing token usage of different approaches must control for whether subagents were spawned.

**Warning signs:**
- Token consumption rate suddenly spikes mid-task
- Usage limits hit far sooner than expected
- Multiple parallel operations visible in terminal output
- Claude mentions delegating to or consulting with other agents

**Prevention:**
- Monitor for subagent spawning during experiments (watch for Task tool invocations)
- Set explicit instructions against spawning subagents if not needed: "Do not use the Task tool"
- Use `/model` to set the subagent model to a cheaper option (Sonnet or Haiku)
- For experiments: log whether subagents were used as an experimental variable
- Disable Agent Teams unless specifically testing that feature

**Detection:** Check session logs for Task tool calls or parallel agent activity. Unexpected token spikes without proportional output are a strong signal.

**Research phase:** Important for any experiment phase that involves complex, multi-file tasks. Must be controlled for or explicitly measured.

**Confidence:** HIGH -- documented in official Anthropic docs, multiple GitHub issues, and independent cost analyses.

**Sources:**
- [The Claude Code Subagent Cost Explosion](https://www.aicosts.ai/blog/claude-code-subagent-cost-explosion-887k-tokens-minute-crisis)
- [Claude Code Sub Agents - Burn Out Your Tokens](https://dev.to/onlineeric/claude-code-sub-agents-burn-out-your-tokens-4cd8)
- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)

---

## Moderate Pitfalls

---

### Pitfall 6: The Cave Talk Illusion (Cosmetic Savings, Real Costs)

**What goes wrong:** Techniques like "cave talk" (making Claude respond in abbreviated language) appear to save ~75% of output tokens in demos. In practice, the savings are offset by: (a) the instruction itself consuming input tokens on every turn, (b) lost context in responses leading to follow-up clarifications, (c) degraded quality for complex tasks where nuance matters, and (d) input tokens dominating total cost in longer sessions anyway.

**Why it happens:** Cave talk is visually dramatic -- the response looks much shorter. The viral nature of the technique led to widespread adoption without rigorous measurement. Most "75% savings" claims measure only output tokens for a single turn, not total session cost.

**Prevention:**
- Measure per-session totals, not per-turn output
- Calculate the instruction overhead (the cave talk CLAUDE.md itself) against per-turn savings
- Test on complex tasks (multi-file refactors, debugging), not just simple demos
- Distinguish between "response style" optimizations (safe) and "reasoning compression" (dangerous)

**Detection:** If cave talk savings are reported as a single percentage without specifying "of output tokens only" and "for this specific task type," the claim is incomplete.

**Research phase:** This is a key technique to benchmark in the experiments phase. Needs rigorous A/B testing with total-session metrics.

**Confidence:** MEDIUM -- the critique is well-sourced but the technique's actual ROI varies by task type and session length. Needs experimental validation.

**Sources:**
- [Caveman Claude GitHub](https://github.com/JuliusBrussee/caveman)
- [Claude Saves Tokens, Forgets Everything](https://golev.com/post/claude-saves-tokens-forgets-everything/)
- [Claude Code Pricing: Optimize Your Token Usage](https://claudefa.st/blog/guide/development/usage-optimization)

---

### Pitfall 7: The 33K-45K Invisible Buffer (Your Context Window Is Smaller Than You Think)

**What goes wrong:** Claude Code reserves a hardcoded buffer of ~33K tokens (reduced from ~45K in early 2026) that users cannot access. Auto-compaction triggers at approximately 83.5% of the total window (~167K tokens for a 200K window). Users who think they have 200K tokens of working space actually have ~153K after system overhead and the buffer.

**Why it happens:** The buffer serves three purposes: working space for summarization, completion buffer for in-progress tasks, and response generation space. It is not configurable despite user requests. The `CLAUDE_CODE_MAX_OUTPUT_TOKENS` setting controls individual response length, NOT this buffer -- a common source of confusion.

**Prevention:**
- Account for the buffer when designing experiments that test context window boundaries
- Use `/context` to see actual available space, not theoretical maximum
- If testing with 1M context models, understand that the buffer scales differently
- Use `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (1-100) to control when compaction fires, but understand this shifts the trigger point, not the buffer size

**Detection:** When `/context` shows 25% remaining, actual usable space before compaction is only ~8.5% (25% minus 16.5% buffer).

**Research phase:** Relevant when investigating context window mechanics and compaction behavior.

**Confidence:** HIGH -- confirmed via `/context` output analysis, multiple independent tests, and GitHub issues.

**Sources:**
- [Claude Code Context Buffer: The 33K-45K Token Problem](https://claudefa.st/blog/guide/mechanics/context-buffer-management)
- [Context windows - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/context-windows)

---

### Pitfall 8: MCP Tool Schema Bloat (Paying for Tools You Never Use)

**What goes wrong:** Each connected MCP server injects its full tool schema into every single message. A server with 10-15 tools costs 1,500-4,000 tokens per turn. Servers with extensive documentation can exceed 5,000-8,000 tokens. Multiple servers can reduce effective context from 200K to approximately 70K. This overhead applies whether the tools are used or not.

**Why it happens:** MCP tool definitions must be available for Claude to decide whether to use them. Without the schema in context, Claude cannot invoke the tool. Claude Code's tool search feature (enabled by default) partially mitigates this by deferring tool definitions until needed, but awareness of the mechanism is still critical.

**Prevention:**
- Audit connected MCP servers before experiments: disconnect unused ones
- Use `ENABLE_TOOL_SEARCH=auto:5` to defer more aggressively (5% threshold vs default 10%)
- Use project-level MCP configs to load only relevant servers per project
- For experiments measuring baseline overhead: test with zero MCP servers, then add them incrementally
- Consider CLI tool alternatives that consume zero tokens when idle

**Detection:** Run `/context` and check "Tools" section. If tool definitions consume >10% of your context, there's optimization opportunity.

**Research phase:** Must be measured during the system prompt / overhead analysis phase. MCP overhead is a major variable that must be controlled in experiments.

**Confidence:** HIGH -- documented in official Claude Code docs, GitHub feature requests (#7172, #11364, #3406), and independent analyses.

**Sources:**
- [Claude Code MCP Servers and Token Overhead](https://www.mindstudio.ai/blog/claude-code-mcp-server-token-overhead)
- [Claude Code's Hidden MCP Flag: 32k Tokens Back](https://paddo.dev/blog/claude-code-hidden-mcp-flag/)
- [MCP Server Token Costs in Claude Code: Full Breakdown](https://www.jdhodges.com/blog/claude-code-mcp-server-token-costs/)
- [GitHub Issue #11364: Lazy-load MCP tool definitions](https://github.com/anthropics/claude-code/issues/11364)

---

### Pitfall 9: CLAUDE.md as a Token Dump (The Compounding Instruction Tax)

**What goes wrong:** Users fill CLAUDE.md with extensive project context, coding standards, architectural notes, and workflow instructions. This file is re-injected on every single API call -- not just per session, per message. A 1,000-token CLAUDE.md costs 1,000 tokens on turn 1, and 1,000 tokens again on turn 2, and again on turn 3... across an entire session. Over 30 turns, that's 30,000 tokens of overhead from CLAUDE.md alone.

**Why it happens:** CLAUDE.md is the canonical place to put project instructions, so users naturally expand it. The per-message cost is invisible -- it looks like a one-time setup, not a recurring tax.

**Prevention:**
- Keep CLAUDE.md under 200 lines / 500 tokens
- Use CLAUDE.md as an index pointing to skill files loaded on demand
- Move domain-specific knowledge into skills (loaded only when relevant)
- Benchmark: measure a session's overhead with CLAUDE.md vs. without it
- Use a skills architecture: 10 skills with frontmatter-only loading costs ~1,000 tokens total at startup vs. 50,000+ if everything were in CLAUDE.md

**Detection:** Check `/context` for "Memory files" or "CLAUDE.md" token count. If it exceeds 1,000 tokens, consider restructuring.

**Research phase:** Part of the system prompt overhead analysis. Compare token usage with different CLAUDE.md sizes.

**Confidence:** HIGH -- documented in official Claude Code docs and confirmed via `/context` measurements.

**Sources:**
- [Stop Wasting Tokens: Optimize Claude Code Context by 60%](https://medium.com/@jpranav97/stop-wasting-tokens-how-to-optimize-claude-code-context-by-60-bfad6fd477e5)
- [Claude Code Skills: The 98% Token Savings Architecture](https://www.codewithseb.com/blog/claude-code-skills-reusable-ai-workflows-guide)
- [Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices)

---

### Pitfall 10: The False Economy of Too-Short Prompts

**What goes wrong:** Aggressively brief prompts save a few dozen tokens on input but cause Claude to: (a) ask clarifying questions (multi-turn overhead), (b) produce incorrect output requiring correction (retry overhead), (c) generate exploratory responses covering multiple interpretations (output bloat). The total token cost of a vague prompt + 3 correction turns far exceeds one detailed prompt + 1 correct response.

**Why it happens:** Short prompts feel efficient. The cost of retries and clarifications is spread across multiple turns and harder to attribute to the original prompt's brevity.

**Consequences:** A "help me refactor the auth system" prompt leads to clarification exchanges that burn tokens before any real work happens. One well-scoped prompt with file paths, constraints, and expected output beats five clarifying exchanges.

**Prevention:**
- Invest tokens in upfront specificity: file paths, constraints, expected behavior, edge cases
- Measure total-task-completion cost, not per-prompt cost
- Include acceptance criteria in the initial prompt to avoid correction cycles
- Rule of thumb: 50 extra input tokens to avoid 500 output tokens of clarification is a 10:1 return

**Detection:** If a session shows a pattern of short-prompt -> Claude-question -> user-clarification -> Claude-attempt -> user-correction, the initial prompt was too short.

**Research phase:** Relevant to the prompt engineering experiments. Test "minimal prompt" vs. "detailed prompt" total session costs.

**Confidence:** HIGH -- well-established in prompt engineering literature and confirmed by multiple Claude Code practitioners.

**Sources:**
- [Claude Code Isn't Eating Your Tokens. Your Workflow Is.](https://cybernerdie.medium.com/claude-code-isnt-eating-your-tokens-your-workflow-is-aeb4445176d3)
- [Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices)

---

### Pitfall 11: Prompt Cache TTL Blind Spots (The 5-Minute Eviction)

**What goes wrong:** Claude's prompt cache has a 5-minute TTL. Active typing keeps the cache warm indefinitely, but any pause longer than 5 minutes evicts the cache entirely. Resuming after a break forces full context recreation. One documented case showed a 350K-token cache recreation after 13 hours of inactivity, causing a 9% usage spike from a single prompt.

**Why it happens:** The 5-minute TTL is a design tradeoff balancing cache storage costs vs. hit rates. Most users don't realize the cache is this aggressive. There's a 1-hour TTL option at 2x cost, but it's rarely used.

**Consequences:** For token optimization research: experiments that span multiple work sessions (with breaks) incur cache recreation costs that confound measurements. Two identical experiments -- one continuous, one with a lunch break -- will show different token costs.

**Prevention:**
- Note session continuity as an experimental variable
- If comparing techniques across sessions, account for cache-cold-start costs
- Design experiments to run within continuous sessions when possible
- Understand that cache write costs 1.25x normal pricing, but cache reads cost only 0.1x -- the break-even is at turn 2

**Detection:** Check for cache_read vs. cache_creation tokens in API responses. A spike in cache_creation after a gap indicates cache eviction.

**Research phase:** Must be accounted for in experiment design methodology. Session continuity is a confounding variable.

**Confidence:** HIGH -- documented in official Anthropic prompt caching docs and confirmed via independent traffic analysis.

**Sources:**
- [How Prompt Caching Actually Works in Claude Code](https://www.claudecodecamp.com/p/how-prompt-caching-actually-works-in-claude-code)
- [How I Debugged Claude Code's 9% Cache Spike](https://medium.com/@luongnv89/how-i-debugged-claude-codes-9-cache-spike-in-one-prompt-9ec4e6932d6e)
- [Prompt caching - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

---

### Pitfall 12: The 1M Context Window Trap (More Space Does Not Mean Better Attention)

**What goes wrong:** Users switch to 1M context models (e.g., `sonnet[1m]`, `opus[1m]`) expecting to avoid compaction entirely. While the larger window delays compaction, it introduces a different problem: attention degradation. Retrieval accuracy drops measurably starting around 400K tokens, becomes unreliable past 600K on Sonnet 4.6, and Opus 4.6 drops from 93% accuracy at 256K to 76% at 1M on multi-needle retrieval benchmarks.

**Why it happens:** The "lost in the middle" phenomenon -- models over-attend to the beginning and end of context, under-attending to the middle. A larger context window means more middle, and more forgotten content.

**Consequences:** Instructions placed in the "middle" of a long session are effectively invisible. Claude may ignore design documents, misunderstand architectural decisions, or violate rules that worked at 200K. A researcher testing "does 1M context eliminate compaction problems?" may find that it replaces compaction-induced amnesia with attention-induced amnesia.

**Prevention:**
- Don't use 1M context as a substitute for context management
- Monitor retrieval accuracy as context fills (test with specific recall questions)
- Keep critical instructions at the beginning (CLAUDE.md) or end (current prompt) of context
- Compare behavior at 200K, 400K, 600K, and 800K to find the degradation curve for each model
- The guidance stands: curate what goes into context, don't just dump everything

**Detection:** If Claude starts ignoring mid-session instructions or producing responses inconsistent with earlier context, attention degradation may be the cause.

**Research phase:** Important for the context window mechanics investigation. Tests should measure not just "does it fit?" but "does Claude still follow instructions at this context size?"

**Confidence:** HIGH -- confirmed by Anthropic's own MRCR v2 benchmarks and independent developer testing.

**Sources:**
- [Claude Code Now Has 1M Tokens of Context -- and You Shouldn't Fill Them](https://wmedia.es/en/tips/claude-code-1m-context-window-tips)
- [Claude Opus 4.6 1M: Self-reported degradation starting at 40%](https://github.com/anthropics/claude-code/issues/34685)
- [Context windows - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/context-windows)

---

### Pitfall 13: Using the Wrong Model for the Task (The 5x Overspend)

**What goes wrong:** Defaulting to Opus for all tasks when Sonnet handles 80%+ of coding tasks at ~20% of the cost. Output tokens on Opus cost $75/M vs. $15/M on Sonnet (5x premium). At Opus's highest effort level, it uses 48% fewer tokens than Sonnet for equivalent quality on complex tasks -- but this advantage only materializes for genuinely complex reasoning. For formatting, minor edits, simple refactors, and routine code generation, Opus provides no quality advantage while consuming quota 5x faster.

**Why it happens:** Users want "the best model" and don't realize the cost differential. Claude Code Max plans have unified quota, making it feel "free" -- but the quota is denominated in tokens, and Opus consumes them much faster.

**Prevention:**
- Default to Sonnet for routine tasks; switch to Opus only for complex reasoning
- Use `/model` to switch models mid-session based on task complexity
- For experiments: test each technique on both Sonnet and Opus to measure model-specific effects
- Use effort levels (`/effort`) to control thinking depth on a per-task basis

**Detection:** If token consumption per task varies wildly across similar tasks, check which model was used. High-cost outliers on simple tasks indicate model mismatch.

**Research phase:** Relevant to any experiment comparing techniques. Model selection is a key control variable.

**Confidence:** HIGH -- pricing is public, performance comparisons well-documented.

**Sources:**
- [Claude Code Pricing: Optimize Your Token Usage](https://claudefa.st/blog/guide/development/usage-optimization)
- [Model configuration - Claude Code Docs](https://code.claude.com/docs/en/model-config)
- [Pricing - Claude API Docs](https://platform.claude.com/docs/en/about-claude/pricing)

---

## Minor Pitfalls

---

### Pitfall 14: File Reading Overhead (The 70% Line-Number Tax)

**What goes wrong:** Claude Code's Read tool and `@filename` syntax add line-number formatting to every file loaded into context. This adds approximately 70% token overhead to raw file content (1.7x multiplier). A file that would cost 1,000 tokens raw costs ~1,700 tokens when loaded.

**Prevention:**
- Use `--lines` or specify offset/limit to read only relevant sections
- Avoid reading entire large files when only a section is needed
- Recent Claude Code versions use compact line-number format -- ensure you're on a recent version
- For experiments measuring file-loading overhead: compare raw file tokens against loaded-in-context tokens

**Detection:** Compare raw file token counts (via a tokenizer) with `/context` reported sizes after loading.

**Confidence:** HIGH -- documented as GitHub bug (#20223, #18218), partially addressed in recent updates.

**Sources:**
- [GitHub Issue #20223: File loading adds 70% token overhead](https://github.com/anthropics/claude-code/issues/20223)

---

### Pitfall 15: Extended Thinking Budget Waste

**What goes wrong:** Extended thinking defaults to up to 31,999 tokens per request. For simple tasks, this is pure waste. Conversely, there are reports that Claude Code delivers only ~10% of the requested thinking budget regardless of configuration -- meaning the budget setting may not work as expected.

**Prevention:**
- Lower thinking budget for simple tasks: `MAX_THINKING_TOKENS=8000` or use `/effort low`
- Disable thinking entirely in `/config` for mechanical tasks
- For experiments: control thinking budget as a variable and measure actual thinking tokens consumed vs. budget

**Detection:** Compare configured thinking budget against actual thinking tokens in API responses.

**Confidence:** MEDIUM -- the 10% delivery claim (GitHub #20350) is disputed and may reflect measurement methodology issues.

**Sources:**
- [Building with extended thinking - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)
- [GitHub Issue #20350: 10% of Requested Thinking Budget](https://github.com/anthropics/claude-code/issues/20350)

---

### Pitfall 16: The Autocompact Loop (Historical but Instructive)

**What goes wrong:** A bug in Claude Code versions prior to ~2.1.89 caused infinite compaction loops, where the system would retry compaction up to 3,272 times in a single session. This consumed 96-108M tokens/day vs. normal 0-45M tokens/day. Globally, approximately 250,000 wasted API calls per day before the fix.

**Prevention:**
- Ensure Claude Code is on version 2.1.89+ which includes a circuit breaker (MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3)
- Monitor for repeated compaction messages in terminal output
- For research: note that any historical data or blog posts from before April 2026 may include sessions affected by this bug

**Detection:** If compaction fires repeatedly without the session making progress, the loop bug may be present.

**Confidence:** HIGH -- officially acknowledged and patched by Anthropic. Fix documented in April 1, 2026 changelog.

**Sources:**
- [GitHub Issue #9579: Autocompacting Loop](https://github.com/anthropics/claude-code/issues/9579)
- [GitHub Issue #34363: Autocompact buffer exceeds context window](https://github.com/anthropics/claude-code/issues/34363)
- [Changelog - Claude Code Docs](https://code.claude.com/docs/en/changelog)

---

### Pitfall 17: Over-Constraining Output Length (Quality vs. Token Tradeoff)

**What goes wrong:** Imposing strict output length limits (e.g., "respond in under 100 tokens") can reduce output token expenditure by 20-30%, but overly stringent constraints truncate essential code elements, reducing functional correctness. The model cuts corners on completeness to meet the length constraint.

**Prevention:**
- Constrain verbosity of explanation, not code output (e.g., "minimal commentary, complete code")
- Test output quality at different constraint levels before adopting a limit
- Use structured output formats (e.g., "respond with only the changed function") rather than arbitrary token limits
- For experiments: always measure quality alongside token count -- savings are meaningless if correctness drops

**Detection:** If constrained outputs require follow-up requests for "the rest" or produce code that doesn't compile/run, the constraint is too tight.

**Confidence:** MEDIUM -- documented in academic research on LLM output constraints but not specific to Claude Code.

**Sources:**
- [Optimizing Token Consumption in LLMs: A Nano Surge Approach](https://arxiv.org/html/2504.15989v2)
- [LLM Cost Optimization: Reduce Tokens Without Losing Quality](https://bloglab-65579.firebaseapp.com/blogs/ai/llm-cost-optimization-reduce-tokens-without-losing-quality.html)

---

## Meta-Pitfalls for the Research Project Itself

These are pitfalls specific to conducting this token optimization research, not pitfalls of token optimization in general.

---

### Meta-Pitfall A: Survivorship Bias in Community Techniques

**What goes wrong:** Blog posts and viral tweets about token-saving techniques report only successes. Techniques that degraded quality or didn't save tokens are rarely written about. The researcher risks cataloging a biased set of "working" techniques.

**Prevention:**
- Test every technique independently, including popular ones
- Explicitly measure quality (correctness, completeness) alongside token count
- Include negative results in the research report
- Seek out GitHub issues and complaints, not just success stories

---

### Meta-Pitfall B: Claude Code Version Sensitivity

**What goes wrong:** Claude Code updates frequently (sometimes weekly). Tokenization behavior, compaction logic, tool overhead, and default settings change between versions. Findings from version 2.1.74 may not apply to 2.1.89+.

**Prevention:**
- Record Claude Code version for every experiment
- Re-validate critical findings after updates
- Note version numbers in all research outputs
- Check the changelog before publishing findings

---

### Meta-Pitfall C: Conflating API Usage with Claude Code Usage

**What goes wrong:** Research about Claude API token optimization is applied to Claude Code without accounting for Claude Code's additional layers: system prompts, tool schemas, MCP servers, compaction, agent spawning, and the statusbar system. An API-level optimization (e.g., "use prompt caching") may already be automatic in Claude Code, or may behave differently due to Claude Code's wrapper.

**Prevention:**
- Clearly distinguish between "Claude API" and "Claude Code" in all findings
- Test optimizations within Claude Code, not just via the API
- Document which layer each optimization targets (API, Claude Code wrapper, user workflow)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Measurement setup | JSONL undercount (#1) | Validate measurement pipeline before ANY experiments |
| System prompt analysis | CLAUDE.md tax (#9), MCP bloat (#8) | Baseline with zero CLAUDE.md, zero MCP, then add incrementally |
| Tokenizer reverse-engineering | File line-number overhead (#14) | Compare raw vs. loaded token counts explicitly |
| Context window mechanics | Buffer (#7), cache TTL (#11), 1M trap (#12) | Design experiments to isolate each mechanism |
| Compaction investigation | Quality cliff (#4), autocompact loop (#16) | Ensure latest Claude Code version; note compaction events |
| Output reduction techniques | Cave talk illusion (#6), over-constraining (#17) | Measure total session cost AND quality, not just output tokens |
| Prompt engineering | False economy of short prompts (#10) | Measure task-completion cost, not per-prompt cost |
| Session workflow optimization | Context compounding (#2), model mismatch (#13) | Track per-turn cumulative costs; control model as variable |
| Subagent / advanced features | Token multiplication (#5) | Explicitly control subagent usage in experiments |
| Comparative experiments | All measurement pitfalls (#1, #2, #3) | Use consistent methodology across all comparisons |

---

## Key Insight for the Research Project

The single most important finding across all pitfalls: **the dominant token cost in Claude Code is not what you write or what Claude writes -- it's the invisible, cumulative re-sending of context on every turn.** System prompts (~14K), tool schemas (1K-18K), CLAUDE.md, conversation history -- all resent on every message. Optimizations that reduce this per-turn overhead compound across sessions. Optimizations that only reduce output tokens are a rounding error in long sessions.

The research should prioritize techniques in this order of expected impact:
1. **Workflow patterns** (session management, compaction timing, task decomposition) -- highest leverage
2. **Context overhead reduction** (CLAUDE.md optimization, MCP pruning, skills architecture) -- significant and compounding
3. **Model/effort selection** (right model for right task) -- easy wins, 60-80% savings on mismatch
4. **Output reduction techniques** (response style, constraints) -- visible but often overstated
5. **Exotic techniques** (cave talk, compressed prompts) -- good for demos, questionable at scale
