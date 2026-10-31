"""Dialog that runs ``pip install -r requirements.txt`` for a tool, with live log."""
from __future__ import annotations

import sys

from PyQt6.QtCore import QProcess
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)


class DepsDialog(QDialog):
    """Install a tool's requirements in the background and stream pip output."""

    def __init__(self, tool, parent=None) -> None:
        super().__init__(parent)
        self.tool = tool

        self.setWindowTitle(f"Install requirements — {tool.name}")
        self.resize(680, 460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(8)

        hint = QLabel(f"python -m pip install -r requirements.txt\nin {tool.directory}")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log, 1)

        row = QHBoxLayout()
        self.status = QLabel("Starting pip…")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        row.addWidget(self.status, 1)
        row.addWidget(self.stop_btn)
        row.addWidget(self.close_btn)
        layout.addLayout(row)

        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(tool.directory))
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.process.start(
            sys.executable,
            ["-m", "pip", "install", "-r", "requirements.txt"],
        )

    # ── Slots ────────────────────────────────────────────────────────────────────
    def _read_output(self) -> None:
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.log.moveCursor(QTextCursor.MoveOperation.End)
            self.log.insertPlainText(data)

    def _finished(self, exit_code: int, _status) -> None:
        if exit_code == 0:
            self.status.setText("✔ Requirements installed successfully.")
        else:
            self.status.setText(f"✖ pip failed (exit code {exit_code}). See log above.")
        self.stop_btn.setEnabled(False)

    def _error(self, _error) -> None:
        self.status.setText("✖ Could not run pip. See log above.")
        self.stop_btn.setEnabled(False)

    def _stop(self) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
        self.status.setText("Stopped by user.")
        self.stop_btn.setEnabled(False)
