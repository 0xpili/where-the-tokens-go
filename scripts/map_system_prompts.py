#!/usr/bin/env python3
"""Map Claude Code's system prompt structure with per-component token counts.

Uses progressive payload building per D-15: start with empty system prompt,
add components one at a time, measure the delta. Per D-16, also measures
how counts change with different configurations (MCP, tools, memory).

The script maps the system prompt structure by building payloads progressively:
  1. Empty baseline
  2. Core identity/role text
  3. Safety guidelines
  4. Tool usage instructions
  5. Environment context
  6. CLAUDE.md content
  7. Memory (MEMORY.md) content

Outputs:
  - data/baselines/system_prompt_map.json with component breakdown and
    configuration comparisons
  - Optionally generates results/baseline-report.md (when called with --report)

Usage:
    python3 scripts/map_system_prompts.py
    python3 scripts/map_system_prompts.py --prompt-file path/to/prompt.txt
    python3 scripts/map_system_prompts.py --repeat 5
    python3 scripts/map_system_prompts.py --report
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
from count_tokens import count_tokens, count_system_prompt
from measure_baseline import (
    TOOL_DEFINITIONS,
    CLAUDE_MD_SMALL,
    CLAUDE_MD_MEDIUM,
    CLAUDE_MD_LARGE,
    MEMORY_MD,
    MCP_TOOLS_1SERVER_3TOOLS,
    MCP_TOOLS_3SERVERS_10TOOLS,
    generate_report,
)


# ---------------------------------------------------------------------------
# System prompt components (progressive breakdown)
# ---------------------------------------------------------------------------

# These approximate the structure of Claude Code's system prompt.
# When --prompt-file is provided, that overrides these defaults.

COMPONENT_CORE_IDENTITY = """\
You are Claude Code, an interactive CLI tool that helps users with software \
engineering tasks. You can read and write files, execute commands, search \
codebases, and interact with the user. You are powered by Claude, Anthropic's \
AI assistant.

Your primary goals are:
1. Help users accomplish their coding tasks efficiently and correctly
2. Provide clear explanations of what you're doing and why
3. Maintain the user's trust through transparency and reliability
"""

COMPONENT_SAFETY = """\
Safety guidelines:
- Never execute commands that could damage the system or delete important data \
without explicit user confirmation
- Do not access or modify files outside the project directory without permission
- Respect .gitignore patterns and do not commit sensitive files like .env or \
credentials
- When encountering credentials or API keys, warn the user about security risks
- Do not run destructive git commands (push --force, reset --hard) without \
explicit permission
- Verify file paths before writing to prevent accidental overwrites
"""

COMPONENT_TOOL_INSTRUCTIONS = """\
Tool usage instructions:
- Use Read to examine file contents before modifying them. The file_path \
parameter must be an absolute path.
- Use Edit for targeted changes to existing files. This is preferred over \
Write for modifications. The edit will fail if old_text is not unique.
- Use Bash for running commands, tests, and build tools. Avoid using it for \
tasks that have dedicated tools.
- Use Grep for searching file contents with regex patterns. Supports glob \
and type filtering.
- Use Glob for finding files by name patterns. Returns paths sorted by \
modification time.
- Use Write only for creating new files or complete rewrites. Always read \
the file first before overwriting.
- Use Agent for parallelizable subtasks that can be delegated. The agent \
has access to all the same tools.

