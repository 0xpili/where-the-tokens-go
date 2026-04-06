#!/usr/bin/env python3
"""Verify environment for token optimization research.

Checks Python version, required packages, CLI tools, API access,
and data directories. Prints a summary table and exits 0 if all
critical checks pass, 1 otherwise.
"""

import importlib
import os
import subprocess
import sys
from pathlib import Path


def check_python_version() -> tuple[bool, str]:
    """Check Python >= 3.10."""
    v = sys.version_info
    ok = v >= (3, 10)
    return ok, f"{v.major}.{v.minor}.{v.micro}"


def check_package(name: str) -> tuple[bool, str]:
    """Check if a Python package is importable and return its version."""
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", getattr(mod, "version", "unknown"))
        return True, str(version)
    except ImportError:
        return False, "not installed"


def check_cli_tool(name: str, version_flag: str = "--version") -> tuple[bool, str]:
    """Check if a CLI tool is on PATH and return its version."""
    try:
        result = subprocess.run(
            [name, version_flag],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = (result.stdout.strip() or result.stderr.strip()).split("\n")[0]
        return True, version
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "not found"


def check_env_var(name: str) -> tuple[bool, str]:
    """Check if an environment variable is set (never print the value)."""
    val = os.environ.get(name)
    if val:
        return True, "set (value hidden)"
    return False, "NOT SET"


def check_api_access() -> tuple[bool, str]:
    """Make a minimal count_tokens API call to validate access."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False, "skipped (no API key)"
    try:
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.count_tokens(
            model="claude-sonnet-4-6",
            messages=[{"role": "user", "content": "test"}],
        )
        return True, f"count_tokens returned {response.input_tokens} tokens"
    except Exception as e:
        return False, f"API error: {e}"


def check_directory(path: str) -> tuple[bool, str]:
    """Check if a directory exists."""
    p = Path(path).expanduser()
    if p.is_dir():
        return True, str(p)
    return False, f"{p} does not exist"


def main() -> int:
    print("=" * 60)
    print("  Token Optimization Research - Environment Verification")
    print("=" * 60)
    print()

    checks: list[tuple[str, bool, str, bool]] = []
    # (name, passed, detail, is_critical)

    # Python version
    ok, detail = check_python_version()
    checks.append(("Python >= 3.10", ok, detail, True))

    # Required packages
    for pkg in ("anthropic", "duckdb", "pandas"):
        ok, detail = check_package(pkg)
        checks.append((f"Package: {pkg}", ok, detail, True))

    # CLI tools
    ok, detail = check_cli_tool("jq")
    checks.append(("CLI: jq", ok, detail, True))

    # Environment variables
    ok, detail = check_env_var("ANTHROPIC_API_KEY")
    checks.append(("ANTHROPIC_API_KEY", ok, detail, True))

    # API access (only if key is set)
    ok, detail = check_api_access()
    checks.append(("API: count_tokens", ok, detail, True))

    # Data directories
    claude_dir = Path("~/.claude/projects").expanduser()
    ok, detail = check_directory(str(claude_dir))
    checks.append(("Claude projects dir", ok, detail, False))

    # Print results table
    print(f"{'Check':<25} {'Status':<8} {'Detail'}")
    print("-" * 70)

    critical_failures = 0
    for name, passed, detail, is_critical in checks:
        status = "PASS" if passed else "FAIL"
        marker = " (!)" if (not passed and is_critical) else ""
        print(f"{name:<25} {status:<8} {detail}{marker}")
        if not passed and is_critical:
            critical_failures += 1

    print()
    if critical_failures:
        print(f"RESULT: {critical_failures} critical check(s) FAILED")
        return 1
    else:
        print("RESULT: All critical checks PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
