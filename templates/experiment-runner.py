"""
Experiment Runner Template
Copy this file for each new experiment and customize the CONFIG section.

Encodes methodology decisions D-08 (identical task replay), D-09 (session-level
totals), D-10 (document everything), and D-11 (control variables).

Usage:
    python3 experiments/CTX-01-clear-impact/run.py --setup
    python3 experiments/CTX-01-clear-impact/run.py --condition control
    python3 experiments/CTX-01-clear-impact/run.py --condition treatment
    python3 experiments/CTX-01-clear-impact/run.py --analyze
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import duckdb

# Add scripts/ to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from count_tokens import count_tokens

# === CUSTOMIZE THIS SECTION ===
CONFIG = {
    "experiment_id": "CHANGE-ME",
    "experiment_name": "CHANGE ME: descriptive name",
    "requirement": "REQ-ID",
    "model": "claude-sonnet-4-6",
    "hypothesis": "CHANGE ME: what you expect to find",
    "task_description": "CHANGE ME: exact task for Claude Code",
    "control_variables": {
        "claude_code_version": "2.1.92",
        "mcp_servers": "none",
        "claude_md": "default",
        "memory_md": "absent",
    },
}
# === END CUSTOMIZE ===

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "token_research.duckdb"


def setup_experiment_dirs():
    """Create experiment data directories."""
    exp_dir = PROJECT_ROOT / "data" / "experiments" / CONFIG["experiment_id"]
    (exp_dir / "control").mkdir(parents=True, exist_ok=True)
    (exp_dir / "treatment").mkdir(parents=True, exist_ok=True)
    return exp_dir


def record_result(condition: str, metrics: dict):
    """Record experiment results to DuckDB.

    Per D-12: DuckDB used for cross-session statistical analysis.
    Per D-14: Raw data preserved alongside analysis.
    """
    if not DB_PATH.exists():
        print(
            f"ERROR: Database not found: {DB_PATH}\n"
            "Run 'python3 scripts/setup_duckdb.py' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = duckdb.connect(str(DB_PATH))
    conn.execute(
        """
        INSERT INTO experiments (
            experiment_id, experiment_name, experiment_date, hypothesis,
            condition, total_input_tokens, total_output_tokens,
            total_cache_creation, total_cache_read,
            session_duration_ms, turns_to_completion, compaction_events,
            model, claude_code_version, mcp_servers, claude_md_hash, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            CONFIG["experiment_id"],
            CONFIG["experiment_name"],
            datetime.now().isoformat(),
            CONFIG["hypothesis"],
            condition,
            metrics.get("total_input_tokens", 0),
            metrics.get("total_output_tokens", 0),
            metrics.get("total_cache_creation", 0),
            metrics.get("total_cache_read", 0),
            metrics.get("session_duration_ms", 0),
            metrics.get("turns_to_completion", 0),
            metrics.get("compaction_events", 0),
            CONFIG["model"],
            CONFIG["control_variables"]["claude_code_version"],
            CONFIG["control_variables"]["mcp_servers"],
            CONFIG["control_variables"].get("claude_md", ""),
            metrics.get("notes", ""),
        ],
    )
    conn.close()
    print(f"Recorded {condition} results for {CONFIG['experiment_id']}")

    # Also save raw metrics as JSON per D-14
    exp_dir = PROJECT_ROOT / "data" / "experiments" / CONFIG["experiment_id"]
    metrics_file = exp_dir / condition / "metrics.json"
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_file, "w") as f:
        json.dump(
            {
                "experiment_id": CONFIG["experiment_id"],
                "condition": condition,
                "recorded_at": datetime.now().isoformat(),
                "metrics": metrics,
                "config": CONFIG,
            },
            f,
            indent=2,
        )
    print(f"Raw metrics saved to {metrics_file}")


def analyze():
    """Compare control vs treatment results.

    Per D-09: Session-level totals compared to capture compounding effects.
    """
    if not DB_PATH.exists():
        print(
            f"ERROR: Database not found: {DB_PATH}\n"
            "Run 'python3 scripts/setup_duckdb.py' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = duckdb.connect(str(DB_PATH))
    results = conn.execute(
        """
        SELECT condition, total_input_tokens, total_output_tokens,
               total_cache_creation, total_cache_read,
               turns_to_completion, compaction_events
        FROM experiments
        WHERE experiment_id = ?
        ORDER BY condition
    """,
        [CONFIG["experiment_id"]],
    ).fetchdf()
    conn.close()

    if len(results) < 2:
        print(f"Need both control and treatment data. Have {len(results)} row(s).")
        return

    print(f"\n=== {CONFIG['experiment_name']} ===\n")
    print(results.to_string(index=False))

    control = results[results["condition"] == "control"].iloc[0]
    treatment = results[results["condition"] == "treatment"].iloc[0]

    input_delta = control["total_input_tokens"] - treatment["total_input_tokens"]
    if control["total_input_tokens"] > 0:
        pct = 100 * input_delta / control["total_input_tokens"]
        print(f"\nInput token delta: {input_delta:,} ({pct:+.1f}%)")
    print(
        f"Output token delta: {control['total_output_tokens'] - treatment['total_output_tokens']:,}"
    )

    # Confounding variable warnings
    if control["compaction_events"] > 0 or treatment["compaction_events"] > 0:
        print(
            "\nWARNING: Compaction events detected -- results may reflect compaction effects"
        )
    if control["turns_to_completion"] != treatment["turns_to_completion"]:
        print(
            f"\nNOTE: Different turn counts (control={control['turns_to_completion']}, "
            f"treatment={treatment['turns_to_completion']}) -- may affect comparison"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Experiment runner")
    parser.add_argument(
        "--condition",
        choices=["control", "treatment"],
        help="Which condition to record",
    )
    parser.add_argument(
        "--analyze", action="store_true", help="Analyze results"
    )
    parser.add_argument(
        "--setup", action="store_true", help="Create experiment directories"
    )
    args = parser.parse_args()

    if args.setup:
        exp_dir = setup_experiment_dirs()
        print(f"Created experiment directories at {exp_dir}")
    elif args.analyze:
        analyze()
    elif args.condition:
        # Interactive: prompt user to enter metrics from statusbar/cost
        print(f"Recording {args.condition} results for {CONFIG['experiment_id']}")
        print("Enter metrics (from statusbar JSON or /cost command):")
        metrics = {
            "total_input_tokens": int(input("  Total input tokens: ")),
            "total_output_tokens": int(input("  Total output tokens: ")),
            "total_cache_creation": int(input("  Cache creation tokens: ")),
            "total_cache_read": int(input("  Cache read tokens: ")),
            "session_duration_ms": int(input("  Session duration (ms): ")),
            "turns_to_completion": int(input("  Turns to completion: ")),
            "compaction_events": int(input("  Compaction events: ")),
            "notes": input("  Notes: "),
        }
        record_result(args.condition, metrics)
    else:
        parser.print_help()
