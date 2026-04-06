#!/usr/bin/env python3
"""Measure per-tool token costs for Claude Code's 7 built-in tools.

Measures each tool's schema overhead individually using count_with_tools,
then measures cumulative overhead (1 tool, 2 tools, ... 7 tools) to check
whether tool overhead is additive or has a fixed per-tool cost.

Usage:
    python3 scripts/measure_tools.py
    python3 scripts/measure_tools.py --repeat 5
    python3 scripts/measure_tools.py --model claude-sonnet-4-6 --repeat 3
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
from count_tokens import count_with_tools

# Import tool definitions from measure_baseline
from measure_baseline import TOOL_DEFINITIONS, TOOL_BY_NAME


# ---------------------------------------------------------------------------
# Measurement helpers
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


def _generate_placeholder_data(model: str, repeat: int) -> dict:
    """Generate placeholder data when API is unavailable."""
    now = datetime.now(timezone.utc).isoformat()

    # Estimated values based on Piebald-AI research
    tool_estimates = {
        "Read": 2400,
        "Write": 1800,
        "Edit": 2100,
        "Bash": 1700,
        "Grep": 2000,
        "Glob": 1500,
        "Agent": 1600,
    }

    individual = {}
    for name, est in tool_estimates.items():
        individual[name] = {
            "schema_tokens": est,
            "description_tokens": int(est * 0.3),
            "mean": est,
            "min": est,
            "max": est,
            "stdev": 0.0,
            "measurements": [est] * repeat,
            "_estimated": True,
        }

    # Cumulative overhead (roughly additive with small fixed per-tool cost)
    sorted_tools = sorted(tool_estimates.items(), key=lambda x: x[1], reverse=True)
    cumulative = {"0_tools": 0}
    running = 0
    for i, (name, est) in enumerate(sorted_tools, 1):
        running += est
        cumulative[f"{i}_tool{'s' if i > 1 else ''}"] = running

    cumulative["overhead_per_additional_tool"] = int(
        sum(tool_estimates.values()) / len(tool_estimates)
    )

    return {
        "metadata": {
            "date": now,
            "model": model,
            "repeat_count": repeat,
            "source": "estimated (ANTHROPIC_API_KEY not set)",
        },
        "individual_tools": individual,
        "cumulative_overhead": cumulative,
    }


# ---------------------------------------------------------------------------
# Live measurement
# ---------------------------------------------------------------------------

def measure_tool_costs(model: str, repeat: int) -> dict:
    """Measure per-tool token costs using count_with_tools.

    Args:
        model: Model to use for tokenization.
        repeat: Number of measurement repetitions.

    Returns:
        Dict with individual_tools and cumulative_overhead.
    """
    now = datetime.now(timezone.utc).isoformat()

    tool_names = ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Agent"]

    print(f"\nMeasuring per-tool token costs (model={model}, repeat={repeat})")
    print("=" * 65)

    # Individual tool measurements
    individual = {}
    for name in tool_names:
        print(f"  {name} ...", end=" ", flush=True)
        tool_def = TOOL_BY_NAME[name]
        stats = _measure_n_times(
            lambda td=tool_def: count_with_tools([td], model=model)["tool_overhead"],
            repeat,
        )
        individual[name] = {
            "schema_tokens": stats["mean"],
            "description_tokens": 0,  # Would need separate measurement to isolate
            **stats,
        }
        print(f"{stats['mean']:.0f} tokens")

    # Cumulative overhead: measure with 0, 1, 2, ... 7 tools
    print("\n  Cumulative overhead:")
    # Sort tools by individual cost (descending) for cumulative test
    sorted_tool_names = sorted(
        tool_names,
        key=lambda n: individual[n]["schema_tokens"],
        reverse=True,
    )

    cumulative = {}

    # 0 tools baseline
    print(f"    0 tools ...", end=" ", flush=True)
    baseline = _measure_n_times(
        lambda: count_with_tools([], model=model)["tool_overhead"],
        repeat,
    )
    cumulative["0_tools"] = baseline["mean"]
    print(f"{baseline['mean']:.0f} tokens")

    # Add tools one at a time
    tool_list = []
    for i, name in enumerate(sorted_tool_names, 1):
        tool_list.append(TOOL_BY_NAME[name])
        label = f"{i}_tool{'s' if i > 1 else ''}"
        print(f"    {label} ({name}) ...", end=" ", flush=True)
        stats = _measure_n_times(
            lambda tl=list(tool_list): count_with_tools(tl, model=model)["tool_overhead"],
            repeat,
        )
        cumulative[label] = stats["mean"]
        print(f"{stats['mean']:.0f} tokens")

    # Calculate average overhead per additional tool
    if len(cumulative) > 1:
        keys = sorted(cumulative.keys())
        deltas = []
        for j in range(1, len(keys)):
            if keys[j] == "overhead_per_additional_tool":
                continue
            deltas.append(cumulative[keys[j]] - cumulative[keys[j - 1]])
        avg_per_tool = statistics.mean(deltas) if deltas else 0
        cumulative["overhead_per_additional_tool"] = avg_per_tool

    print("=" * 65)

    # Print comparison table
    print("\n  Tool Cost Comparison (sorted by cost):")
    print("  " + "-" * 40)
    sorted_tools = sorted(individual.items(), key=lambda x: x[1]["schema_tokens"], reverse=True)
    for name, data in sorted_tools:
        bar = "#" * int(data["schema_tokens"] / 100)
        print(f"    {name:6s} | {data['schema_tokens']:6.0f} tokens | {bar}")
    print("  " + "-" * 40)
    total = sum(d["schema_tokens"] for d in individual.values())
    print(f"    {'TOTAL':6s} | {total:6.0f} tokens")

    return {
        "metadata": {
            "date": now,
            "model": model,
            "repeat_count": repeat,
            "source": "live (Anthropic count_tokens API)",
        },
        "individual_tools": individual,
        "cumulative_overhead": cumulative,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Measure per-tool token costs for Claude Code built-in tools",
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
        help="Measurement repetitions per tool (default: 3)",
    )
    parser.add_argument(
        "--output",
        default="data/baselines/tool_costs.json",
        help="Output JSON file path",
    )
    args = parser.parse_args()

    if _api_available():
        data = measure_tool_costs(model=args.model, repeat=args.repeat)
    else:
        print("\nWARNING: ANTHROPIC_API_KEY not set. Generating placeholder data.")
        print("Set the key and re-run for real measurements.\n")
        data = _generate_placeholder_data(model=args.model, repeat=args.repeat)

    # Save JSON
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\nTool cost data saved to {args.output}")


if __name__ == "__main__":
    main()
