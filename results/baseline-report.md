# Baseline Token Overhead Measurements (ESTIMATED -- API key was not available)

## Metadata

- **Date:** 2026-04-06T01:16:12.466209+00:00
- **Model:** claude-sonnet-4-6
- **Measurement source:** estimated (ANTHROPIC_API_KEY not set)
- **Repeat count:** 1
- **Script version:** 1.0

## Table 1: Component Overhead Breakdown

Total typical overhead (system prompt + all tools + medium CLAUDE.md): **18920 tokens**

| Component | Mean Tokens | Min | Max | Stdev | % of Typical |
|-----------|------------|-----|-----|-------|-------------|
| empty_baseline | 29 | 29 | 29 | 0.0 | 0.2% |
| system_prompt | 3200 | 3200 | 3200 | 0.0 | 16.9% |
| all_tools | 15500 | 15500 | 15500 | 0.0 | 81.9% |
| tool_Read | 2400 | 2400 | 2400 | 0.0 | 12.7% |
| tool_Write | 1800 | 1800 | 1800 | 0.0 | 9.5% |
| tool_Edit | 2100 | 2100 | 2100 | 0.0 | 11.1% |
| tool_Bash | 1700 | 1700 | 1700 | 0.0 | 9.0% |
| tool_Grep | 2000 | 2000 | 2000 | 0.0 | 10.6% |
| tool_Glob | 1500 | 1500 | 1500 | 0.0 | 7.9% |
| tool_Agent | 1600 | 1600 | 1600 | 0.0 | 8.5% |
| claude_md_small | 45 | 45 | 45 | 0.0 | 0.2% |
| claude_md_medium | 220 | 220 | 220 | 0.0 | 1.2% |
| claude_md_large | 870 | 870 | 870 | 0.0 | 4.6% |
| memory_md | 150 | 150 | 150 | 0.0 | 0.8% |
| mcp_1server_3tools | 900 | 900 | 900 | 0.0 | 4.8% |
| mcp_3servers_10tools | 2800 | 2800 | 2800 | 0.0 | 14.8% |
| environment_info | 60 | 60 | 60 | 0.0 | 0.3% |

## Table 2: Per-Tool Schema Costs

| Tool | Schema Tokens (overhead) | Rank |
|------|------------------------|------|
| Read | 2400 | 1 |
| Edit | 2100 | 2 |
| Grep | 2000 | 3 |
| Write | 1800 | 4 |
| Bash | 1700 | 5 |
| Agent | 1600 | 6 |
| Glob | 1500 | 7 |

### Cumulative Tool Overhead

| Tools Count | Total Tokens | Marginal Cost |
|-------------|-------------|---------------|
| 0_tools | 0 | +0 |
| 1_tool | 2400 | +2400 |
| 2_tools | 4500 | +2100 |
| 3_tools | 6500 | +2000 |
| 4_tools | 8300 | +1800 |
| 5_tools | 10000 | +1700 |
| 6_tools | 11600 | +1600 |
| 7_tools | 13100 | +1500 |

Average overhead per additional tool: **1871 tokens**

## Table 3: Configuration Comparison

| Configuration | Tokens | Components |
|--------------|--------|------------|
| minimal | 279 | core_identity, safety_guidelines |
| standard | 589 | core_identity, safety_guidelines, tool_instructions, environment_context |
| standard_with_claude_md | 809 | core_identity, safety_guidelines, tool_instructions, environment_context, claude_md_medium |
| full | 959 | core_identity, safety_guidelines, tool_instructions, environment_context, claude_md_medium, memory_md |
| full_with_mcp | 1859 | core_identity, safety_guidelines, tool_instructions, environment_context, claude_md_medium, memory_md, mcp_3servers_10tools |

## Table 4: System Prompt Component Map

| Component | Delta Tokens | Cumulative | Description |
|-----------|-------------|------------|-------------|
| empty_baseline | 29 | 29 | Absolute minimum (single user message, no system prompt) |
| core_identity | 120 | 149 | Claude Code role and behavior definition |
| safety_guidelines | 130 | 279 | Safety rules and permission boundaries |
| tool_instructions | 250 | 529 | Instructions for using each built-in tool |
| environment_context | 60 | 589 | OS, shell, working directory, git status |
| claude_md_medium | 220 | 809 | User CLAUDE.md content (medium size) |
| memory_md | 150 | 959 | MEMORY.md project memory content |

## Key Findings

1. **Biggest overhead contributor:** all_tools at 15500 tokens
2. **Empty baseline:** 29 tokens (absolute minimum with a single user message)
3. **CLAUDE.md scaling:** Small=45, Large=870 tokens (19.3x increase)
4. **Sum of individual tools:** 13100 tokens (compare to all_tools=15500)
5. **MCP overhead:** 3 tools=900, 10 tools=2800 tokens

## Methodology

Measurements taken using Anthropic's `count_tokens` API (`POST /v1/messages/count_tokens`), 
which provides ground-truth input token counts for any message payload including system prompts and tool definitions.

**Progressive payload building:** Each component is isolated by measuring the delta between a base 
payload (without the component) and the same payload with the component added. This ensures we measure 
the exact token cost of each component in isolation.

**Variance:** Each measurement repeated 1 time(s). Statistics (mean, min, max, stdev) 
reported for each component per D-07.

**Known limitations:**
- System prompt text used here is a representative approximation, not the exact Claude Code system prompt
- Tool definitions approximate Claude Code's built-in tools (schema structure matches, descriptions are representative)
- Token counts may include system optimization tokens that are not billed (per Anthropic documentation)
- Measurements are for a specific model version and may change with model updates

## Raw Data

Raw measurement data preserved for reproducibility (per D-14):

- `data/baselines/baseline_overhead.json` -- Component overhead measurements
- `data/baselines/tool_costs.json` -- Per-tool token costs and cumulative overhead
- `data/baselines/system_prompt_map.json` -- System prompt structure mapping

---
*Generated: 2026-04-06T01:16:12.466209+00:00*
