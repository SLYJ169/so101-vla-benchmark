#!/usr/bin/env python3
"""Summarize a real-robot trial CSV using final completion only."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    with args.csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit("No trials found.")

    def is_success(row: dict[str, str]) -> bool:
        value = (row.get("result") or row.get("final_result") or "").strip().upper()
        return value == "SUCCESS"

    success = sum(is_success(r) for r in rows)
    total = len(rows)
    print(f"Final completion: {success}/{total} ({100.0 * success / total:.1f}%)")


if __name__ == "__main__":
    main()
