# src\claude_orchestrator\gui\main_window_planner.py
# 追加/置換 import
from claude_orchestrator.application.usecases.approve_next_task_usecase import (
    ApproveNextTaskUseCase,
)
from claude_orchestrator.application.usecases.prepare_next_task_approval_usecase import (
    PrepareNextTaskApprovalUseCase,
)
from claude_orchestrator.application.usecases.reject_next_task_usecase import (
    RejectNextTaskUseCase,
)
from claude_orchestrator.infrastructure.next_task_approval_store import (
    NextTaskApprovalStore,
)