When making function calls, check that all required parameters are provided. \
If multiple independent calls are needed, make them in the same block for \
efficiency.
"""

COMPONENT_ENVIRONMENT = """\
Environment context:
- Platform: darwin (macOS)
- OS Version: Darwin 25.3.0
- Shell: /bin/zsh
- Working directory: /Users/user/project
- Git repository: yes (branch: main, clean working tree)
- Node.js: v23.5.0
- Python: 3.13.1
- Package manager: npm
"""

# Full system prompt (all components combined)
FULL_SYSTEM_PROMPT = "\n\n".join([
    COMPONENT_CORE_IDENTITY,
    COMPONENT_SAFETY,
    COMPONENT_TOOL_INSTRUCTIONS,
    COMPONENT_ENVIRONMENT,
])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _measure_n_times(func, n: int) -> dict:
    """Run a measurement function N times and return statistics."""
    values = [func() for _ in range(n)]
    return {
        "mean": statistics.mean(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 2 else 0.0,
        "measurements": values,
    }


def _api_available() -> bool:
    """Check if the Anthropic API key is set."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _generate_placeholder_map(model: str, repeat: int) -> dict:
    """Generate placeholder system prompt map when API is unavailable."""
    now = datetime.now(timezone.utc).isoformat()

    # Estimated values based on known Claude Code overhead research
    components = [
        {"name": "empty_baseline", "tokens": 29, "cumulative": 29, "description": "Absolute minimum (single user message, no system prompt)"},
        {"name": "core_identity", "tokens": 120, "cumulative": 149, "description": "Claude Code role and behavior definition"},
        {"name": "safety_guidelines", "tokens": 130, "cumulative": 279, "description": "Safety rules and permission boundaries"},
        {"name": "tool_instructions", "tokens": 250, "cumulative": 529, "description": "Instructions for using each built-in tool"},
        {"name": "environment_context", "tokens": 60, "cumulative": 589, "description": "OS, shell, working directory, git status"},
        {"name": "claude_md_medium", "tokens": 220, "cumulative": 809, "description": "User CLAUDE.md content (medium size)"},
        {"name": "memory_md", "tokens": 150, "cumulative": 959, "description": "MEMORY.md project memory content"},
    ]

    # Add _estimated flag
    for c in components:
        c["_estimated"] = True

    configurations = {
        "minimal": {
            "tokens": 279,
            "components": ["core_identity", "safety_guidelines"],
            "_estimated": True,
        },
        "standard": {
            "tokens": 589,
            "components": ["core_identity", "safety_guidelines", "tool_instructions", "environment_context"],
            "_estimated": True,
        },
        "standard_with_claude_md": {
            "tokens": 809,
            "components": ["core_identity", "safety_guidelines", "tool_instructions", "environment_context", "claude_md_medium"],
            "_estimated": True,
        },
        "full": {
            "tokens": 959,
            "components": ["core_identity", "safety_guidelines", "tool_instructions", "environment_context", "claude_md_medium", "memory_md"],
            "_estimated": True,
        },
        "full_with_mcp": {
            "tokens": 1859,
            "components": ["core_identity", "safety_guidelines", "tool_instructions", "environment_context", "claude_md_medium", "memory_md", "mcp_3servers_10tools"],
            "_estimated": True,
        },
    }

    return {
        "metadata": {
            "date": now,
            "model": model,
            "repeat_count": repeat,
            "source": "estimated (ANTHROPIC_API_KEY not set)",
        },
        "components": components,
        "configurations": configurations,
    }


# ---------------------------------------------------------------------------
# Live measurement
# ---------------------------------------------------------------------------

