"""Core services: app state, tool scanning and independent process running."""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.core.state import LOGS_DIR


@dataclass
class RunningTool:
    """Bookkeeping for one launched tool process."""
    process: subprocess.Popen
    tool_id: str
    name: str
    started_at: datetime
    log_file: object
    log_path: Path


class ToolRunner(QObject):
    """Launches tools as fully independent subprocesses and tracks their state.

    Design notes:
    - Tools are spawned with ``CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS`` so
      they never share a console with the toolbox and keep running even if the
      toolbox is closed. A tool that crashes cannot take the toolbox down.
    - A QTimer polls every process every 2 seconds and emits ``processesChanged``
      so the UI can refresh its status indicators without blocking.
    - stdout/stderr of every tool is captured into ``logs/<tool_id>-<timestamp>.log``.
    """

    processesChanged = pyqtSignal()

    POLL_INTERVAL_MS = 2000

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._running: dict[str, RunningTool] = {}

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(self.POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start()

    # ── Launching ────────────────────────────────────────────────────────────────
    def launch(self, tool) -> tuple[bool, str]:
        """Spawn ``tool`` as an independent process. Returns (ok, message)."""
        # Stale entry from a process that exited but was not polled yet.
        stale = self._running.get(tool.id)
        if stale is not None:
            if stale.process.poll() is None:
                return False, "Tool is already running."
            self._cleanup(stale)

        entry = tool.entry_path
        if not entry.exists():
            return False, f"Entry file not found: {entry}"

        log_path = self._new_log_path(tool.id)
        try:
            log_file = open(log_path, "wb")
        except OSError as exc:
            return False, f"Cannot open log file ({log_path.name}): {exc}"

        # On unix just detach; DETACHED_PROCESS exists only on Windows.
        creationflags = 0
        if os.name == "nt":
            creationflags = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
        try:
            process = subprocess.Popen(
                [sys.executable, str(entry)],
                cwd=str(tool.directory),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        except OSError as exc:
            log_file.close()
            return False, str(exc)

        self._running[tool.id] = RunningTool(
            process=process,
            tool_id=tool.id,
            name=tool.name,
            started_at=datetime.now(),
            log_file=log_file,
            log_path=log_path,
        )
        self.processesChanged.emit()
        return True, f"Started with PID {process.pid}. Log: {log_path.name}"

    # ── Queries ──────────────────────────────────────────────────────────────────
    def is_running(self, tool_id: str) -> bool:
        info = self._running.get(tool_id)
        return info is not None and info.process.poll() is None

    def pid_of(self, tool_id: str) -> int | None:
        info = self._running.get(tool_id)
        return None if info is None else info.process.pid

    def started_at_of(self, tool_id: str) -> datetime | None:
        info = self._running.get(tool_id)
        return None if info is None else info.started_at

    def log_path_of(self, tool_id: str) -> Path | None:
        info = self._running.get(tool_id)
        return None if info is None else info.log_path

    def running_count(self) -> int:
        return sum(1 for tool_id in self._running if self.is_running(tool_id))

    # ── Actions ──────────────────────────────────────────────────────────────────
    def terminate(self, tool_id: str) -> bool:
        """Force-stop a running tool. On Windows terminate() == TerminateProcess."""
        info = self._running.get(tool_id)
        if info is None or info.process.poll() is not None:
            return False
        try:
            info.process.terminate()
        except OSError:
            return False
        self._poll()  # refresh bookkeeping immediately
        return True

    # ── Internals ────────────────────────────────────────────────────────────────
    def _poll(self) -> None:
        changed = False
        for info in list(self._running.values()):
            if info.process.poll() is not None:
                self._cleanup(info)
                changed = True
        if changed:
            self.processesChanged.emit()

    def _cleanup(self, info: RunningTool) -> None:
        self._running.pop(info.tool_id, None)
        try:
            info.log_file.close()
        except OSError:
            pass

    @staticmethod
    def _new_log_path(tool_id: str) -> Path:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return LOGS_DIR / f"{tool_id}-{stamp}.log"

    def latest_log_path(self, tool_id: str) -> Path | None:
        """Newest log for a tool (running log first, then the most recent one)."""
        path = self.log_path_of(tool_id)
        if path is not None and path.exists():
            return path
        if not LOGS_DIR.exists():
            return None
        candidates = sorted(LOGS_DIR.glob(f"{tool_id}-*.log"))
        return candidates[-1] if candidates else None


def _unused_sys_guard():  # pragma: no cover
    """Keeps ``import os/subprocess/sys`` lint-stable when flags are platform-gated."""
    return os, subprocess, sys
