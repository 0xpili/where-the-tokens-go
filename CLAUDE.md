<!-- GSD:project-start source:PROJECT.md -->
## Project

**Token Optimization Research for Claude Code**

A deep-dive research project exploring techniques to reduce token consumption when using Claude Code without sacrificing output quality or performance. The project involves reverse-engineering Claude's tokenization, system prompt mechanics, tool call overhead, and context window behavior — then running real experiments to measure which strategies actually save tokens. The deliverable is a publicly shareable research report plus a practical guide.

**Core Value:** Discover and validate concrete, measurable techniques that let Claude Code users stretch their usage limits further without losing the quality of Claude's responses.

### Constraints

- **Methodology**: Findings must be backed by actual experiments or observable evidence, not just theoretical reasoning
- **Quality bar**: Report must be publishable — clear writing, structured findings, reproducible experiments
- **Scope**: Focus on techniques available to end users (prompt strategies, CLAUDE.md configs, workflow patterns) — not internal API changes
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Layer 1: Token Counting (Authoritative Measurement)
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Anthropic Token Count API** | `POST /v1/messages/count_tokens` | Ground-truth input token counting | FREE, accepts full message payloads (system prompts, tools, images, PDFs), matches billing. The only authoritative source for Claude 3+ token counts. | HIGH |
| **Anthropic Python SDK** | `anthropic` (latest, currently ~0.82+) | Programmatic token counting via `client.messages.count_tokens()` | Official SDK; directly calls the Token Count API. Supports system prompts, tool definitions, images, PDFs. Returns `{ "input_tokens": N }`. | HIGH |
| **Anthropic TypeScript SDK** | `@anthropic-ai/sdk` (latest) | Same as Python, for JS/TS experiments | Official SDK; `client.messages.countTokens()`. Useful if building Node.js experiment harnesses. | HIGH |
# Count tokens for any message payload -- system prompt, tools, everything
### Layer 2: Local/Offline Token Approximation
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **`@anthropic-ai/tokenizer`** (npm) | Beta | Fast local token counts for text-only payloads | Runs offline, no API call needed. BUT: only accurate for Claude 1/2 models. For Claude 3+, it is a "very rough approximation." Use for relative comparisons, not absolute counts. | MEDIUM |
| **Xenova/claude-tokenizer** (HuggingFace) | N/A | Python-based local tokenization via HuggingFace Transformers | `GPT2TokenizerFast.from_pretrained('Xenova/claude-tokenizer')`. Based on Claude 1/2 tokenizer. Same accuracy caveat as above. Good for batch analysis of text patterns. | LOW |
- Analyzing tokenization patterns (how code vs. prose vs. whitespace tokenizes differently)
- Relative comparisons ("Strategy A uses ~30% fewer tokens than Strategy B")
- Batch processing thousands of text samples where API calls would be slow
- Final measurements for publishable results (use the API instead)
- Counting tokens for tool definitions, images, PDFs, or structured messages
- Any claim about absolute token counts for Claude 3+ models
### Layer 3: Claude Code Session Data (Raw Observability)
| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **JSONL Transcripts** (`~/.claude/projects/<hash>/sessions/`) | Raw per-message token usage from actual sessions | Every Claude Code session writes JSONL with `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` per message. This is THE primary data source for real-world analysis. | HIGH |
| **`/cost` command** (built into Claude Code) | Quick session-level usage summary | Shows total cost, total duration, token usage for the current session. Good for spot checks but not for structured experiments. | HIGH |
| **`/context` command** (built into Claude Code) | Current context window usage breakdown | Shows tokens consumed, tokens available, breakdown by category. Essential for understanding compaction behavior. | HIGH |
| **`/stats` command** (built into Claude Code) | Usage patterns over time | Available for Max/Pro subscribers. Shows usage trends. | MEDIUM |
### Layer 4: Session Analysis Tools
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **ccusage** | Latest (`npx ccusage@latest`) | Aggregate token usage across sessions, days, months, 5-hour billing windows | Best-in-class CLI for Claude Code usage analysis. Reads JSONL transcripts directly. Reports daily/monthly/session/block breakdowns. Separates cache creation vs. cache read. Offline mode available. | HIGH |
| **DuckDB** | Latest | SQL-based analysis of JSONL transcripts | Read JSONL files directly with SQL queries. Powerful for ad-hoc analysis, cross-session comparisons, statistical aggregations. `SELECT * FROM read_json('~/.claude/projects/*/sessions/*.jsonl')`. | HIGH |
| **cccost** | Latest | Real-time per-session token instrumentation | Generates `.usage.json` with per-model stats. Good for live monitoring during experiments. Integrates with statusline scripts. | MEDIUM |
| **jq** | Latest | Quick JSONL parsing and filtering | One-liners for extracting token data from transcripts. Good for scripting experiment pipelines. | HIGH |
### Layer 5: System Prompt & Overhead Analysis
| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **Piebald-AI/claude-code-system-prompts** (GitHub) | Complete catalog of Claude Code's system prompt components with token counts | Updated within minutes of each Claude Code release. 110+ prompt strings, 24 tool definitions, sub-agent prompts, utility prompts. CHANGELOG tracks 141+ versions. Essential reference for understanding overhead. | HIGH |
| **Token Count API + constructed payloads** | Measure exact overhead of each component | Build message payloads with/without specific components (system prompt, tool defs, MCP schemas) and call `count_tokens` to measure the delta. | HIGH |
| **Yuyz0112/claude-code-reverse** | Visualize Claude Code's LLM interactions | Tool to see exactly what gets sent to the API. Useful for understanding the full prompt structure. | MEDIUM |
- Baseline overhead (system prompt + built-in tools + global config): ~27,169 tokens
- Tool definitions alone: 14,000-17,000 tokens (biggest single component)
- System prompt text: ~2,300-3,600 tokens
- Full project setup (with CLAUDE.md, MCP servers, etc.): ~30,919 tokens
- Autocompact buffer: ~33,000 tokens reserved before compaction triggers
### Layer 6: Experiment Orchestration & Benchmarking
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Claude Agent SDK** (Python: `claude_agent_sdk`, TS: `@anthropic-ai/claude-agent-sdk`) | Latest | Programmatic Claude Code execution with token tracking | Run identical tasks with different prompt strategies programmatically. Each `query()` returns `total_cost_usd` and per-step `usage` with full token breakdowns including cache tokens. Per-model breakdowns via `model_usage`. | HIGH |
| **Claude Code CLI** (`claude` with `--output-format stream-json`) | Latest | Headless experiment execution | Run Claude Code non-interactively with structured JSON output. Parse with jq for token stats. CAVEAT: Known bug where stream-json mode duplicates token stats 3-8x for multi-block responses. Verify against JSONL transcripts. | MEDIUM |
| **promptfoo** | Latest (`npm install promptfoo`) | A/B testing prompt strategies across models | Open-source CLI for systematic prompt evaluation. Side-by-side comparison of response quality + token usage + latency. Supports Claude via provider config. Good for structured experiments. | MEDIUM |
| **Python scripts** (custom) | N/A | Experiment harness | Write custom scripts using the Anthropic SDK to run controlled experiments: same task, different system prompts, different instruction styles. Log all token counts. | HIGH |
### Layer 7: Visualization & Reporting
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Python + matplotlib/plotly** | Latest | Charts for research report | Standard visualization for token usage comparisons, overhead breakdowns, strategy A/B results. | HIGH |
| **Jupyter Notebooks** | Latest | Interactive analysis and reproducible experiments | Run experiments, analyze JSONL data, produce visualizations in one document. Good for the publishable research report. | HIGH |
| **DuckDB + Observable/Vega-Lite** | Latest | Interactive data exploration | SQL-driven analysis with rich charting. Alternative to Jupyter for web-publishable reports. | MEDIUM |
## Alternatives Considered
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Token counting | Anthropic Count API | `tiktoken` (OpenAI) | tiktoken uses cl100k_base, a different tokenizer. ~70% vocabulary overlap with Claude's tokenizer, but NOT accurate for Claude. Would give misleading measurements. |
| Token counting | Anthropic Count API | `@anthropic-ai/tokenizer` (local) | Only accurate for Claude 1/2. "Very rough approximation" for Claude 3+. Use for relative comparisons only, never absolute. |
| Session analysis | ccusage + DuckDB | Langfuse | Langfuse is overkill for this research. Designed for production observability of deployed LLM apps, not single-user research. Requires infrastructure (Docker, PostgreSQL). ccusage reads Claude Code's native JSONL files directly. |
| Session analysis | ccusage + DuckDB | Claude-Code-Usage-Monitor | Focused on real-time monitoring and limit prediction, not research analysis. Less flexible for custom queries. |
| Benchmarking | Claude Agent SDK + custom scripts | LLMPerf | LLMPerf measures API performance (latency, throughput), not prompt-level token optimization. Wrong tool for this research. |
| Benchmarking | promptfoo + custom scripts | Helicone | Helicone is a proxy-based observability platform. Adds infrastructure complexity. Not needed when we can read Claude Code's native logs. |
| Cost tracking | ccusage | tokencost (AgentOps) | tokencost uses tiktoken under the hood, which is inaccurate for Claude models. Good for OpenAI, wrong for this project. |
## What NOT to Use (and Why)
| Tool | Why to Avoid |
|------|-------------|
| **tiktoken** | OpenAI's tokenizer. Different BPE vocabulary from Claude. Will produce inaccurate token counts. Any findings based on tiktoken for Claude models would be misleading. |
| **tokencost** | Uses tiktoken internally. Same problem as above. |
| **LLMPerf / LLM Locust** | Measure API throughput and latency, not token optimization. Solving a different problem. |
| **Langfuse** (for this project) | Production observability platform. Requires Docker/Kubernetes, PostgreSQL. Massive overkill for a research project analyzing local JSONL files. |
| **Any web-based tokenizer** (claude-tokenizer.vercel.app, etc.) | Fine for one-off exploration. Useless for systematic experiments requiring hundreds of measurements. Not scriptable. |
## Installation
# Core: Anthropic Python SDK (primary experiment tool)
# Core: ccusage for session analysis
# Core: DuckDB for SQL analysis of JSONL transcripts
# or: brew install duckdb
# Core: jq for JSONL parsing
# Optional: promptfoo for structured A/B testing
# Optional: Claude Agent SDK for programmatic execution
# or: npm install @anthropic-ai/claude-agent-sdk
# Optional: Local tokenizer for pattern analysis (Claude 1/2 accuracy only)
# or (Python): pip install transformers && python -c "from transformers import GPT2TokenizerFast; GPT2TokenizerFast.from_pretrained('Xenova/claude-tokenizer')"
# Optional: Jupyter for interactive analysis
## Key Environment & Data Paths
| Path / Variable | Purpose |
|-----------------|---------|
| `~/.claude/projects/<hash>/sessions/*.jsonl` | Raw session transcripts with per-message token usage |
| `~/.claude/projects/<hash>/sessions-index.json` | Session metadata (summaries, message counts, branches) |
| `ANTHROPIC_API_KEY` | Required for Token Count API and Agent SDK |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Override auto-compaction threshold (1-100) for compaction experiments |
## Research-Specific Stack Considerations
### For Tokenizer Behavior Analysis
### For System Prompt Overhead Measurement
### For Prompt Strategy Benchmarking
### For Context Window & Compaction Research
## Sources
- [Anthropic Token Counting API Docs](https://platform.claude.com/docs/en/build-with-claude/token-counting) - HIGH confidence, official documentation
- [Anthropic Agent SDK Cost Tracking](https://platform.claude.com/docs/en/agent-sdk/cost-tracking) - HIGH confidence, official documentation
- [Anthropic Count Tokens API Reference](https://docs.anthropic.com/en/api/messages-count-tokens) - HIGH confidence, official API reference
- [@anthropic-ai/tokenizer npm package](https://www.npmjs.com/package/@anthropic-ai/tokenizer) - HIGH confidence, official package (with noted limitations)
- [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) - HIGH confidence, community-maintained, updated per release
- [ccusage - Claude Code Usage Analysis](https://github.com/ryoppippi/ccusage) - HIGH confidence, well-maintained open source tool
- [cccost - Instrument Claude Code](https://github.com/badlogic/cccost) - MEDIUM confidence, community tool
- [DuckDB + Claude Code JSONL Analysis](https://liambx.com/blog/claude-code-log-analysis-with-duckdb) - MEDIUM confidence, community approach
- [Yuyz0112/claude-code-reverse](https://github.com/Yuyz0112/claude-code-reverse) - MEDIUM confidence, reverse engineering tool
- [Claude Code Context Buffer Analysis](https://claudefa.st/blog/guide/mechanics/context-buffer-management) - MEDIUM confidence, community research
- [Context Compaction Docs](https://platform.claude.com/docs/en/build-with-claude/compaction) - HIGH confidence, official documentation
- [Claude Code Headless Mode Docs](https://code.claude.com/docs/en/headless) - HIGH confidence, official documentation
- [promptfoo](https://www.promptfoo.dev/docs/intro/) - MEDIUM confidence, well-known open source tool
- [Claude Code Manage Costs](https://code.claude.com/docs/en/costs) - HIGH confidence, official documentation
- [Xenova/claude-tokenizer on HuggingFace](https://huggingface.co/Xenova/claude-tokenizer) - LOW confidence for Claude 3+ accuracy, useful for pattern analysis only
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
