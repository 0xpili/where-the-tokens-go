#!/usr/bin/env python3
"""Measure Claude Code's baseline token overhead at component level.

Uses progressive payload building (add one component at a time, measure the
delta) to isolate per-component costs. Per D-07, each measurement is repeated
N times to establish variance.

Components measured (per D-05):
  - Empty baseline (absolute minimum)
  - System prompt (Claude Code core system prompt)
  - Built-in tool schemas (all 7, plus each individually)
  - CLAUDE.md at different sizes (small ~100, medium ~500, large ~2000 tokens)
  - Memory (MEMORY.md) content
  - MCP server overhead (1 server/3 tools, 3 servers/10 tools)
  - Environment info

Usage:
    python3 scripts/measure_baseline.py
    python3 scripts/measure_baseline.py --repeat 5
    python3 scripts/measure_baseline.py --model claude-sonnet-4-6 --repeat 3
    python3 scripts/measure_baseline.py --report  # also generate baseline-report.md
"""

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts/ to sys.path so we can import count_tokens
sys.path.insert(0, str(Path(__file__).parent))
from count_tokens import count_tokens, measure_delta, count_with_tools, count_system_prompt

# ---------------------------------------------------------------------------
# Tool schema definitions matching Claude Code's 7 built-in tools
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "Read",
        "description": (
            "Reads a file from the local filesystem. You can access any file "
            "directly by using this tool. The file_path parameter must be an "
            "absolute path, not a relative path."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to read",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of lines to read (optional)",
                },
                "offset": {
                    "type": "integer",
                    "description": "The line number to start reading from (optional)",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "Write",
        "description": (
            "Writes a file to the local filesystem. This tool will overwrite "
            "the existing file if there is one at the provided path. Use the "
            "Read tool first to read a file before overwriting it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file",
                },
            },
            "required": ["file_path", "content"],
        },
    },
    {
        "name": "Edit",
        "description": (
            "Performs exact string replacements in files. The edit will fail if "
            "old_text is not unique in the file. Use a larger surrounding context "
            "to make it unique or use replace_all to change every instance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to modify",
                },
                "old_text": {
                    "type": "string",
                    "description": "The text to replace",
                },
                "new_text": {
                    "type": "string",
                    "description": "The text to replace it with",
                },
            },
            "required": ["file_path", "old_text", "new_text"],
        },
    },
    {
        "name": "Bash",
        "description": (
            "Executes a given bash command and returns its output. The shell "
            "environment is initialized from the user's profile. Avoid using "
            "this for tasks that have dedicated tools."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Optional timeout in milliseconds (max 600000)",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "Grep",
        "description": (
            "A powerful search tool built on ripgrep. Supports full regex "
            "syntax and filters files with glob or type parameters. Use this "
            "for content search tasks instead of bash grep."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The regex pattern to search for in file contents",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in (optional)",
                },
                "include": {
                    "type": "string",
                    "description": "Glob pattern to filter files (optional, e.g. '*.js')",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "Glob",
        "description": (
            "Fast file pattern matching tool that works with any codebase size. "
            "Supports glob patterns like '**/*.js' or 'src/**/*.ts'. Returns "
            "matching file paths sorted by modification time."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The glob pattern to match files against",
                },
                "path": {
                    "type": "string",
                    "description": "The directory to search in (optional)",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "Agent",
        "description": (
            "Launch a new agent that has access to all the same tools. Use this "
            "for tasks that can be parallelized or that require exploring "
            "multiple approaches. The agent receives a task description and context."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The task for the agent to perform",
                },
                "context": {
                    "type": "string",
                    "description": "Additional context for the agent (optional)",
                },
            },
            "required": ["task"],
        },
    },
]

# Tool name to definition lookup
TOOL_BY_NAME = {t["name"]: t for t in TOOL_DEFINITIONS}

# ---------------------------------------------------------------------------
# Representative content for system prompt components
# ---------------------------------------------------------------------------

