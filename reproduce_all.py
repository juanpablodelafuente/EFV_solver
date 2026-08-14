from __future__ import annotations

"""Validate archived EFV data and recreate the figures and tables."""

import argparse
import json
from pathlib import Path

from src.data_io import ReleaseDataError
from src.workflow import reproduce


ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reproduce EFV benchmark profile figures and result tables."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate all publication inputs without creating outputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory; defaults to figures/ and tables/.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = reproduce(
            ROOT,
            check_only=args.check_only,
            output_directory=args.output_dir,
        )
    except ReleaseDataError as exc:
        print("REPRODUCTION CHECK FAILED")
        print(str(exc))
        print("\nSee data/README.md for dataset definitions and required fields.")
        return 2

    print("REPRODUCTION CHECK PASSED")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