def map_system_prompts(
    model: str,
    repeat: int,
    prompt_file: str | None = None,
) -> dict:
    """Map system prompt structure with per-component token counts.

    Uses progressive payload building: start with empty, add one component
    at a time, measure the cumulative total and delta.

    Args:
        model: Model for tokenization.
        repeat: Number of measurement repetitions.
        prompt_file: Optional path to a file containing system prompt text
                     (overrides built-in representative text).

    Returns:
        Dict with components list and configurations comparison.
    """
    now = datetime.now(timezone.utc).isoformat()
    source = "estimated"

    # If a prompt file is provided, load it and split into sections
    if prompt_file and Path(prompt_file).exists():
        prompt_text = Path(prompt_file).read_text()
        source = "prompt-file"
        # Use the provided text as the full prompt; we still measure
        # progressively by adding our representative components but use
        # the file content as the core identity
        core = prompt_text
        safety = ""
        tool_instr = ""
        env = ""
    else:
        source = "estimated"
        core = COMPONENT_CORE_IDENTITY
        safety = COMPONENT_SAFETY
        tool_instr = COMPONENT_TOOL_INSTRUCTIONS
        env = COMPONENT_ENVIRONMENT

    print(f"\nMapping system prompt structure (model={model}, repeat={repeat}, source={source})")
    print("=" * 65)

    components_list = []
    running_system = ""

    # 1. Empty baseline (no system prompt at all)
    print("  empty_baseline ...", end=" ", flush=True)
    baseline_stats = _measure_n_times(
        lambda: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            model=model,
        ),
        repeat,
    )
    empty_baseline = baseline_stats["mean"]
    components_list.append({
        "name": "empty_baseline",
        "tokens": 0,
        "cumulative": empty_baseline,
        "description": "Absolute minimum (single user message, no system prompt)",
        **baseline_stats,
    })
    print(f"{empty_baseline:.0f} tokens (absolute)")

    # 2. Core identity
    print("  core_identity ...", end=" ", flush=True)
    running_system = core
    core_stats = _measure_n_times(
        lambda: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            system=running_system,
            model=model,
        ),
        repeat,
    )
    core_total = core_stats["mean"]
    core_delta = core_total - empty_baseline
    components_list.append({
        "name": "core_identity",
        "tokens": core_delta,
        "cumulative": core_total,
        "description": "Claude Code role and behavior definition",
        **core_stats,
    })
    print(f"+{core_delta:.0f} tokens (cumulative: {core_total:.0f})")

    # 3. Safety guidelines
    if safety:
        print("  safety_guidelines ...", end=" ", flush=True)
        prev_total = core_total
        running_system = core + "\n\n" + safety
        safety_stats = _measure_n_times(
            lambda rs=running_system: count_tokens(
                messages=[{"role": "user", "content": "Hello"}],
                system=rs,
                model=model,
            ),
            repeat,
        )
        safety_total = safety_stats["mean"]
        safety_delta = safety_total - prev_total
        components_list.append({
            "name": "safety_guidelines",
            "tokens": safety_delta,
            "cumulative": safety_total,
            "description": "Safety rules and permission boundaries",
            **safety_stats,
        })
        print(f"+{safety_delta:.0f} tokens (cumulative: {safety_total:.0f})")
    else:
        safety_total = core_total

    # 4. Tool usage instructions
    if tool_instr:
        print("  tool_instructions ...", end=" ", flush=True)
        prev_total = safety_total
        running_system = core + "\n\n" + safety + "\n\n" + tool_instr
        tool_stats = _measure_n_times(
            lambda rs=running_system: count_tokens(
                messages=[{"role": "user", "content": "Hello"}],
                system=rs,
                model=model,
            ),
            repeat,
        )
        tool_total = tool_stats["mean"]
        tool_delta = tool_total - prev_total
        components_list.append({
            "name": "tool_instructions",
            "tokens": tool_delta,
            "cumulative": tool_total,
            "description": "Instructions for using each built-in tool",
            **tool_stats,
        })
        print(f"+{tool_delta:.0f} tokens (cumulative: {tool_total:.0f})")
    else:
        tool_total = safety_total

    # 5. Environment context
    if env:
        print("  environment_context ...", end=" ", flush=True)
        prev_total = tool_total
        running_system = core + "\n\n" + safety + "\n\n" + tool_instr + "\n\n" + env
        env_stats = _measure_n_times(
            lambda rs=running_system: count_tokens(
                messages=[{"role": "user", "content": "Hello"}],
                system=rs,
                model=model,
            ),
            repeat,
        )
        env_total = env_stats["mean"]
        env_delta = env_total - prev_total
        components_list.append({
            "name": "environment_context",
            "tokens": env_delta,
            "cumulative": env_total,
            "description": "OS, shell, working directory, git status",
            **env_stats,
        })
        print(f"+{env_delta:.0f} tokens (cumulative: {env_total:.0f})")
    else:
        env_total = tool_total

    # 6. CLAUDE.md content (medium)
    print("  claude_md_medium ...", end=" ", flush=True)
    prev_total = env_total
    full_prompt = running_system if running_system else core
    system_with_claude_md = full_prompt + "\n\n" + CLAUDE_MD_MEDIUM
    claude_md_stats = _measure_n_times(
        lambda s=system_with_claude_md: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            system=s,
            model=model,
        ),
        repeat,
    )
    claude_md_total = claude_md_stats["mean"]
    claude_md_delta = claude_md_total - prev_total
    components_list.append({
        "name": "claude_md_medium",
        "tokens": claude_md_delta,
        "cumulative": claude_md_total,
        "description": "User CLAUDE.md content (medium size)",
        **claude_md_stats,
    })
    print(f"+{claude_md_delta:.0f} tokens (cumulative: {claude_md_total:.0f})")

    # 7. Memory (MEMORY.md) content
    print("  memory_md ...", end=" ", flush=True)
    prev_total = claude_md_total
    system_with_memory = system_with_claude_md + "\n\n" + MEMORY_MD
    memory_stats = _measure_n_times(
        lambda s=system_with_memory: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            system=s,
            model=model,
        ),
        repeat,
    )
    memory_total = memory_stats["mean"]
    memory_delta = memory_total - prev_total
    components_list.append({
        "name": "memory_md",
        "tokens": memory_delta,
        "cumulative": memory_total,
        "description": "MEMORY.md project memory content",
        **memory_stats,
    })
    print(f"+{memory_delta:.0f} tokens (cumulative: {memory_total:.0f})")

    print("=" * 65)

    # --- Configuration comparisons (per D-16) ---
    print("\nConfiguration comparisons:")

    # Build configuration measurements
    configs = {}

    # Minimal: core + safety
    print("  minimal (core + safety) ...", end=" ", flush=True)
    minimal_system = core + ("\n\n" + safety if safety else "")
    minimal_stats = _measure_n_times(
        lambda s=minimal_system: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            system=s,
            model=model,
        ),
        repeat,
    )
    configs["minimal"] = {
        "tokens": minimal_stats["mean"],
        "components": ["core_identity", "safety_guidelines"],
    }
    print(f"{minimal_stats['mean']:.0f} tokens")

    # Standard: core + safety + tool instructions + environment
    print("  standard ...", end=" ", flush=True)
    standard_system = "\n\n".join(filter(None, [core, safety, tool_instr, env]))
    standard_stats = _measure_n_times(
        lambda s=standard_system: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            system=s,
            model=model,
        ),
        repeat,
    )
    configs["standard"] = {
        "tokens": standard_stats["mean"],
        "components": ["core_identity", "safety_guidelines", "tool_instructions", "environment_context"],
    }
    print(f"{standard_stats['mean']:.0f} tokens")

    # Standard + CLAUDE.md
    print("  standard + claude_md ...", end=" ", flush=True)
    std_claude_system = standard_system + "\n\n" + CLAUDE_MD_MEDIUM
    std_claude_stats = _measure_n_times(
        lambda s=std_claude_system: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            system=s,
            model=model,
        ),
        repeat,
    )
    configs["standard_with_claude_md"] = {
        "tokens": std_claude_stats["mean"],
        "components": ["core_identity", "safety_guidelines", "tool_instructions", "environment_context", "claude_md_medium"],
    }
    print(f"{std_claude_stats['mean']:.0f} tokens")

    # Full: standard + CLAUDE.md + memory
    print("  full ...", end=" ", flush=True)
    full_system = std_claude_system + "\n\n" + MEMORY_MD
    full_stats = _measure_n_times(
        lambda s=full_system: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            system=s,
            model=model,
        ),
        repeat,
    )
    configs["full"] = {
        "tokens": full_stats["mean"],
        "components": ["core_identity", "safety_guidelines", "tool_instructions", "environment_context", "claude_md_medium", "memory_md"],
    }
    print(f"{full_stats['mean']:.0f} tokens")

    # Full + MCP
    print("  full + mcp ...", end=" ", flush=True)
    # MCP adds tool definitions, not system prompt text, but we measure the
    # total overhead including both system prompt and tools
    full_mcp_stats = _measure_n_times(
        lambda s=full_system: count_tokens(
            messages=[{"role": "user", "content": "Hello"}],
            system=s,
            tools=TOOL_DEFINITIONS + MCP_TOOLS_3SERVERS_10TOOLS,
            model=model,
        ),
        repeat,
    )
    configs["full_with_mcp"] = {
        "tokens": full_mcp_stats["mean"],
        "components": ["core_identity", "safety_guidelines", "tool_instructions", "environment_context", "claude_md_medium", "memory_md", "mcp_3servers_10tools"],
    }
    print(f"{full_mcp_stats['mean']:.0f} tokens")

    print("=" * 65)

    return {
        "metadata": {
            "date": now,
            "model": model,
            "repeat_count": repeat,
            "source": source,
        },
        "components": components_list,
        "configurations": configs,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Map Claude Code system prompt structure with per-component token counts",
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
        "--prompt-file",
        default=None,
        help="Path to text file with system prompt content (overrides built-in representative text)",
    )
    parser.add_argument(
        "--output",
        default="data/baselines/system_prompt_map.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Also generate results/baseline-report.md (reads all baseline JSONs)",
    )
    args = parser.parse_args()

    if _api_available():
        data = map_system_prompts(
            model=args.model,
            repeat=args.repeat,
            prompt_file=args.prompt_file,
        )
    else:
        print("\nWARNING: ANTHROPIC_API_KEY not set. Generating placeholder data.")
        print("Set the key and re-run for real measurements.\n")
        data = _generate_placeholder_map(model=args.model, repeat=args.repeat)

    # Save JSON
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\nSystem prompt map saved to {args.output}")

    # Optionally generate the comprehensive baseline report
    if args.report:
        baseline_path = str(Path(args.output).parent / "baseline_overhead.json")
        tools_path = str(Path(args.output).parent / "tool_costs.json")

        if not Path(baseline_path).exists():
            print(f"WARNING: {baseline_path} not found. Run measure_baseline.py first.")
        if not Path(tools_path).exists():
            print(f"WARNING: {tools_path} not found. Run measure_tools.py first.")

        generate_report(
            baseline_path=baseline_path if Path(baseline_path).exists() else args.output,
            tools_path=tools_path if Path(tools_path).exists() else args.output,
            prompt_map_path=args.output,
            output_path="results/baseline-report.md",
        )


if __name__ == "__main__":
    main()
