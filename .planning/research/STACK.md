# Technology Stack

**Project:** Token Optimization Research for Claude Code
**Researched:** 2026-04-05

## Recommended Stack

This is a research project, not a product build. The "stack" is the set of tools, APIs, data sources, and analysis methods needed to measure, analyze, and benchmark token consumption in Claude Code sessions. Every recommendation below is oriented toward producing reproducible, publishable findings.

### Layer 1: Token Counting (Authoritative Measurement)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Anthropic Token Count API** | `POST /v1/messages/count_tokens` | Ground-truth input token counting | FREE, accepts full message payloads (system prompts, tools, images, PDFs), matches billing. The only authoritative source for Claude 3+ token counts. | HIGH |
| **Anthropic Python SDK** | `anthropic` (latest, currently ~0.82+) | Programmatic token counting via `client.messages.count_tokens()` | Official SDK; directly calls the Token Count API. Supports system prompts, tool definitions, images, PDFs. Returns `{ "input_tokens": N }`. | HIGH |
| **Anthropic TypeScript SDK** | `@anthropic-ai/sdk` (latest) | Same as Python, for JS/TS experiments | Official SDK; `client.messages.countTokens()`. Useful if building Node.js experiment harnesses. | HIGH |

**How to use for this research:**
```python
import anthropic
client = anthropic.Anthropic()

# Count tokens for any message payload -- system prompt, tools, everything
response = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="You are a scientist",
    tools=[...],  # Include tool definitions to measure their overhead
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.input_tokens)  # Exact count
```

**Critical caveat:** The count is an estimate that may differ slightly from actual billing. Anthropic adds system optimization tokens that are NOT billed but ARE counted. You are not billed for system-added tokens.

### Layer 2: Local/Offline Token Approximation

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **`@anthropic-ai/tokenizer`** (npm) | Beta | Fast local token counts for text-only payloads | Runs offline, no API call needed. BUT: only accurate for Claude 1/2 models. For Claude 3+, it is a "very rough approximation." Use for relative comparisons, not absolute counts. | MEDIUM |
| **Xenova/claude-tokenizer** (HuggingFace) | N/A | Python-based local tokenization via HuggingFace Transformers | `GPT2TokenizerFast.from_pretrained('Xenova/claude-tokenizer')`. Based on Claude 1/2 tokenizer. Same accuracy caveat as above. Good for batch analysis of text patterns. | LOW |

**When to use local tokenizers:**
- Analyzing tokenization patterns (how code vs. prose vs. whitespace tokenizes differently)
- Relative comparisons ("Strategy A uses ~30% fewer tokens than Strategy B")
- Batch processing thousands of text samples where API calls would be slow

**When NOT to use local tokenizers:**
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

**JSONL transcript structure (key fields):**
```json
{
  "type": "assistant",
  "message": {
    "id": "msg_...",
    "usage": {
      "input_tokens": 27169,
      "output_tokens": 342,
      "cache_creation_input_tokens": 5200,
      "cache_read_input_tokens": 21000
    }
  }
}
```

### Layer 4: Session Analysis Tools

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **ccusage** | Latest (`npx ccusage@latest`) | Aggregate token usage across sessions, days, months, 5-hour billing windows | Best-in-class CLI for Claude Code usage analysis. Reads JSONL transcripts directly. Reports daily/monthly/session/block breakdowns. Separates cache creation vs. cache read. Offline mode available. | HIGH |
| **DuckDB** | Latest | SQL-based analysis of JSONL transcripts | Read JSONL files directly with SQL queries. Powerful for ad-hoc analysis, cross-session comparisons, statistical aggregations. `SELECT * FROM read_json('~/.claude/projects/*/sessions/*.jsonl')`. | HIGH |
| **cccost** | Latest | Real-time per-session token instrumentation | Generates `.usage.json` with per-model stats. Good for live monitoring during experiments. Integrates with statusline scripts. | MEDIUM |
| **jq** | Latest | Quick JSONL parsing and filtering | One-liners for extracting token data from transcripts. Good for scripting experiment pipelines. | HIGH |

