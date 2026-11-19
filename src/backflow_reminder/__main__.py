"""Command line entry point."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .core import format_table, load_devices, report


def main(argv: list[str] | None = None) -> int:
    """Print the status table. Exit code 1 if any device is overdue."""
    parser = argparse.ArgumentParser(prog="backflow_reminder")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--warn-days", type=int, default=30)
    args = parser.parse_args(argv)
    try:
        results = report(load_devices(args.csv_file), args.as_of, args.warn_days)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(format_table(results))
    return 1 if any(r.status == "OVERDUE" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
