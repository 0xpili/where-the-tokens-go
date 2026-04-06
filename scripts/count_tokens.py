#!/usr/bin/env python3
"""Reusable count_tokens API wrapper with progressive payload building.

Uses Anthropic's count_tokens API (POST /v1/messages/count_tokens) for
ground-truth input token counting. This is the authoritative measurement
tool for component-level token analysis.

Functions:
    count_tokens     - Count input tokens for a complete message payload
    measure_delta    - Measure token delta when adding a component
    count_with_tools - Count tokens with specific tool definitions
    count_system_prompt - Count tokens for a system prompt in isolation

CLI usage:
    python count_tokens.py text "Hello world"
    python count_tokens.py file path/to/file.txt
    python count_tokens.py system "You are a helpful assistant."
    python count_tokens.py text "Hello" --model claude-sonnet-4-6 --repeat 5
"""

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Optional

import anthropic

DEFAULT_MODEL = "claude-sonnet-4-6"

client = anthropic.Anthropic()


def count_tokens(
    messages: list[dict],
    system: Optional[str] = None,
    tools: Optional[list[dict]] = None,
    model: str = DEFAULT_MODEL,
) -> int:
    """Count input tokens for a complete message payload.

    Args:
        messages: List of message dicts with role and content.
        system: Optional system prompt text.
        tools: Optional list of tool definition dicts.
        model: Model to use for tokenization.

    Returns:
        Integer token count.
    """
    kwargs: dict = {"model": model, "messages": messages}
    if system is not None:
        kwargs["system"] = system
    if tools is not None:
        kwargs["tools"] = tools
    response = client.messages.count_tokens(**kwargs)
    return response.input_tokens


def measure_delta(
    base_kwargs: dict,
    addition_key: str,
    addition_value,
    model: str = DEFAULT_MODEL,
) -> int:
    """Measure token delta when adding a component to a base payload.

    Used for progressive payload building per D-15 to isolate the
    token cost of individual components (system prompts, tools, etc.).

    Args:
        base_kwargs: Base keyword arguments (system, tools, etc.).
        addition_key: Key to add (e.g., 'system', 'tools').
        addition_value: Value to add for the key.
        model: Model to use for tokenization.

    Returns:
        Integer token difference (positive means addition_value added tokens).
    """
    base_count = count_tokens(
        messages=[{"role": "user", "content": "Hello"}],
        **{k: v for k, v in base_kwargs.items() if k != "messages"},
        model=model,
    )
    modified = {**base_kwargs, addition_key: addition_value}
    modified_count = count_tokens(
        messages=[{"role": "user", "content": "Hello"}],
        **{k: v for k, v in modified.items() if k != "messages"},
        model=model,
    )
    return modified_count - base_count


def count_with_tools(
    tool_definitions: list[dict],
    system: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Count tokens with specific tool definitions.

    Args:
        tool_definitions: List of tool definition dicts.
        system: Optional system prompt text.
        model: Model to use for tokenization.

    Returns:
        Dict with total_tokens, base_tokens (no tools), tool_overhead.
    """
    base = count_tokens(
        messages=[{"role": "user", "content": "Hello"}],
        system=system,
        model=model,
    )
    with_tools = count_tokens(
        messages=[{"role": "user", "content": "Hello"}],
        system=system,
        tools=tool_definitions,
        model=model,
    )
    return {
        "total_tokens": with_tools,
        "base_tokens": base,
        "tool_overhead": with_tools - base,
    }


def count_system_prompt(
    system_text: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Count tokens for a system prompt in isolation.

    Args:
        system_text: The system prompt text.
        model: Model to use for tokenization.

    Returns:
        Dict with total_tokens, base_tokens (no system), system_overhead.
    """
    base = count_tokens(
        messages=[{"role": "user", "content": "Hello"}],
        model=model,
    )
    with_system = count_tokens(
        messages=[{"role": "user", "content": "Hello"}],
        system=system_text,
        model=model,
    )
    return {
        "total_tokens": with_system,
        "base_tokens": base,
        "system_overhead": with_system - base,
    }


def _run_repeated(func, n: int) -> dict:
    """Run a measurement function N times and report statistics.

    Per D-07: multiple measurements taken to establish variance/confidence.

    Args:
        func: Callable returning an int (token count) or dict.
        n: Number of repetitions.

    Returns:
        Dict with measurements, mean, min, max, stdev (if n > 1).
    """
    results = [func() for _ in range(n)]

    # Handle both int results and dict results
    if isinstance(results[0], int):
        values = results
        result = {
            "input_tokens": values[0],
            "measurements": values,
            "repeat": n,
        }
        if n > 1:
            result["mean"] = statistics.mean(values)
            result["min"] = min(values)
            result["max"] = max(values)
            result["stdev"] = statistics.stdev(values) if n > 2 else 0.0
        return result
    else:
        # Dict results -- just return the last one with all measurements
        result = results[-1]
        result["repeat"] = n
        if n > 1:
            # Extract primary metric for stats
            primary_key = next(
                (k for k in ("input_tokens", "total_tokens", "system_overhead", "tool_overhead") if k in result),
                None,
            )
            if primary_key:
                values = [r[primary_key] for r in results]
                result["measurements"] = values
                result["mean"] = statistics.mean(values)
                result["min"] = min(values)
                result["max"] = max(values)
                result["stdev"] = statistics.stdev(values) if n > 2 else 0.0
        return result


def cmd_text(args: argparse.Namespace) -> dict:
    """Count tokens for a simple user message."""
    return _run_repeated(
        lambda: count_tokens(
            messages=[{"role": "user", "content": args.text}],
            model=args.model,
        ),
        args.repeat,
    )


def cmd_file(args: argparse.Namespace) -> dict:
    """Read a file and count tokens for it as a user message."""
    content = Path(args.path).read_text()
    return _run_repeated(
        lambda: count_tokens(
            messages=[{"role": "user", "content": content}],
            model=args.model,
        ),
        args.repeat,
    )


def cmd_system(args: argparse.Namespace) -> dict:
    """Measure system prompt overhead."""
    return _run_repeated(
        lambda: count_system_prompt(args.text, model=args.model),
        args.repeat,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Count tokens using Anthropic's count_tokens API",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model for tokenization (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Run N times and report mean/min/max (default: 1)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # text subcommand
    p_text = subparsers.add_parser("text", help="Count tokens for text")
    p_text.add_argument("text", help="Text to count tokens for")
    p_text.set_defaults(func=cmd_text)

    # file subcommand
    p_file = subparsers.add_parser("file", help="Count tokens for a file")
    p_file.add_argument("path", help="Path to file")
    p_file.set_defaults(func=cmd_file)

    # system subcommand
    p_sys = subparsers.add_parser("system", help="Measure system prompt overhead")
    p_sys.add_argument("text", help="System prompt text")
    p_sys.set_defaults(func=cmd_system)

    args = parser.parse_args()
    result = args.func(args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