**Recommended analysis pipeline:**
1. Run experiments in Claude Code (producing JSONL transcripts)
2. Use `ccusage session` for quick per-session summaries
3. Use DuckDB for deep cross-session statistical analysis
4. Use jq for scripted extraction in experiment automation

### Layer 5: System Prompt & Overhead Analysis

| Technology | Purpose | Why | Confidence |
|------------|---------|-----|------------|
| **Piebald-AI/claude-code-system-prompts** (GitHub) | Complete catalog of Claude Code's system prompt components with token counts | Updated within minutes of each Claude Code release. 110+ prompt strings, 24 tool definitions, sub-agent prompts, utility prompts. CHANGELOG tracks 141+ versions. Essential reference for understanding overhead. | HIGH |
| **Token Count API + constructed payloads** | Measure exact overhead of each component | Build message payloads with/without specific components (system prompt, tool defs, MCP schemas) and call `count_tokens` to measure the delta. | HIGH |
| **Yuyz0112/claude-code-reverse** | Visualize Claude Code's LLM interactions | Tool to see exactly what gets sent to the API. Useful for understanding the full prompt structure. | MEDIUM |

**Key overhead measurements from Piebald-AI (as of v2.1.92):**
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

**IMPORTANT: stream-json token duplication bug.**
When using `--output-format stream-json`, Claude Code SDK splits single API responses with multiple content blocks (thinking, text, tool_use) into separate streaming events, each preserving the complete usage statistics. This inflates token counts 3-8x. Always cross-reference against JSONL transcript files for ground truth.

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

```bash
# Core: Anthropic Python SDK (primary experiment tool)
pip install anthropic

# Core: ccusage for session analysis
npx ccusage@latest  # or: npm install -g ccusage

# Core: DuckDB for SQL analysis of JSONL transcripts
pip install duckdb
# or: brew install duckdb

# Core: jq for JSONL parsing
brew install jq  # macOS

# Optional: promptfoo for structured A/B testing
npm install -g promptfoo

# Optional: Claude Agent SDK for programmatic execution
pip install claude-agent-sdk
# or: npm install @anthropic-ai/claude-agent-sdk

# Optional: Local tokenizer for pattern analysis (Claude 1/2 accuracy only)
npm install @anthropic-ai/tokenizer
# or (Python): pip install transformers && python -c "from transformers import GPT2TokenizerFast; GPT2TokenizerFast.from_pretrained('Xenova/claude-tokenizer')"

# Optional: Jupyter for interactive analysis
pip install jupyterlab matplotlib plotly pandas
```

## Key Environment & Data Paths

| Path / Variable | Purpose |
|-----------------|---------|
| `~/.claude/projects/<hash>/sessions/*.jsonl` | Raw session transcripts with per-message token usage |
| `~/.claude/projects/<hash>/sessions-index.json` | Session metadata (summaries, message counts, branches) |
| `ANTHROPIC_API_KEY` | Required for Token Count API and Agent SDK |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Override auto-compaction threshold (1-100) for compaction experiments |

## Research-Specific Stack Considerations

### For Tokenizer Behavior Analysis
Use the Anthropic Token Count API as ground truth, supplemented by the local `@anthropic-ai/tokenizer` for pattern exploration. Compare how the same text tokenizes differently: code vs. prose, whitespace variations, special characters, compressed vs. natural language. The local tokenizer is "wrong" for Claude 3+ in absolute terms but useful for understanding BPE mechanics.

### For System Prompt Overhead Measurement
Use the Token Count API with constructed message payloads. Start with a minimal payload, then incrementally add components (system prompt, tool definitions, MCP schemas, CLAUDE.md content) and measure the delta each time. Cross-reference against Piebald-AI's documented token counts.

### For Prompt Strategy Benchmarking
Use the Claude Agent SDK to programmatically run the same task with different prompt strategies. Each `query()` returns authoritative `total_cost_usd` and per-step token breakdowns. Run multiple trials per strategy for statistical significance.

### For Context Window & Compaction Research
Use `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` to control when compaction fires. Run identical long sessions with different compaction thresholds. Compare context usage via `/context` command and JSONL transcript analysis. DuckDB is ideal for comparing token trajectories across sessions.

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