# Representative Claude Code system prompt (core identity + safety + tool instructions)
SYSTEM_PROMPT_CORE = """\
You are Claude Code, an interactive CLI tool that helps users with software engineering tasks. \
You can read and write files, execute commands, search codebases, and interact with the user. \
You are powered by Claude, Anthropic's AI assistant.

Your primary goals are:
1. Help users accomplish their coding tasks efficiently and correctly
2. Follow security best practices and never execute dangerous commands without confirmation
3. Use the appropriate tool for each task (Read for files, Grep for search, etc.)
4. Provide clear explanations of what you're doing and why

Safety guidelines:
- Never execute commands that could damage the system or delete important data without explicit user confirmation
- Do not access or modify files outside the project directory without permission
- Respect .gitignore patterns and do not commit sensitive files
- When encountering credentials or API keys, warn the user about security risks

Tool usage instructions:
- Use Read to examine file contents before modifying them
- Use Edit for targeted changes to existing files (preferred over Write for modifications)
- Use Bash for running commands, tests, and build tools
- Use Grep for searching file contents with regex patterns
- Use Glob for finding files by name patterns
- Use Write only for creating new files or complete rewrites
- Use Agent for parallelizable subtasks

Environment context:
- Working directory is the user's project root
- Git repository status is available
- The user's shell profile has been loaded
"""

# CLAUDE.md content at different sizes
CLAUDE_MD_SMALL = """\
## Project
Build a REST API with Node.js.

## Conventions
- Use TypeScript
- Follow ESLint rules
"""

CLAUDE_MD_MEDIUM = """\
## Project
Token Optimization Research for Claude Code -- a deep-dive research project exploring techniques \
to reduce token consumption when using Claude Code without sacrificing output quality or performance.

## Conventions
- Use Python 3.13 for all scripts
- Follow PEP 8 style guidelines
- Type hints required for all function signatures
- All measurements must use the Anthropic count_tokens API for ground truth
- Raw data preserved in JSON format alongside analysis
- Results presented in structured markdown tables

## Constraints
- Methodology: Findings must be backed by actual experiments or observable evidence
- Quality bar: Report must be publishable with clear writing and reproducible experiments
- Scope: Focus on techniques available to end users, not internal API changes

## Key Decisions
- count_tokens API for component-level measurement
- Statusbar JSON capture for session-level tracking
- DuckDB for cross-session statistical analysis
- Multiple measurements per component for variance estimation
"""

CLAUDE_MD_LARGE = """\
## Project
Token Optimization Research for Claude Code -- a deep-dive research project exploring techniques \
to reduce token consumption when using Claude Code without sacrificing output quality or performance. \
The project involves reverse-engineering Claude's tokenization, system prompt mechanics, tool call \
overhead, and context window behavior, then running real experiments to measure which strategies \
actually save tokens. The deliverable is a publicly shareable research report plus a practical guide.

## Core Value
Discover and validate concrete, measurable techniques that let Claude Code users stretch their \
usage limits further without losing the quality of Claude's responses.

## Requirements
- Deep analysis of Claude's tokenizer behavior (what costs more/fewer tokens)
- Reverse-engineering of Claude Code system prompt structure and overhead
- Analysis of tool call token costs (Read, Edit, Bash, Grep, Glob, Write, Agent)
- Investigation of context window mechanics (compaction, caching, conversation length)
- Catalog of input token reduction techniques (prompt engineering, context management)
- Catalog of output token reduction techniques (response style, instruction tuning)
- Creative approaches (cave talk, custom instructions, compressed prompts)
- Real experiments comparing token usage with measured results
- Comprehensive research report with methodology and findings
- Practical actionable guide with effort-vs-impact assessment

## Conventions
- Use Python 3.13 for all measurement scripts
- Follow PEP 8 style guidelines with type hints for all function signatures
- All measurements use the Anthropic count_tokens API for ground truth (D-02)
- Raw data preserved in JSON format alongside analysis (D-14)
- Results presented in structured markdown tables (D-13)
- Multiple measurements taken to establish variance/confidence intervals (D-07)
- Session-level totals compared, not per-turn, to capture compounding effects (D-09)
- Each experiment documents: task description, setup, measurement method, raw data, conclusions (D-10)

## Constraints
- Methodology: Findings must be backed by actual experiments or observable evidence
- Quality bar: Report must be publishable with clear writing, structured findings, reproducible experiments
- Scope: Focus on techniques available to end users (prompt strategies, CLAUDE.md configs, workflow patterns)

## Technology Stack
- Anthropic Python SDK for count_tokens API calls
- DuckDB for SQL analysis of session data
- ccusage for session-level token aggregation (with JSONL undercount caveats)
- jq for JSONL parsing and statusbar JSON extraction
- matplotlib for visualization
- Claude Code CLI for live session measurement via /cost, /context, statusbar

## Key Decisions
- count_tokens API for component-level measurement (D-02)
- Statusbar JSON capture for session-level tracking (D-01)
- DuckDB for cross-session statistical analysis (D-12)
- Multiple measurements per component for variance estimation (D-07)
- Before/after experiments use identical task replay (D-08)
- Control variables documented for each experiment (D-11)
- JSONL logs known to undercount by 100-174x, never used for absolute claims (D-03 caveat)
"""

