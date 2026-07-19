from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import ConfigError, load_project_config, resolve_profile
from .transports import execute_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="firmware-lifter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available profiles")

    run_parser = subparsers.add_parser("run", help="Run a profile")
    run_parser.add_argument("profile", help="Profile name")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path.cwd()

    try:
        if args.command == "list":
            project = load_project_config(root)
            for name in sorted(project.profiles):
                print(name)
            return 0

        if args.command == "run":
            profile = resolve_profile(root, args.profile)
            execute_profile(profile)
            return 0
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
