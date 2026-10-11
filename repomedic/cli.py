from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence
from repomedic import __version__
from repomedic.core.engine import ScanEngine
from repomedic.core.models import Severity
from repomedic.reporters.console import ConsoleReporter
from repomedic.reporters.json_rep import JsonReporter
from repomedic.reporters.github import GitHubReporter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repomedic",
        description="RepoMedic - Open-source repository diagnostics toolkit",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"repomedic {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    # scan subcommand
    scan_parser = subparsers.add_parser("scan", help="Run repository diagnostics")
    scan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to repository directory (default: current directory)",
    )
    scan_parser.add_argument(
        "-f",
        "--format",
        choices=["console", "json", "github"],
        default="console",
        help="Output format (default: console)",
    )
    scan_parser.add_argument(
        "--fail-on",
        choices=["error", "warning", "none"],
        default="error",
        help="Failure threshold for exit code 1 (default: error)",
    )
    scan_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color in console output",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    
    # Default to "scan ." if no arguments provided
    args_list = list(argv) if argv is not None else sys.argv[1:]
    if not args_list:
        args_list = ["scan", "."]
    elif args_list[0] not in ("scan", "-h", "--help", "--version", "-v"):
        args_list = ["scan"] + args_list

    args = parser.parse_args(args_list)

    if args.command == "scan":
        target_path = Path(args.path)
        if not target_path.exists():
            sys.stderr.write(f"Error: Path does not exist: {target_path}\n")
            return 2
        if not target_path.is_dir():
            sys.stderr.write(f"Error: Path is not a directory: {target_path}\n")
            return 2

        engine = ScanEngine()
        result = engine.run(target_path)

        # Select reporter
        if args.format == "json":
            reporter = JsonReporter()
        elif args.format == "github":
            reporter = GitHubReporter()
        else:
            reporter = ConsoleReporter(use_color=not args.no_color)

        output = reporter.format(result)
        if output:
            print(output)

        # Evaluate exit code
        if args.fail_on == "error" and result.has_errors:
            return 1
        elif args.fail_on == "warning" and (result.has_warnings or result.has_errors):
            return 1
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
