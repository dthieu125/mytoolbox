"""Shared right-click menu for a tool, used by both grid cards and the list view."""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication, QMenu

from src.core.runner import latest_log_file
from src.core.scanner import ToolInfo


def build_tool_menu(window, tool: ToolInfo) -> QMenu:
    """Build the management menu for ``tool``.

    ``window`` is the MainWindow; the menu delegates actions to its handlers so
    grid and list views share one implementation.
    """
    runner = window.runner
    config = window.config
    running = runner.is_running(tool.id)

    menu = QMenu(window)

    launch = menu.addAction("Bring to front" if running else "Launch")
    launch.triggered.connect(lambda: window._activate(tool))

    if running:
        restart = menu.addAction("Restart")
        restart.triggered.connect(lambda: window._restart(tool))
        terminate = menu.addAction("Terminate process")
        terminate.triggered.connect(lambda: window._terminate(tool))

    menu.addSeparator()

    pin = menu.addAction(
        "Unpin from top" if config.is_favorite(tool.id) else "Pin to top"
    )
    pin.triggered.connect(lambda: window._toggle_favorite(tool))

    hide = menu.addAction(
        "Unhide tool" if config.is_hidden(tool.id) else "Hide from toolbox"
    )
    hide.triggered.connect(lambda: window._toggle_hidden(tool))

    menu.addSeparator()

    open_folder = menu.addAction("Open folder")
    open_folder.triggered.connect(lambda: window._open_path(tool.directory))

    manifest = tool.directory / "tool.toml"
    edit_manifest = menu.addAction("Edit tool.toml")
    edit_manifest.triggered.connect(lambda: window._open_path(manifest))

    log_path = runner.latest_log_path(tool.id) or latest_log_file(tool.id)
    open_log = menu.addAction("Open log file")
    open_log.setEnabled(log_path is not None)
    if log_path is not None:
        open_log.triggered.connect(lambda: window._open_path(log_path))

    copy_path = menu.addAction("Copy folder path")
    copy_path.triggered.connect(
        lambda: QApplication.clipboard().setText(str(tool.directory))
    )

    requirements = tool.directory / "requirements.txt"
    if requirements.exists():
        menu.addSeparator()
        install = menu.addAction("Install requirements…")
        install.triggered.connect(lambda: window._install_deps(tool))

    # Usage stats are handy for auditing tools.
    count = config.launch_count(tool.id)
    if count:
        stats = menu.addAction(f"Launched {count}×  ·  PID {runner.pid_of(tool.id)}" if running else f"Launched {count}×")
        stats.setEnabled(False)

    return menu
