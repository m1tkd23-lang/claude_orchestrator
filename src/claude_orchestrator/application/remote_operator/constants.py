# src\claude_orchestrator\application\remote_operator\constants.py
from __future__ import annotations

MENU_MAIN = "main"
MENU_IN_PROGRESS_TASK_LIST = "in_progress_task_list"
MENU_COMPLETED_TASK_LIST = "completed_task_list"
MENU_TASK_LIST = "task_list"
MENU_SELECTED_TASK = "selected_task"
MENU_PROPOSAL_LIST = "proposal_list"
MENU_SELECTED_PROPOSAL = "selected_proposal"
MENU_CREATED_TASK = "created_task"
MENU_POST_RUN = "post_run"

MENU_POST_PIPELINE = "post_pipeline"
MENU_PLAN_DIRECTOR_RESULT = "plan_director_result"
MENU_NEXT_TASK_APPROVAL = "next_task_approval"
MENU_PIPELINE_SETTINGS = "pipeline_settings"

MENU_EXITED = "exited"

DEFAULT_MENU = MENU_MAIN

PLANNER_SAFE = "planner_safe"
PLANNER_IMPROVEMENT = "planner_improvement"
PLANNER_ROLES = {PLANNER_SAFE, PLANNER_IMPROVEMENT}
DEFAULT_PLANNER_ROLE = PLANNER_SAFE