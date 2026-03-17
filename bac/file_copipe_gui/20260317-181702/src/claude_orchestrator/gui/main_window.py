# src\claude_orchestrator\gui\main_window.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from claude_orchestrator.application.usecases.advance_task_usecase import (
    AdvanceTaskUseCase,
)
from claude_orchestrator.application.usecases.create_task_usecase import (
    CreateTaskUseCase,
)
from claude_orchestrator.application.usecases.init_project_usecase import (
    InitProjectUseCase,
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
from claude_orchestrator.infrastructure.project_paths import ProjectPaths


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Claude Orchestrator GUI MVP")
        self.resize(1600, 950)

        self._last_prompt_path: str = ""
        self._last_output_json_path: str = ""
        self._current_task_id: str = ""
        self._last_repo_path: str = ""

        self._build_ui()
        self._connect_signals()
        self._apply_initial_state()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_layout.addWidget(self._build_repo_group())
        left_layout.addWidget(self._build_task_create_group())
        left_layout.addWidget(self._build_task_list_group(), stretch=1)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        center_layout.addWidget(self._build_task_detail_group())
        center_layout.addWidget(self._build_action_group())
        center_layout.addWidget(self._build_log_group(), stretch=1)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        right_layout.addWidget(self._build_prompt_group(), stretch=3)
        right_layout.addWidget(self._build_output_path_group())
        right_layout.addWidget(self._build_validation_group())

        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 4)

    def _build_repo_group(self) -> QGroupBox:
        group = QGroupBox("対象 repo")
        layout = QGridLayout(group)

        self.repo_path_edit = QLineEdit()
        self.repo_path_edit.setPlaceholderText(r"D:\Develop\repos\your_target_repo")

        self.btn_repo_browse = QPushButton("参照")
        self.btn_check_init = QPushButton("初期化確認")
        self.btn_init_project = QPushButton("init-project")

        layout.addWidget(QLabel("repo path"), 0, 0)
        layout.addWidget(self.repo_path_edit, 0, 1, 1, 3)
        layout.addWidget(self.btn_repo_browse, 0, 4)
        layout.addWidget(self.btn_check_init, 1, 3)
        layout.addWidget(self.btn_init_project, 1, 4)

        return group

    def _build_task_create_group(self) -> QGroupBox:
        group = QGroupBox("新規 task 作成")
        layout = QGridLayout(group)

        self.task_title_edit = QLineEdit()
        self.task_desc_edit = QPlainTextEdit()
        self.task_desc_edit.setPlaceholderText("task description")
        self.task_desc_edit.setFixedHeight(90)

        self.context_files_edit = QPlainTextEdit()
        self.context_files_edit.setPlaceholderText("1行1ファイル")
        self.context_files_edit.setFixedHeight(80)

        self.constraints_edit = QPlainTextEdit()
        self.constraints_edit.setPlaceholderText("1行1制約")
        self.constraints_edit.setFixedHeight(80)

        self.btn_create_task = QPushButton("task作成")

        layout.addWidget(QLabel("title"), 0, 0)
        layout.addWidget(self.task_title_edit, 0, 1)
        layout.addWidget(QLabel("description"), 1, 0)
        layout.addWidget(self.task_desc_edit, 1, 1)
        layout.addWidget(QLabel("context files"), 2, 0)
        layout.addWidget(self.context_files_edit, 2, 1)
        layout.addWidget(QLabel("constraints"), 3, 0)
        layout.addWidget(self.constraints_edit, 3, 1)
        layout.addWidget(self.btn_create_task, 4, 1)

        return group

    def _build_task_list_group(self) -> QGroupBox:
        group = QGroupBox("task 一覧")
        layout = QVBoxLayout(group)

        top_row = QHBoxLayout()
        self.btn_refresh_tasks = QPushButton("一覧更新")
        top_row.addStretch()
        top_row.addWidget(self.btn_refresh_tasks)

        self.task_list_widget = QListWidget()
        self.task_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addLayout(top_row)
        layout.addWidget(self.task_list_widget)

        return group

    def _build_task_detail_group(self) -> QGroupBox:
        group = QGroupBox("task 詳細")
        layout = QGridLayout(group)

        self.detail_task_id = QLineEdit()
        self.detail_title = QLineEdit()
        self.detail_description = QPlainTextEdit()
        self.detail_status = QLineEdit()
        self.detail_current_stage = QLineEdit()
        self.detail_next_role = QLineEdit()
        self.detail_cycle = QLineEdit()
        self.detail_last_completed_role = QLineEdit()
        self.detail_max_cycles = QLineEdit()
        self.detail_task_dir = QLineEdit()

        read_only_line_edits = [
            self.detail_task_id,
            self.detail_title,
            self.detail_status,
            self.detail_current_stage,
            self.detail_next_role,
            self.detail_cycle,
            self.detail_last_completed_role,
            self.detail_max_cycles,
            self.detail_task_dir,
        ]
        for widget in read_only_line_edits:
            widget.setReadOnly(True)

        self.detail_description.setReadOnly(True)
        self.detail_description.setFixedHeight(100)

        layout.addWidget(QLabel("task_id"), 0, 0)
        layout.addWidget(self.detail_task_id, 0, 1)
        layout.addWidget(QLabel("title"), 1, 0)
        layout.addWidget(self.detail_title, 1, 1)
        layout.addWidget(QLabel("description"), 2, 0)
        layout.addWidget(self.detail_description, 2, 1)
        layout.addWidget(QLabel("status"), 3, 0)
        layout.addWidget(self.detail_status, 3, 1)
        layout.addWidget(QLabel("current_stage"), 4, 0)
        layout.addWidget(self.detail_current_stage, 4, 1)
        layout.addWidget(QLabel("next_role"), 5, 0)
        layout.addWidget(self.detail_next_role, 5, 1)
        layout.addWidget(QLabel("cycle"), 6, 0)
        layout.addWidget(self.detail_cycle, 6, 1)
        layout.addWidget(QLabel("last_completed_role"), 7, 0)
        layout.addWidget(self.detail_last_completed_role, 7, 1)
        layout.addWidget(QLabel("max_cycles"), 8, 0)
        layout.addWidget(self.detail_max_cycles, 8, 1)
        layout.addWidget(QLabel("task_dir"), 9, 0)
        layout.addWidget(self.detail_task_dir, 9, 1)

        return group

    def _build_action_group(self) -> QGroupBox:
        group = QGroupBox("操作")
        layout = QVBoxLayout(group)

        status_row = QGridLayout()
        self.current_prompt_path_edit = QLineEdit()
        self.current_prompt_path_edit.setReadOnly(True)

        self.current_output_json_path_edit = QLineEdit()
        self.current_output_json_path_edit.setReadOnly(True)

        status_row.addWidget(QLabel("prompt path"), 0, 0)
        status_row.addWidget(self.current_prompt_path_edit, 0, 1)
        status_row.addWidget(QLabel("output json path"), 1, 0)
        status_row.addWidget(self.current_output_json_path_edit, 1, 1)

        button_row = QHBoxLayout()
        self.btn_show_next = QPushButton("show-next")
        self.btn_validate = QPushButton("validate-report")
        self.btn_advance = QPushButton("advance")
        self.btn_reload_selected = QPushButton("再読込")

        button_row.addWidget(self.btn_show_next)
        button_row.addWidget(self.btn_validate)
        button_row.addWidget(self.btn_advance)
        button_row.addWidget(self.btn_reload_selected)
        button_row.addStretch()

        layout.addLayout(status_row)
        layout.addLayout(button_row)

        return group

    def _build_prompt_group(self) -> QGroupBox:
        group = QGroupBox("prompt 表示")
        layout = QVBoxLayout(group)

        self.prompt_text_edit = QPlainTextEdit()
        self.prompt_text_edit.setReadOnly(True)

        layout.addWidget(self.prompt_text_edit)
        return group

    def _build_output_path_group(self) -> QGroupBox:
        group = QGroupBox("次に保存すべき JSON パス")
        layout = QVBoxLayout(group)

        self.output_path_detail_edit = QPlainTextEdit()
        self.output_path_detail_edit.setReadOnly(True)
        self.output_path_detail_edit.setFixedHeight(70)

        layout.addWidget(self.output_path_detail_edit)
        return group

    def _build_validation_group(self) -> QGroupBox:
        group = QGroupBox("validation 結果")
        layout = QVBoxLayout(group)

        self.validation_result_edit = QPlainTextEdit()
        self.validation_result_edit.setReadOnly(True)
        self.validation_result_edit.setFixedHeight(90)

        layout.addWidget(self.validation_result_edit)
        return group

    def _build_log_group(self) -> QGroupBox:
        group = QGroupBox("ログ")
        layout = QVBoxLayout(group)

        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)

        layout.addWidget(self.log_edit)
        return group

    def _connect_signals(self) -> None:
        self.btn_repo_browse.clicked.connect(self.on_browse_repo)
        self.btn_check_init.clicked.connect(self.on_check_initialized)
        self.btn_init_project.clicked.connect(self.on_init_project)
        self.btn_create_task.clicked.connect(self.on_create_task)
        self.btn_refresh_tasks.clicked.connect(self.on_refresh_tasks)
        self.task_list_widget.itemSelectionChanged.connect(self.on_task_selected)
        self.btn_show_next.clicked.connect(self.on_show_next)
        self.btn_validate.clicked.connect(self.on_validate_report)
        self.btn_advance.clicked.connect(self.on_advance_task)
        self.btn_reload_selected.clicked.connect(self.on_reload_selected_task)
        self.repo_path_edit.editingFinished.connect(self.on_repo_path_edited)

    def _apply_initial_state(self) -> None:
        self._reset_repo_context(clear_log=False)
        self._append_log("GUI ready.")

    def _get_repo_path(self) -> str:
        return self.repo_path_edit.text().strip()

    def _normalize_repo_path(self, repo_path: str) -> str:
        if not repo_path:
            return ""
        try:
            return str(Path(repo_path).resolve())
        except Exception:
            return repo_path.strip()

    def _require_repo_path(self) -> str:
        repo_path = self._get_repo_path()
        if not repo_path:
            raise ValueError("repo path is empty.")
        return repo_path

    def _require_selected_task_id(self) -> str:
        if not self._current_task_id:
            raise ValueError("task is not selected.")
        return self._current_task_id

    def _parse_multiline_list(self, text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _append_log(self, message: str) -> None:
        self.log_edit.appendPlainText(message)
        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_edit.setTextCursor(cursor)

    def _show_error(self, title: str, exc: Exception) -> None:
        message = f"{type(exc).__name__}: {exc}"
        self._append_log(f"[ERROR] {message}")
        QMessageBox.critical(self, title, message)

    def _show_info(self, title: str, message: str) -> None:
        self._append_log(f"[INFO] {message}")
        QMessageBox.information(self, title, message)

    def _clear_task_detail(self) -> None:
        self.detail_task_id.clear()
        self.detail_title.clear()
        self.detail_description.clear()
        self.detail_status.clear()
        self.detail_current_stage.clear()
        self.detail_next_role.clear()
        self.detail_cycle.clear()
        self.detail_last_completed_role.clear()
        self.detail_max_cycles.clear()
        self.detail_task_dir.clear()
        self._current_task_id = ""

    def _clear_prompt_area(self) -> None:
        self.current_prompt_path_edit.clear()
        self.current_output_json_path_edit.clear()
        self.prompt_text_edit.clear()
        self.output_path_detail_edit.clear()
        self._last_prompt_path = ""
        self._last_output_json_path = ""

    def _clear_validation_area(self) -> None:
        self.validation_result_edit.clear()

    def _clear_task_list(self) -> None:
        self.task_list_widget.clear()

    def _reset_repo_context(self, clear_log: bool = False) -> None:
        self._clear_task_list()
        self._clear_task_detail()
        self._clear_prompt_area()
        self._clear_validation_area()
        if clear_log:
            self.log_edit.clear()

    def _set_task_detail(self, data: dict[str, Any]) -> None:
        self.detail_task_id.setText(str(data.get("task_id", "")))
        self.detail_title.setText(str(data.get("title", "")))
        self.detail_description.setPlainText(str(data.get("description", "")))
        self.detail_status.setText(str(data.get("status", "")))
        self.detail_current_stage.setText(str(data.get("current_stage", "")))
        self.detail_next_role.setText(str(data.get("next_role", "")))
        self.detail_cycle.setText(str(data.get("cycle", "")))
        self.detail_last_completed_role.setText(str(data.get("last_completed_role", "")))
        self.detail_max_cycles.setText(str(data.get("max_cycles", "")))
        self.detail_task_dir.setText(str(data.get("task_dir", "")))
        self._current_task_id = str(data.get("task_id", ""))

    def _read_text_file_if_exists(self, path_str: str) -> str:
        path = Path(path_str)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _handle_repo_changed(self, repo_path: str) -> None:
        normalized = self._normalize_repo_path(repo_path)
        if normalized == self._last_repo_path:
            return

        old_repo = self._last_repo_path
        self._last_repo_path = normalized
        self._reset_repo_context(clear_log=False)

        if normalized:
            if old_repo:
                self._append_log(f"[INFO] repo changed: {old_repo} -> {normalized}")
            else:
                self._append_log(f"[INFO] repo selected: {normalized}")

    def _refresh_task_list(self) -> None:
        repo_path = self._require_repo_path()
        results = StatusUseCase().list_tasks(repo_path=repo_path)

        selected_task_id = self._current_task_id
        found_selected = False

        self.task_list_widget.clear()

        for item in results:
            text = (
                f"{item['task_id']} | "
                f"status={item['status']} | "
                f"current={item['current_stage']} | "
                f"next={item['next_role']} | "
                f"cycle={item['cycle']} | "
                f"title={item['title']}"
            )
            widget_item = QListWidgetItem(text)
            widget_item.setData(Qt.UserRole, item["task_id"])
            self.task_list_widget.addItem(widget_item)

        if selected_task_id:
            for i in range(self.task_list_widget.count()):
                item = self.task_list_widget.item(i)
                if str(item.data(Qt.UserRole)) == selected_task_id:
                    self.task_list_widget.setCurrentItem(item)
                    found_selected = True
                    break

        if selected_task_id and not found_selected:
            self._clear_task_detail()
            self._clear_prompt_area()
            self._clear_validation_area()

        if not results:
            self._clear_task_detail()
            self._clear_prompt_area()
            self._clear_validation_area()

        self._append_log(f"[INFO] task list refreshed. count={len(results)}")

    def _load_selected_task_detail(self, task_id: str) -> None:
        repo_path = self._require_repo_path()
        data = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
        self._set_task_detail(data)
        self._append_log(f"[INFO] task detail loaded: {task_id}")

    def on_browse_repo(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "対象 repo を選択")
        if not selected:
            return
        self.repo_path_edit.setText(selected)
        self._handle_repo_changed(selected)

    def on_repo_path_edited(self) -> None:
        self._handle_repo_changed(self._get_repo_path())

    def on_check_initialized(self) -> None:
        try:
            repo_path = self._require_repo_path()
            self._handle_repo_changed(repo_path)

            project_paths = ProjectPaths(target_repo=Path(repo_path))
            project_paths.ensure_initialized()

            self._append_log(f"[INFO] initialized repo confirmed: {project_paths.root}")
            self._refresh_task_list()
        except Exception as exc:
            self._show_error("初期化確認エラー", exc)

    def on_init_project(self) -> None:
        try:
            repo_path = self._require_repo_path()
            self._handle_repo_changed(repo_path)

            result = InitProjectUseCase().execute(repo_path=repo_path, force=False)
            self._append_log(f"[INFO] init-project completed: {result}")
            self._show_info("初期化完了", f"Initialized:\n{result}")
            self._refresh_task_list()
        except Exception as exc:
            self._show_error("init-project エラー", exc)

    def on_create_task(self) -> None:
        try:
            repo_path = self._require_repo_path()
            self._handle_repo_changed(repo_path)

            title = self.task_title_edit.text().strip()
            description = self.task_desc_edit.toPlainText().strip()

            if not title:
                raise ValueError("title is required.")
            if not description:
                raise ValueError("description is required.")

            context_files = self._parse_multiline_list(self.context_files_edit.toPlainText())
            constraints = self._parse_multiline_list(self.constraints_edit.toPlainText())

            task_dir = CreateTaskUseCase().execute(
                repo_path=repo_path,
                title=title,
                description=description,
                context_files=context_files,
                constraints=constraints,
            )

            created_task_id = Path(task_dir).name

            self._append_log(f"[INFO] task created: {task_dir}")

            self.task_title_edit.clear()
            self.task_desc_edit.clear()
            self.context_files_edit.clear()
            self.constraints_edit.clear()

            self._current_task_id = created_task_id
            self._refresh_task_list()
            self._load_selected_task_detail(created_task_id)

        except Exception as exc:
            self._show_error("task作成エラー", exc)

    def on_refresh_tasks(self) -> None:
        try:
            repo_path = self._require_repo_path()
            self._handle_repo_changed(repo_path)
            self._refresh_task_list()
        except Exception as exc:
            self._show_error("task一覧更新エラー", exc)

    def on_task_selected(self) -> None:
        items = self.task_list_widget.selectedItems()
        if not items:
            return

        try:
            task_id = str(items[0].data(Qt.UserRole))
            self._load_selected_task_detail(task_id)
        except Exception as exc:
            self._show_error("task詳細読込エラー", exc)

    def on_show_next(self) -> None:
        try:
            repo_path = self._require_repo_path()
            self._handle_repo_changed(repo_path)
            task_id = self._require_selected_task_id()

            result = ShowNextUseCase().execute(repo_path=repo_path, task_id=task_id)

            prompt_path = str(result["prompt_path"])
            output_json_path = str(result["output_json_path"])
            prompt_text = self._read_text_file_if_exists(prompt_path)

            self._last_prompt_path = prompt_path
            self._last_output_json_path = output_json_path

            self.current_prompt_path_edit.setText(prompt_path)
            self.current_output_json_path_edit.setText(output_json_path)
            self.prompt_text_edit.setPlainText(prompt_text)
            self.output_path_detail_edit.setPlainText(output_json_path)

            self._clear_validation_area()

            self._append_log(
                "[INFO] show-next completed: "
                f"task_id={task_id}, role={result['role']}, cycle={result['cycle']}"
            )
        except Exception as exc:
            self._show_error("show-next エラー", exc)

    def on_validate_report(self) -> None:
        try:
            repo_path = self._require_repo_path()
            self._handle_repo_changed(repo_path)
            task_id = self._require_selected_task_id()
            role = self.detail_next_role.text().strip()

            if not role or role == "none":
                raise ValueError("next_role is empty or none.")

            result = ValidateReportUseCase().execute(
                repo_path=repo_path,
                task_id=task_id,
                role=role,
            )

            text = (
                f"valid: {result['valid']}\n"
                f"role: {result['role']}\n"
                f"cycle: {result['cycle']}\n"
                f"report_path: {result['report_path']}"
            )
            self.validation_result_edit.setPlainText(text)

            self._append_log(
                "[INFO] validate-report success: "
                f"task_id={task_id}, role={result['role']}, cycle={result['cycle']}"
            )
        except Exception as exc:
            self.validation_result_edit.setPlainText(f"ERROR\n{type(exc).__name__}: {exc}")
            self._show_error("validate-report エラー", exc)

    def on_advance_task(self) -> None:
        try:
            repo_path = self._require_repo_path()
            self._handle_repo_changed(repo_path)
            task_id = self._require_selected_task_id()

            result = AdvanceTaskUseCase().execute(repo_path=repo_path, task_id=task_id)

            self._append_log(
                "[INFO] advance completed: "
                f"task_id={task_id}, "
                f"status={result['status']}, "
                f"current={result['current_stage']}, "
                f"next={result['next_role']}, "
                f"cycle={result['cycle']}"
            )

            self._load_selected_task_detail(task_id)
            self._refresh_task_list()

        except Exception as exc:
            self._show_error("advance エラー", exc)

    def on_reload_selected_task(self) -> None:
        try:
            repo_path = self._require_repo_path()
            self._handle_repo_changed(repo_path)
            task_id = self._require_selected_task_id()

            self._load_selected_task_detail(task_id)

            if self._last_prompt_path:
                prompt_text = self._read_text_file_if_exists(self._last_prompt_path)
                self.prompt_text_edit.setPlainText(prompt_text)
                self.current_prompt_path_edit.setText(self._last_prompt_path)

            if self._last_output_json_path:
                self.current_output_json_path_edit.setText(self._last_output_json_path)
                self.output_path_detail_edit.setPlainText(self._last_output_json_path)

            self._append_log(f"[INFO] selected task reloaded: {task_id}")
        except Exception as exc:
            self._show_error("再読込エラー", exc)