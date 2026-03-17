# src\claude_orchestrator\cli\main.py
from __future__ import annotations

import argparse

from claude_orchestrator.application.usecases.init_project_usecase import (
    InitProjectUseCase,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claude-orchestrator")

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init-project",
        help="Initialize .claude_orchestrator in a target repository.",
    )
    init_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .claude_orchestrator folder.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-project":
        usecase = InitProjectUseCase()
        target_root = usecase.execute(
            repo_path=args.repo,
            force=args.force,
        )
        print(f"Initialized: {target_root}")
        return

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()