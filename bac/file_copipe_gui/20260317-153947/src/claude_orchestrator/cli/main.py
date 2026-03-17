# src\claude_orchestrator\cli\main.py
from __future__ import annotations

import argparse

from claude_orchestrator.application.usecases.create_task_usecase import (
    CreateTaskUseCase,
)
from claude_orchestrator.application.usecases.init_project_usecase import (
    InitProjectUseCase,
)
from claude_orchestrator.application.usecases.show_next_usecase import (
    ShowNextUseCase,
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

    create_task_parser = subparsers.add_parser(
        "create-task",
        help="Create a new task in target repository.",
    )
    create_task_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    create_task_parser.add_argument(
        "--title",
        required=True,
        help="Task title.",
    )
    create_task_parser.add_argument(
        "--description",
        required=True,
        help="Task description.",
    )
    create_task_parser.add_argument(
        "--context-file",
        action="append",
        default=[],
        help="Context file path. Can be specified multiple times.",
    )
    create_task_parser.add_argument(
        "--constraint",
        action="append",
        default=[],
        help="Constraint text. Can be specified multiple times.",
    )

    show_next_parser = subparsers.add_parser(
        "show-next",
        help="Generate next prompt for current task state.",
    )
    show_next_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    show_next_parser.add_argument(
        "--task-id",
        required=True,
        help="Task id, for example TASK-0001.",
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

    if args.command == "create-task":
        usecase = CreateTaskUseCase()
        task_dir = usecase.execute(
            repo_path=args.repo,
            title=args.title,
            description=args.description,
            context_files=args.context_file,
            constraints=args.constraint,
        )
        print(f"Task created: {task_dir}")
        return

    if args.command == "show-next":
        usecase = ShowNextUseCase()
        result = usecase.execute(
            repo_path=args.repo,
            task_id=args.task_id,
        )
        print(f"Next role   : {result['role']}")
        print(f"Cycle       : {result['cycle']}")
        print(f"Prompt file : {result['prompt_path']}")
        print(f"Output json : {result['output_json_path']}")
        return

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()