MEMORY_MD = """\
# Project Memory

## Key Findings
- Baseline token overhead is approximately 27K tokens for a clean session
- Tool definitions contribute 14-17K tokens (biggest single component)
- System prompt text is approximately 2,300-3,600 tokens
- JSONL session logs undercount by 100-174x due to streaming placeholders

## Session Patterns
- Context compaction triggers at approximately 83.5% of context window
- Prompt cache has 5-minute TTL; any pause evicts the cache
- Extended thinking budget (~32K) is invisible but billed as output tokens
"""

ENVIRONMENT_INFO = """\
Platform: darwin
OS Version: Darwin 25.3.0
Shell: /bin/zsh
Working directory: /Users/user/my-project
Git repository: yes (branch: main, clean)
Node.js: v23.5.0
Python: 3.13.1
"""

# MCP server tool definitions for overhead measurement
MCP_TOOLS_1SERVER_3TOOLS = [
    {
        "name": "mcp_server1_tool1",
        "description": "A tool from MCP server 1 that reads database records.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query to execute"},
                "limit": {"type": "integer", "description": "Max rows to return"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "mcp_server1_tool2",
        "description": "A tool from MCP server 1 that writes database records.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Target table name"},
                "data": {"type": "object", "description": "Record data to insert"},
            },
            "required": ["table", "data"],
        },
    },
    {
        "name": "mcp_server1_tool3",
        "description": "A tool from MCP server 1 that searches indexed documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "filters": {"type": "object", "description": "Optional filters"},
            },
            "required": ["query"],
        },
    },
]

MCP_TOOLS_3SERVERS_10TOOLS = MCP_TOOLS_1SERVER_3TOOLS + [
    {
        "name": f"mcp_server{s}_tool{t}",
        "description": f"A tool from MCP server {s} that performs operation {t}.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input for the operation"},
            },
            "required": ["input"],
        },
    }
    for s in range(2, 4)
    for t in range(1, 5)
][:7]  # Get 7 more to total 10


# ---------------------------------------------------------------------------
# Measurement helpers
# ---------------------------------------------------------------------------

