# src\claude_orchestrator\cli\main.py
from __future__ import annotations

import argparse

from claude_orchestrator.application.usecases.advance_task_usecase import (
    AdvanceTaskUseCase,
)
from claude_orchestrator.application.usecases.create_task_from_proposal_usecase import (
    CreateTaskFromProposalUseCase,
)
from claude_orchestrator.application.usecases.create_task_usecase import (
    CreateTaskUseCase,
)
from claude_orchestrator.application.usecases.generate_next_task_proposals_usecase import (
    GenerateNextTaskProposalsUseCase,
)
from claude_orchestrator.application.usecases.init_project_usecase import (
    InitProjectUseCase,
)
from claude_orchestrator.application.usecases.list_proposals_usecase import (
    ListProposalsUseCase,
)
from claude_orchestrator.application.usecases.run_task_usecase import (
    RunTaskUseCase,
)
from claude_orchestrator.application.usecases.show_next_usecase import (
    ShowNextUseCase,
)
from claude_orchestrator.application.usecases.status_usecase import (
    StatusUseCase,
)
from claude_orchestrator.application.usecases.validate_report_usecase import (
    ValidateReportUseCase,
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

    validate_report_parser = subparsers.add_parser(
        "validate-report",
        help="Validate current cycle report for a role.",
    )
    validate_report_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    validate_report_parser.add_argument(
        "--task-id",
        required=True,
        help="Task id, for example TASK-0001.",
    )
    validate_report_parser.add_argument(
        "--role",
        required=True,
        choices=["task_router", "implementer", "reviewer", "director"],
        help="Role name.",
    )

    advance_parser = subparsers.add_parser(
        "advance",
        help="Advance task state using current next_role report.",
    )
    advance_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    advance_parser.add_argument(
        "--task-id",
        required=True,
        help="Task id, for example TASK-0001.",
    )

    status_parser = subparsers.add_parser(
        "status",
        help="Show task status or task list.",
    )
    status_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    status_parser.add_argument(
        "--task-id",
        required=False,
        help="Task id, for example TASK-0001. If omitted, list all tasks.",
    )

    run_task_parser = subparsers.add_parser(
        "run-task",
        help="Run a task until completed or stopped using the same flow as GUI auto run.",
    )
    run_task_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    run_task_parser.add_argument(
        "--task-id",
        required=True,
        help="Task id, for example TASK-0001.",
    )

    generate_next_tasks_parser = subparsers.add_parser(
        "generate-next-tasks",
        help="Generate planner proposals from a completed task.",
    )
    generate_next_tasks_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    generate_next_tasks_parser.add_argument(
        "--task-id",
        required=True,
        help="Completed source task id, for example TASK-0010.",
    )
    generate_next_tasks_parser.add_argument(
        "--reference-doc",
        action="append",
        default=[],
        help="Reference document path relative to repo. Can be specified multiple times.",
    )

    list_proposals_parser = subparsers.add_parser(
        "list-proposals",
        help="List planner proposals for a completed task.",
    )
    list_proposals_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    list_proposals_parser.add_argument(
        "--task-id",
        required=True,
        help="Completed source task id, for example TASK-0010.",
    )

    create_task_from_proposal_parser = subparsers.add_parser(
        "create-task-from-proposal",
        help="Create a new task directly from a planner proposal.",
    )
    create_task_from_proposal_parser.add_argument(
        "--repo",
        required=True,
        help="Target repository path.",
    )
    create_task_from_proposal_parser.add_argument(
        "--task-id",
        required=True,
        help="Completed source task id, for example TASK-0010.",
    )
    create_task_from_proposal_parser.add_argument(
        "--proposal-id",
        required=True,
        help="Proposal id, for example P-001.",
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

    if args.command == "validate-report":
        usecase = ValidateReportUseCase()
        result = usecase.execute(
            repo_path=args.repo,
            task_id=args.task_id,
            role=args.role,
        )
        print(f"Valid       : {result['valid']}")
        print(f"Role        : {result['role']}")
        print(f"Cycle       : {result['cycle']}")
        print(f"Report file : {result['report_path']}")
        return

    if args.command == "advance":
        usecase = AdvanceTaskUseCase()
        result = usecase.execute(
            repo_path=args.repo,
            task_id=args.task_id,
        )
        print(f"Status      : {result['status']}")
        print(f"Current     : {result['current_stage']}")
        print(f"Next role   : {result['next_role']}")
        print(f"Cycle       : {result['cycle']}")
        print(f"State file  : {result['state_path']}")
        return

    if args.command == "status":
        usecase = StatusUseCase()

        if args.task_id:
            result = usecase.get_task_status(
                repo_path=args.repo,
                task_id=args.task_id,
            )
            print(f"Task ID     : {result['task_id']}")
            print(f"Title       : {result['title']}")
            print(f"Description : {result['description']}")
            print(f"Status      : {result['status']}")
            print(f"Current     : {result['current_stage']}")
            print(f"Next role   : {result['next_role']}")
            print(f"Cycle       : {result['cycle']}")
            print(f"Last done   : {result['last_completed_role']}")
            print(f"Max cycles  : {result['max_cycles']}")
            print(f"Task dir    : {result['task_dir']}")
            return

        results = usecase.list_tasks(repo_path=args.repo)

        if not results:
            print("No tasks found.")
            return

        for item in results:
            print(
                f"{item['task_id']} | "
                f"status={item['status']} | "
                f"current={item['current_stage']} | "
                f"next={item['next_role']} | "
                f"cycle={item['cycle']} | "
                f"title={item['title']}"
            )
        return

    if args.command == "run-task":
        usecase = RunTaskUseCase()
        result = usecase.execute(
            repo_path=args.repo,
            task_id=args.task_id,
        )
        print(f"Task ID     : {result['task_id']}")
        print(f"Status      : {result['status']}")
        print(f"Current     : {result['current_stage']}")
        print(f"Next role   : {result['next_role']}")
        print(f"Cycle       : {result['cycle']}")
        print(f"State file  : {result['state_path']}")
        return

    if args.command == "generate-next-tasks":
        usecase = GenerateNextTaskProposalsUseCase()
        result = usecase.execute(
            repo_path=args.repo,
            source_task_id=args.task_id,
            reference_doc_paths=args.reference_doc,
        )
        planner_report = result["planner_report"]
        proposals = list(planner_report.get("proposals", []) or [])

        print(f"Source Task : {result['source_task_id']}")
        print(f"Cycle       : {result['cycle']}")
        print(f"Prompt file : {result['prompt_path']}")
        print(f"Report file : {result['output_json_path']}")
        print(f"Proposal cnt: {len(proposals)}")
        print(f"Summary     : {planner_report.get('summary', '')}")
        return

    if args.command == "list-proposals":
        usecase = ListProposalsUseCase()
        result = usecase.execute(
            repo_path=args.repo,
            source_task_id=args.task_id,
        )

        print(f"Source Task : {result['source_task_id']}")
        print(f"Cycle       : {result['cycle']}")
        print(f"Report file : {result['report_path']}")
        print(f"State file  : {result['state_path']}")
        print(f"Summary     : {result['summary']}")
        print("")

        proposals = result["proposals"]
        if not proposals:
            print("No proposals found.")
            return

        for proposal in proposals:
            depends_on = ", ".join(proposal["depends_on"]) if proposal["depends_on"] else "-"
            print(
                f"{proposal['proposal_id']} | "
                f"state={proposal['state']} | "
                f"title={proposal['title']}"
            )
            if proposal["why_now"]:
                print(f"  why_now    : {proposal['why_now']}")
            print(f"  depends_on : {depends_on}")
            if proposal["description"]:
                print(f"  description: {proposal['description']}")
            print("")
        return

    if args.command == "create-task-from-proposal":
        usecase = CreateTaskFromProposalUseCase()
        result = usecase.execute(
            repo_path=args.repo,
            source_task_id=args.task_id,
            proposal_id=args.proposal_id,
        )
        print(f"Source Task : {result['source_task_id']}")
        print(f"Proposal ID : {result['proposal_id']}")
        print(f"Created Task: {result['created_task_id']}")
        print(f"Task dir    : {result['created_task_dir']}")
        print(f"Report file : {result['planner_report_path']}")
        print(f"State file  : {result['proposal_state_path']}")
        return

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()