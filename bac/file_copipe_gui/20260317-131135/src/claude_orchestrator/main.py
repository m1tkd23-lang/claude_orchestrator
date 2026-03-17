# src\claude_orchestrator\main.py
from pathlib import Path
from claude_orchestrator.orchestrator import Orchestrator


def main():

    repo = Path(r"D:\Develop\repos\drawing_review_app")
    report_dir = Path("runtime/reports")

    orchestrator = Orchestrator(repo, report_dir)

    orchestrator.run(
        "タイトルブロック検出のスコア調整"
    )


if __name__ == "__main__":
    main()