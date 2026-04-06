#!/usr/bin/env python3
"""Import statusbar JSONL captures into DuckDB.

Reads statusbar capture files from data/raw/statusbar/*.jsonl and inserts
each line into the statusbar_captures table. Handles missing/null fields
gracefully and skips duplicate captures (same session_id + capture_timestamp).

Per D-14: Raw measurement data preserved alongside analysis for reproducibility.

Usage:
    python3 scripts/import_statusbar_data.py                  # Import all JSONL files
    python3 scripts/import_statusbar_data.py --dry-run         # Show what would be imported
    python3 scripts/import_statusbar_data.py --file data/raw/statusbar/session123.jsonl
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "token_research.duckdb"
STATUSBAR_DIR = PROJECT_ROOT / "data" / "raw" / "statusbar"


def extract_fields(record: dict) -> dict:
    """Extract and flatten nested fields from a statusbar JSON record.

    Handles missing fields gracefully -- returns None for optional fields
    that may not be present (e.g., current_usage is null before first API call).

    Args:
        record: Parsed JSON dict from a statusbar JSONL line.

    Returns:
        Dict with flattened field names matching the statusbar_captures schema.
    """
    # Safe nested access helpers
    model = record.get("model", {}) or {}
    cost = record.get("cost", {}) or {}
    ctx = record.get("context_window", {}) or {}
    usage = ctx.get("current_usage", {}) or {}
    rate = record.get("rate_limits", {}) or {}
    five_hour = rate.get("five_hour", {}) or {}

    # Parse capture_timestamp if present (added by capture_statusbar.sh)
    ts_str = record.get("capture_timestamp")
    capture_ts = None
    if ts_str:
        try:
            capture_ts = datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            capture_ts = None

    return {
        "session_id": record.get("session_id"),
        "capture_timestamp": capture_ts,
        "model_id": model.get("id"),
        "model_display_name": model.get("display_name"),
        "claude_code_version": record.get("version"),
        "total_cost_usd": cost.get("total_cost_usd"),
        "total_duration_ms": cost.get("total_duration_ms"),
        "total_input_tokens": ctx.get("total_input_tokens"),
        "total_output_tokens": ctx.get("total_output_tokens"),
        "context_window_size": ctx.get("context_window_size"),
        "used_percentage": ctx.get("used_percentage"),
        "current_input_tokens": usage.get("input_tokens"),
        "current_output_tokens": usage.get("output_tokens"),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "five_hour_used_pct": five_hour.get("used_percentage"),
        "transcript_path": record.get("transcript_path"),
    }


def get_existing_keys(conn: duckdb.DuckDBPyConnection) -> set:
    """Get set of (session_id, capture_timestamp) already in the database.

    Used for duplicate detection -- skip captures already imported.
    """
    try:
        rows = conn.execute(
            "SELECT session_id, capture_timestamp FROM statusbar_captures"
        ).fetchall()
        return {(r[0], r[1]) for r in rows}
    except duckdb.CatalogException:
        return set()


def import_file(
    conn: duckdb.DuckDBPyConnection,
    filepath: Path,
    existing_keys: set,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """Import a single JSONL file into the statusbar_captures table.

    Args:
        conn: DuckDB connection.
        filepath: Path to the JSONL file.
        existing_keys: Set of (session_id, timestamp) already in DB.
        dry_run: If True, don't actually insert.

    Returns:
        Tuple of (lines_processed, rows_inserted, rows_skipped).
    """
    lines_processed = 0
    rows_inserted = 0
    rows_skipped = 0

    with open(filepath) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(
                    f"  WARNING: {filepath.name}:{line_num} -- invalid JSON: {e}",
                    file=sys.stderr,
                )
                continue

            lines_processed += 1
            fields = extract_fields(record)

            # Skip if no session_id (required field)
            if not fields["session_id"]:
                print(
                    f"  WARNING: {filepath.name}:{line_num} -- missing session_id, skipped",
                    file=sys.stderr,
                )
                rows_skipped += 1
                continue

            # Check for duplicates
            key = (fields["session_id"], fields["capture_timestamp"])
            if key in existing_keys:
                rows_skipped += 1
                continue

            if not dry_run:
                conn.execute(
                    """
                    INSERT INTO statusbar_captures (
                        session_id, capture_timestamp, model_id, model_display_name,
                        claude_code_version, total_cost_usd, total_duration_ms,
                        total_input_tokens, total_output_tokens, context_window_size,
                        used_percentage, current_input_tokens, current_output_tokens,
                        cache_creation_input_tokens, cache_read_input_tokens,
                        five_hour_used_pct, transcript_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        fields["session_id"],
                        fields["capture_timestamp"],
                        fields["model_id"],
                        fields["model_display_name"],
                        fields["claude_code_version"],
                        fields["total_cost_usd"],
                        fields["total_duration_ms"],
                        fields["total_input_tokens"],
                        fields["total_output_tokens"],
                        fields["context_window_size"],
                        fields["used_percentage"],
                        fields["current_input_tokens"],
                        fields["current_output_tokens"],
                        fields["cache_creation_input_tokens"],
                        fields["cache_read_input_tokens"],
                        fields["five_hour_used_pct"],
                        fields["transcript_path"],
                    ],
                )

            existing_keys.add(key)
            rows_inserted += 1

    return lines_processed, rows_inserted, rows_skipped


def main():
    parser = argparse.ArgumentParser(
        description="Import statusbar JSONL captures into DuckDB"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without inserting",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Import a specific JSONL file (default: all files in data/raw/statusbar/)",
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(
            f"ERROR: Database not found: {DB_PATH}\n"
            "Run 'python3 scripts/setup_duckdb.py' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = duckdb.connect(str(DB_PATH))
    existing_keys = get_existing_keys(conn)

    # Determine files to process
    if args.file:
        if not args.file.exists():
            print(f"ERROR: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        files = [args.file]
    else:
        files = sorted(STATUSBAR_DIR.glob("*.jsonl"))
        if not files:
            print(f"No JSONL files found in {STATUSBAR_DIR}")
            conn.close()
            return

    mode = "DRY RUN" if args.dry_run else "IMPORT"
    print(f"[{mode}] Processing {len(files)} file(s)...\n")

    total_lines = 0
    total_inserted = 0
    total_skipped = 0

    for filepath in files:
        lines, inserted, skipped = import_file(
            conn, filepath, existing_keys, dry_run=args.dry_run
        )
        total_lines += lines
        total_inserted += inserted
        total_skipped += skipped
        status = f"  {filepath.name}: {lines} lines, {inserted} inserted, {skipped} skipped"
        print(status)

    print(f"\nSummary:")
    print(f"  Files processed: {len(files)}")
    print(f"  Lines processed: {total_lines}")
    print(f"  Rows inserted: {total_inserted}")
    print(f"  Rows skipped (duplicates): {total_skipped}")

    if not args.dry_run:
        row_count = conn.execute(
            "SELECT COUNT(*) FROM statusbar_captures"
        ).fetchone()[0]
        print(f"  Total rows in statusbar_captures: {row_count}")

    conn.close()


if __name__ == "__main__":
    main()