def _measure_n_times(func, n: int) -> dict:
    """Run a measurement function N times and return statistics.

    Args:
        func: Callable returning an int (token count).
        n: Number of repetitions.

    Returns:
        Dict with mean, min, max, stdev, measurements.
    """
    values = [func() for _ in range(n)]
    result = {
        "mean": statistics.mean(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 2 else 0.0,
        "measurements": values,
    }
    return result


def _api_available() -> bool:
    """Check if the Anthropic API key is set."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _generate_placeholder_data(model: str, repeat: int) -> dict:
    """Generate placeholder data structure when API is unavailable.

    Returns a data structure with the correct schema but placeholder values
    marked as estimated. This allows downstream scripts and the report
    generator to work even without live API access.
    """
    now = datetime.now(timezone.utc).isoformat()

    def _placeholder(estimated_value: int) -> dict:
        return {
            "mean": estimated_value,
            "min": estimated_value,
            "max": estimated_value,
            "stdev": 0.0,
            "measurements": [estimated_value] * repeat,
            "_estimated": True,
        }

    # Values based on Piebald-AI research and community measurements
    return {
        "metadata": {
            "date": now,
            "model": model,
            "repeat_count": repeat,
            "script_version": "1.0",
            "source": "estimated (ANTHROPIC_API_KEY not set)",
        },
        "components": {
            "empty_baseline": _placeholder(29),
            "system_prompt": _placeholder(3200),
            "all_tools": _placeholder(15500),
            "tool_Read": _placeholder(2400),
            "tool_Write": _placeholder(1800),
            "tool_Edit": _placeholder(2100),
            "tool_Bash": _placeholder(1700),
            "tool_Grep": _placeholder(2000),
            "tool_Glob": _placeholder(1500),
            "tool_Agent": _placeholder(1600),
            "claude_md_small": _placeholder(45),
            "claude_md_medium": _placeholder(220),
            "claude_md_large": _placeholder(870),
            "memory_md": _placeholder(150),
            "mcp_1server_3tools": _placeholder(900),
            "mcp_3servers_10tools": _placeholder(2800),
            "environment_info": _placeholder(60),
        },
        "total_typical_overhead": {
            "mean": 18920,
            "description": "system_prompt + all_tools + medium_claude_md (estimated)",
            "_estimated": True,
        },
    }


# ---------------------------------------------------------------------------
# Live measurement functions
# ---------------------------------------------------------------------------

def measure_all_components(model: str, repeat: int) -> dict:
    """Measure all baseline overhead components using the count_tokens API.

    Uses progressive payload building: start with empty, add one component
    at a time, measure the delta.

    Args:
        model: Model to use for tokenization.
        repeat: Number of measurement repetitions per component.

    Returns:
        Complete measurement dict with all components.
    """
    now = datetime.now(timezone.utc).isoformat()
    components = {}

    print(f"\nMeasuring baseline overhead (model={model}, repeat={repeat})")
    print("=" * 65)

    # 1. Empty baseline
    print("  empty_baseline ...", end=" ", flush=True)
    components["empty_baseline"] = _measure_n_times(
        lambda: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            model=model,
        ),
        repeat,
    )
    print(f"{components['empty_baseline']['mean']:.0f} tokens")

    # 2. System prompt overhead (delta from empty)
    print("  system_prompt ...", end=" ", flush=True)
    components["system_prompt"] = _measure_n_times(
        lambda: measure_delta(
            base_kwargs={},
            addition_key="system",
            addition_value=SYSTEM_PROMPT_CORE,
            model=model,
        ),
        repeat,
    )
    print(f"{components['system_prompt']['mean']:.0f} tokens")

    # 3. All tools together (delta from empty)
    print("  all_tools ...", end=" ", flush=True)
    components["all_tools"] = _measure_n_times(
        lambda: count_with_tools(TOOL_DEFINITIONS, model=model)["tool_overhead"],
        repeat,
    )
    print(f"{components['all_tools']['mean']:.0f} tokens")

    # 4. Individual tool measurements
    for tool_name in ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Agent"]:
        key = f"tool_{tool_name}"
        print(f"  {key} ...", end=" ", flush=True)
        tool_def = TOOL_BY_NAME[tool_name]
        components[key] = _measure_n_times(
            lambda td=tool_def: count_with_tools([td], model=model)["tool_overhead"],
            repeat,
        )
        print(f"{components[key]['mean']:.0f} tokens")

    # 5. CLAUDE.md at different sizes (delta via system prompt addition)
    for label, content in [
        ("claude_md_small", CLAUDE_MD_SMALL),
        ("claude_md_medium", CLAUDE_MD_MEDIUM),
        ("claude_md_large", CLAUDE_MD_LARGE),
    ]:
        print(f"  {label} ...", end=" ", flush=True)
        # Measure delta of adding CLAUDE.md content to the system prompt
        base_system = SYSTEM_PROMPT_CORE
        extended_system = base_system + "\n\n" + content
        components[label] = _measure_n_times(
            lambda ext=extended_system, base=base_system: (
                count_tokens(
                    messages=[{"role": "user", "content": "Hello"}],
                    system=ext,
                    model=model,
                )
                - count_tokens(
                    messages=[{"role": "user", "content": "Hello"}],
                    system=base,
                    model=model,
                )
            ),
            repeat,
        )
        print(f"{components[label]['mean']:.0f} tokens")

    # 6. Memory (MEMORY.md) overhead
    print("  memory_md ...", end=" ", flush=True)
    base_system = SYSTEM_PROMPT_CORE
    system_with_memory = base_system + "\n\n" + MEMORY_MD
    components["memory_md"] = _measure_n_times(
        lambda: (
            count_tokens(
                messages=[{"role": "user", "content": "Hello"}],
                system=system_with_memory,
                model=model,
            )
            - count_tokens(
                messages=[{"role": "user", "content": "Hello"}],
                system=base_system,
                model=model,
            )
        ),
        repeat,
    )
    print(f"{components['memory_md']['mean']:.0f} tokens")

    # 7. MCP server overhead (measured as additional tools on top of built-in tools)
    print("  mcp_1server_3tools ...", end=" ", flush=True)
    all_builtin_plus_mcp3 = TOOL_DEFINITIONS + MCP_TOOLS_1SERVER_3TOOLS
    components["mcp_1server_3tools"] = _measure_n_times(
        lambda: (
            count_with_tools(all_builtin_plus_mcp3, model=model)["tool_overhead"]
            - count_with_tools(TOOL_DEFINITIONS, model=model)["tool_overhead"]
        ),
        repeat,
    )
    print(f"{components['mcp_1server_3tools']['mean']:.0f} tokens")

    print("  mcp_3servers_10tools ...", end=" ", flush=True)
    all_builtin_plus_mcp10 = TOOL_DEFINITIONS + MCP_TOOLS_3SERVERS_10TOOLS
    components["mcp_3servers_10tools"] = _measure_n_times(
        lambda: (
            count_with_tools(all_builtin_plus_mcp10, model=model)["tool_overhead"]
            - count_with_tools(TOOL_DEFINITIONS, model=model)["tool_overhead"]
        ),
        repeat,
    )
    print(f"{components['mcp_3servers_10tools']['mean']:.0f} tokens")

    # 8. Environment info overhead
    print("  environment_info ...", end=" ", flush=True)
    system_with_env = base_system + "\n\n" + ENVIRONMENT_INFO
    components["environment_info"] = _measure_n_times(
        lambda: (
            count_tokens(
                messages=[{"role": "user", "content": "Hello"}],
                system=system_with_env,
                model=model,
            )
            - count_tokens(
                messages=[{"role": "user", "content": "Hello"}],
                system=base_system,
                model=model,
            )
        ),
        repeat,
    )
    print(f"{components['environment_info']['mean']:.0f} tokens")

    # Calculate total typical overhead
    typical_mean = (
        components["system_prompt"]["mean"]
        + components["all_tools"]["mean"]
        + components["claude_md_medium"]["mean"]
    )

    print("=" * 65)
    print(f"  Typical overhead (system + tools + medium CLAUDE.md): {typical_mean:.0f} tokens")

    return {
        "metadata": {
            "date": now,
            "model": model,
            "repeat_count": repeat,
            "script_version": "1.0",
            "source": "live (Anthropic count_tokens API)",
        },
        "components": components,
        "total_typical_overhead": {
            "mean": typical_mean,
            "description": "system_prompt + all_tools + medium_claude_md",
        },
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    baseline_path: str,
    tools_path: str,
    prompt_map_path: str | None,
    output_path: str,
) -> None:
    """Generate baseline-report.md from JSON measurement data.

    Args:
        baseline_path: Path to baseline_overhead.json.
        tools_path: Path to tool_costs.json.
        prompt_map_path: Path to system_prompt_map.json (optional).
        output_path: Path for the output report.
    """
    baseline = json.loads(Path(baseline_path).read_text())
    tools = json.loads(Path(tools_path).read_text())
    prompt_map = None
    if prompt_map_path and Path(prompt_map_path).exists():
        prompt_map = json.loads(Path(prompt_map_path).read_text())

    meta = baseline["metadata"]
    is_estimated = meta.get("source", "").startswith("estimated")
    source_note = " (ESTIMATED -- API key was not available)" if is_estimated else ""

    lines = []
    lines.append(f"# Baseline Token Overhead Measurements{source_note}")
    lines.append("")
    lines.append("## Metadata")
    lines.append("")
    lines.append(f"- **Date:** {meta['date']}")
    lines.append(f"- **Model:** {meta['model']}")
    lines.append(f"- **Measurement source:** {meta.get('source', 'live')}")
    lines.append(f"- **Repeat count:** {meta['repeat_count']}")
    lines.append(f"- **Script version:** {meta['script_version']}")
    lines.append("")

    # Table 1: Component overhead breakdown
    lines.append("## Table 1: Component Overhead Breakdown")
    lines.append("")
    total_typical = baseline["total_typical_overhead"]["mean"]
    lines.append(f"Total typical overhead (system prompt + all tools + medium CLAUDE.md): **{total_typical:.0f} tokens**")
    lines.append("")
    lines.append("| Component | Mean Tokens | Min | Max | Stdev | % of Typical |")
    lines.append("|-----------|------------|-----|-----|-------|-------------|")

    comps = baseline["components"]
    for name, data in comps.items():
        mean = data["mean"]
        pct = (mean / total_typical * 100) if total_typical > 0 else 0
        lines.append(
            f"| {name} | {mean:.0f} | {data['min']} | {data['max']} | {data['stdev']:.1f} | {pct:.1f}% |"
        )
    lines.append("")

    # Table 2: Per-tool schema costs
    lines.append("## Table 2: Per-Tool Schema Costs")
    lines.append("")
    if "individual_tools" in tools:
        lines.append("| Tool | Schema Tokens (overhead) | Rank |")
        lines.append("|------|------------------------|------|")
        ind_tools = tools["individual_tools"]
        sorted_tools = sorted(ind_tools.items(), key=lambda x: x[1].get("schema_tokens", x[1].get("mean", 0)), reverse=True)
        for rank, (tname, tdata) in enumerate(sorted_tools, 1):
            tokens = tdata.get("schema_tokens", tdata.get("mean", 0))
            lines.append(f"| {tname} | {tokens:.0f} | {rank} |")
        lines.append("")

        # Cumulative overhead
        if "cumulative_overhead" in tools:
            lines.append("### Cumulative Tool Overhead")
            lines.append("")
            lines.append("| Tools Count | Total Tokens | Marginal Cost |")
            lines.append("|-------------|-------------|---------------|")
            cum = tools["cumulative_overhead"]
            prev = 0
            for key in sorted(cum.keys()):
                if key == "overhead_per_additional_tool":
                    continue
                val = cum[key]
                marginal = val - prev if prev > 0 else val
                lines.append(f"| {key} | {val:.0f} | +{marginal:.0f} |")
                prev = val
            if "overhead_per_additional_tool" in cum:
                lines.append("")
                lines.append(f"Average overhead per additional tool: **{cum['overhead_per_additional_tool']:.0f} tokens**")
            lines.append("")

    # Table 3: Configuration comparison
    if prompt_map and "configurations" in prompt_map:
        lines.append("## Table 3: Configuration Comparison")
        lines.append("")
        lines.append("| Configuration | Tokens | Components |")
        lines.append("|--------------|--------|------------|")
        for cfg_name, cfg_data in prompt_map["configurations"].items():
            components_list = ", ".join(cfg_data.get("components", []))
            lines.append(f"| {cfg_name} | {cfg_data['tokens']:.0f} | {components_list} |")
        lines.append("")

    # Table 4: System prompt component map
    if prompt_map and "components" in prompt_map:
        lines.append("## Table 4: System Prompt Component Map")
        lines.append("")
        lines.append("| Component | Delta Tokens | Cumulative | Description |")
        lines.append("|-----------|-------------|------------|-------------|")
        for comp in prompt_map["components"]:
            desc = comp.get("description", "")
            lines.append(
                f"| {comp['name']} | {comp['tokens']:.0f} | {comp['cumulative']:.0f} | {desc} |"
            )
        lines.append("")

    # Key findings
    lines.append("## Key Findings")
    lines.append("")
    # Find biggest overhead contributor
    overhead_items = {k: v["mean"] for k, v in comps.items() if k not in ("empty_baseline",)}
    if overhead_items:
        biggest = max(overhead_items, key=overhead_items.get)
        lines.append(f"1. **Biggest overhead contributor:** {biggest} at {overhead_items[biggest]:.0f} tokens")
    lines.append(f"2. **Empty baseline:** {comps['empty_baseline']['mean']:.0f} tokens (absolute minimum with a single user message)")
    if "claude_md_small" in comps and "claude_md_large" in comps:
        small = comps["claude_md_small"]["mean"]
        large = comps["claude_md_large"]["mean"]
        ratio = large / small if small > 0 else 0
        lines.append(f"3. **CLAUDE.md scaling:** Small={small:.0f}, Large={large:.0f} tokens ({ratio:.1f}x increase)")
    if "individual_tools" in tools:
        tool_total = sum(
            v.get("schema_tokens", v.get("mean", 0))
            for v in tools["individual_tools"].values()
        )
        lines.append(f"4. **Sum of individual tools:** {tool_total:.0f} tokens (compare to all_tools={comps.get('all_tools', {}).get('mean', 'N/A')})")
    if "mcp_1server_3tools" in comps and "mcp_3servers_10tools" in comps:
        mcp3 = comps["mcp_1server_3tools"]["mean"]
        mcp10 = comps["mcp_3servers_10tools"]["mean"]
        lines.append(f"5. **MCP overhead:** 3 tools={mcp3:.0f}, 10 tools={mcp10:.0f} tokens")
    lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append("Measurements taken using Anthropic's `count_tokens` API (`POST /v1/messages/count_tokens`), ")
    lines.append("which provides ground-truth input token counts for any message payload including system prompts and tool definitions.")
    lines.append("")
    lines.append("**Progressive payload building:** Each component is isolated by measuring the delta between a base ")
    lines.append("payload (without the component) and the same payload with the component added. This ensures we measure ")
    lines.append("the exact token cost of each component in isolation.")
    lines.append("")
    lines.append(f"**Variance:** Each measurement repeated {meta['repeat_count']} time(s). Statistics (mean, min, max, stdev) ")
    lines.append("reported for each component per D-07.")
    lines.append("")
    lines.append("**Known limitations:**")
    lines.append("- System prompt text used here is a representative approximation, not the exact Claude Code system prompt")
    lines.append("- Tool definitions approximate Claude Code's built-in tools (schema structure matches, descriptions are representative)")
    lines.append("- Token counts may include system optimization tokens that are not billed (per Anthropic documentation)")
    lines.append("- Measurements are for a specific model version and may change with model updates")
    lines.append("")

    # Raw data references (per D-14)
    lines.append("## Raw Data")
    lines.append("")
    lines.append("Raw measurement data preserved for reproducibility (per D-14):")
    lines.append("")
    lines.append(f"- `data/baselines/baseline_overhead.json` -- Component overhead measurements")
    lines.append(f"- `data/baselines/tool_costs.json` -- Per-tool token costs and cumulative overhead")
    if prompt_map_path:
        lines.append(f"- `data/baselines/system_prompt_map.json` -- System prompt structure mapping")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated: {meta['date']}*")

    report_text = "\n".join(lines)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(report_text + "\n")
    print(f"\nReport written to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Measure Claude Code baseline token overhead at component level",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Model for tokenization (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="Measurement repetitions per component (default: 3)",
    )
    parser.add_argument(
        "--output",
        default="data/baselines/baseline_overhead.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Also generate results/baseline-report.md",
    )
    args = parser.parse_args()

    if _api_available():
        data = measure_all_components(model=args.model, repeat=args.repeat)
    else:
        print("\nWARNING: ANTHROPIC_API_KEY not set. Generating placeholder data.")
        print("Set the key and re-run for real measurements.\n")
        data = _generate_placeholder_data(model=args.model, repeat=args.repeat)

    # Save JSON
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\nBaseline data saved to {args.output}")

    # Optionally generate report
    if args.report:
        tools_path = str(Path(args.output).parent / "tool_costs.json")
        prompt_map_path = str(Path(args.output).parent / "system_prompt_map.json")
        if not Path(tools_path).exists():
            print(f"WARNING: {tools_path} not found. Run measure_tools.py first for complete report.")
        generate_report(
            baseline_path=args.output,
            tools_path=tools_path if Path(tools_path).exists() else args.output,
            prompt_map_path=prompt_map_path if Path(prompt_map_path).exists() else None,
            output_path="results/baseline-report.md",
        )


if __name__ == "__main__":
    main()
