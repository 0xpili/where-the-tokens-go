#!/usr/bin/env python3
"""Initialize the DuckDB database with the token research schema.

Per D-12: DuckDB used for cross-session statistical analysis and querying.

Usage:
    python3 scripts/setup_duckdb.py          # Create/initialize database
    python3 scripts/setup_duckdb.py --reset   # Drop all tables and recreate
    python3 scripts/setup_duckdb.py --status   # Show table info and row counts
"""

import argparse
import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "token_research.duckdb"
SCHEMA_PATH = PROJECT_ROOT / "analysis" / "schemas" / "measurements.sql"

TABLES = [
    "statusbar_captures",
    "baseline_components",
    "experiments",
    "tool_costs",
]


def setup_database(reset: bool = False) -> None:
    """Create or reinitialize the DuckDB database.

    Args:
        reset: If True, drop all tables before recreating.
    """
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema file not found: {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = duckdb.connect(str(DB_PATH))

    if reset:
        print("Resetting database -- dropping all tables...")
        for table in TABLES:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"Dropped {len(TABLES)} tables.")

    # Read and execute schema SQL
    schema_sql = SCHEMA_PATH.read_text()
    # Split on semicolons and execute each statement
    for statement in schema_sql.split(";"):
        # Strip comment-only lines, then check if SQL remains
        lines = [
            line for line in statement.strip().splitlines()
            if line.strip() and not line.strip().startswith("--")
        ]
        if lines:
            conn.execute(statement.strip())

    print(f"Database initialized: {DB_PATH}")
    print_status(conn)
    conn.close()


def print_status(conn: duckdb.DuckDBPyConnection) -> None:
    """Print table list and row counts."""
    tables = conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    print(f"\nTables ({len(table_names)}):")
    for name in sorted(table_names):
        count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name}: {count} rows")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize DuckDB for token research"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables and recreate from schema",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show table info and row counts only (no schema changes)",
    )
    args = parser.parse_args()

    if args.status:
        if not DB_PATH.exists():
            print(f"Database not found: {DB_PATH}", file=sys.stderr)
            sys.exit(1)
        conn = duckdb.connect(str(DB_PATH))
        print_status(conn)
        conn.close()
    else:
        setup_database(reset=args.reset)


if __name__ == "__main__":
    main()
