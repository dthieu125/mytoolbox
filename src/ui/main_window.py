"""Main window: toolbar, grid/list views, themes, tray integration and tool management."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QDesktopServices, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QScrollArea,
    QStackedWidget,
    QSystemTrayIcon,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core.config import Config
from src.core.runner import ToolRunner
from src.core.scanner import ToolInfo, scan_tools
from src.core.state import APP_NAME, APP_VERSION, LOGS_DIR, TOOLS_DIR
from src.core.windowing import focus_window_for_pid
from src.ui.deps_dialog import DepsDialog
from src.ui.icons import build_app_icon, tray_icon
from src.ui.style import get_stylesheet, other_theme
from src.ui.tool_card import ToolCard
from src.ui.tool_list import ToolListWidget
from src.ui.tool_menu import build_tool_menu

SORT_OPTIONS = [
    ("Name (A→Z)", "name"),
    ("Recently launched", "recent"),
    ("Most launched", "most"),
]

VIEW_GRID = "grid"
VIEW_LIST = "list"


class _GridHost(QWidget):
    """Container of the card grid; reports its resized width for reflow."""

    widthChanged = pyqtSignal(int)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        super().resizeEvent(event)
        self.widthChanged.emit(event.size().width())


class MainWindow(QMainWindow):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle(f"{APP_NAME} — {APP_VERSION}")
        self.setWindowIcon(build_app_icon())
        self.setMinimumSize(560, 420)

        self.runner = ToolRunner(self)
        self.runner.processesChanged.connect(self._on_processes_changed)

        self._all_tools: list[ToolInfo] = []
        self._visible_tools: list[ToolInfo] = []
        self._cards: dict[str, ToolCard] = {}
        self._scan_warnings: list[str] = []
        self._last_cols = 0
        self._quitting = False
        self._tray_hinted = False

        self._build_ui()
        self._build_tray()
        self._install_shortcuts()
        self._restore_geometry()
        self._apply_view_mode_button()
        self.refresh()

    # ── UI construction ──────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 14, 16, 8)
        root.setSpacing(10)

        # Header row
        header = QHBoxLayout()
        title = QLabel(f"🧰 {APP_NAME}")
        title.setObjectName("Title")
        subtitle = QLabel(str(TOOLS_DIR))
        subtitle.setObjectName("Subtitle")
        self.view_btn = QToolButton()
        self.view_btn.clicked.connect(self._toggle_view)
        self.theme_btn = QToolButton()
        self.theme_btn.setText("◐")
        self.theme_btn.setToolTip("Toggle light/dark theme (Ctrl+T)")
        self.theme_btn.clicked.connect(self._toggle_theme)
        refresh_btn = QToolButton()
        refresh_btn.setText("⟳")
        refresh_btn.setToolTip("Rescan tools/ (Ctrl+R)")
        refresh_btn.clicked.connect(self.refresh)
        more_btn = QToolButton()
        more_btn.setText("⋯")
        more_btn.setToolTip("More actions")
        more_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        more_btn.setMenu(self._build_more_menu())

        header.addWidget(title)
        header.addWidget(subtitle, 1)
        header.addWidget(self.view_btn)
        header.addWidget(self.theme_btn)
        header.addWidget(refresh_btn)
        header.addWidget(more_btn)
        root.addLayout(header)

        # Filter row
        filters = QHBoxLayout()
        filters.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search tools…  (Ctrl+F)")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(180)
        self.search.textChanged.connect(self._on_search_changed)

        self.category_box = QComboBox()
        self.category_box.setMinimumWidth(150)
        self.category_box.currentIndexChanged.connect(self._on_category_changed)

        self.sort_box = QComboBox()
        for label, key in SORT_OPTIONS:
            self.sort_box.addItem(label, key)
        self.sort_box.setMinimumWidth(150)
        self._select_sort(self.config.sort_mode)
        self.sort_box.currentIndexChanged.connect(self._on_sort_changed)

        filters.addWidget(self.search, 1)
        filters.addWidget(self.category_box)
        filters.addWidget(self.sort_box)
        root.addLayout(filters)

        # Scan warnings
        self._warn_label = QLabel()
        self._warn_label.setObjectName("Warning")
        self._warn_label.setWordWrap(True)
        self._warn_label.setHidden(True)
        root.addWidget(self._warn_label)

        # Views
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        # Grid page
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._grid_host = _GridHost()
        self._grid_host.widthChanged.connect(self._reflow)
        self._scroll.setWidget(self._grid_host)
        self.stack.addWidget(self._scroll)

        # List page
        self.tool_list = ToolListWidget()
        self.tool_list.activated.connect(self._activate)
        self.tool_list.contextRequested.connect(self._show_tool_menu)
        self.stack.addWidget(self.tool_list)

        self._apply_view_page()

    def _build_more_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setToolTipsVisible(True)

        self.show_hidden_action = menu.addAction("Show hidden tools")
        self.show_hidden_action.setCheckable(True)
        self.show_hidden_action.setChecked(self.config.show_hidden)
        self.show_hidden_action.toggled.connect(self._set_show_hidden)

        menu.addSeparator()
        open_logs = menu.addAction("Open logs folder")
        open_logs.triggered.connect(self._open_logs_folder)
        about = menu.addAction(f"About {APP_NAME}")
        about.triggered.connect(self._show_about)

        menu.addSeparator()
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self._quit)
        return menu

    def _build_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(tray_icon(0), self)
        self._tray_menu = QMenu()
        self.tray.setContextMenu(self._tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()
        self._refresh_tray()

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._focus_search)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh)
        QShortcut(QKeySequence("Ctrl+G"), self, activated=self._toggle_view)
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self._toggle_theme)
        QShortcut(QKeySequence("Escape"), self, activated=self._clear_search)

    # ── Data loading / filtering ─────────────────────────────────────────────────
    def refresh(self) -> None:
        self._all_tools, self._scan_warnings = scan_tools(TOOLS_DIR)
        self._rebuild_category_combo()
        self._reload_view()

    def _rebuild_category_combo(self) -> None:
        categories = sorted(
            {tool.category for tool in self._all_tools if tool.category},
            key=str.casefold,
        )
        current = self.config.category
        self.category_box.blockSignals(True)
        self.category_box.clear()
        self.category_box.addItem("All categories", "")
        for category in categories:
            self.category_box.addItem(category, category)
        index = self.category_box.findData(current)
        self.category_box.setCurrentIndex(max(0, index))
        self.category_box.blockSignals(False)
        if index < 0:
            self.config.category = ""

    def _reload_view(self) -> None:
        self._visible_tools = self._compute_visible()
        self._populate_grid()
        self.tool_list.populate(self._visible_tools, self.config)
        self._apply_view_page()
        self.refresh_statuses()
        self._update_status()

    def _compute_visible(self) -> list[ToolInfo]:
        query = self.search.text().strip().lower()
        category = self.config.category
        tools: list[ToolInfo] = []
        for tool in self._all_tools:
            if not self.config.show_hidden and self.config.is_hidden(tool.id):
                continue
            if category and (tool.category or "") != category:
                continue
            if query:
                haystack = f"{tool.name} {tool.id} {tool.category} {tool.description}".lower()
                if query not in haystack:
                    continue
            tools.append(tool)

        mode = self.config.sort_mode

        def sort_key(tool: ToolInfo):
            favourite_rank = 0 if self.config.is_favorite(tool.id) else 1
            if mode == "recent":
                primary = -self.config.last_launched(tool.id)
            elif mode == "most":
                primary = -self.config.launch_count(tool.id)
            else:
                primary = tool.name.casefold()
            return (favourite_rank, primary, tool.name.casefold())

        return sorted(tools, key=sort_key)

    # ── View management ──────────────────────────────────────────────────────────
    def _populate_grid(self) -> None:
        for card in list(self._cards.values()):
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        # Remove any leftover direct children (e.g. the previous empty-state label).
        for child in self._grid_host.findChildren(
            QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly
        ):
            child.setParent(None)
            child.deleteLater()

        old = self._grid_host.layout()
        if old is not None:
            QWidget().setLayout(old)  # detach the layout so a fresh one can be set
        layout = QGridLayout(self._grid_host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        if not self._visible_tools:
            empty = QLabel(self._empty_message())
            empty.setObjectName("EmptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            layout.addWidget(empty, 0, 0)
            self._last_cols = 0
            return

        self._last_cols = 0  # force a reflow with the current width
        for col, tool in enumerate(self._visible_tools):
            card = ToolCard(
                tool,
                favorite=self.config.is_favorite(tool.id),
                hidden=self.config.is_hidden(tool.id),
                launch_count=self.config.launch_count(tool.id),
            )
            card.activated.connect(self._activate)
            card.contextRequested.connect(self._show_tool_menu)
            layout.addWidget(card, 0, col, Qt.AlignmentFlag.AlignTop)
            self._cards[tool.id] = card
        self._reflow(self._scroll.viewport().width())

    def _reflow(self, width: int) -> None:
        """Re-position cards to fit as many per row as the width allows."""
        if not self._cards:
            return
        layout = self._grid_host.layout()
        if layout is None:
            return
        cols = max(1, int(width // (ToolCard.CARD_WIDTH + layout.spacing())))
        if cols == self._last_cols:
            return
        self._last_cols = cols
        for index, tool in enumerate(self._visible_tools):
            card = self._cards.get(tool.id)
            if card is not None:
                card.setParent(self._grid_host)  # re-adding moves the widget
                layout.addWidget(card, index // cols, index % cols, Qt.AlignmentFlag.AlignTop)

    def _apply_view_page(self) -> None:
        self.stack.setCurrentIndex(0 if self.config.view_mode == VIEW_GRID else 1)

    def _apply_view_mode_button(self) -> None:
        self.view_btn.setText("☰ List" if self.config.view_mode == VIEW_GRID else "▦ Grid")
        self.view_btn.setToolTip(
            "Switch to list view (Ctrl+G)"
            if self.config.view_mode == VIEW_GRID
            else "Switch to grid view (Ctrl+G)"
        )

    def _toggle_view(self) -> None:
        self.config.view_mode = VIEW_LIST if self.config.view_mode == VIEW_GRID else VIEW_GRID
        self._apply_view_page()
        self._apply_view_mode_button()

    def _empty_message(self) -> str:
        if self._all_tools and not self._visible_tools:
            return "No tools match the current search/filter."
        return "No tools yet.\n\nAdd a folder containing a tool.toml into tools/ and press Refresh."

    # ── Tool actions (called by cards, list and context menu) ────────────────────
    def _activate(self, tool: ToolInfo) -> None:
        if self.runner.is_running(tool.id):
            pid = self.runner.pid_of(tool.id)
            if pid is not None and focus_window_for_pid(pid):
                self.statusBar().showMessage(f"Brought {tool.name} to front (PID {pid})")
            else:
                self.statusBar().showMessage(f"{tool.name} is already running (PID {pid}).")
            return

        ok, message = self.runner.launch(tool)
        if ok:
            self.config.record_launch(tool.id)
            self.statusBar().showMessage(f"{tool.name}: {message}")
            self._reload_view()  # launch stats may change sort order
        else:
            QMessageBox.warning(self, tool.name, f"Failed to launch {tool.name}:\n\n{message}")
            self.refresh_statuses()

    def _restart(self, tool: ToolInfo) -> None:
        if not self.runner.is_running(tool.id):
            self._activate(tool)
            return
        self.runner.terminate(tool.id)
        QTimer.singleShot(900, lambda: self._launch_again(tool))

    def _launch_again(self, tool: ToolInfo) -> None:
        ok, message = self.runner.launch(tool)
        if ok:
            self.config.record_launch(tool.id)
            self.statusBar().showMessage(f"Restarted {tool.name}: {message}")
        else:
            self.statusBar().showMessage(f"Restart failed: {message}")
        self._reload_view()

    def _terminate(self, tool: ToolInfo) -> None:
        self.runner.terminate(tool.id)
        self.refresh_statuses()
        self.statusBar().showMessage(f"Terminated {tool.name}.")

    def _toggle_favorite(self, tool: ToolInfo) -> None:
        pinned = self.config.toggle_favorite(tool.id)
        self._reload_view()
        self.statusBar().showMessage(
            f"{'Pinned' if pinned else 'Unpinned'} {tool.name}."
        )

    def _toggle_hidden(self, tool: ToolInfo) -> None:
        hidden = not self.config.is_hidden(tool.id)
        self.config.set_hidden(tool.id, hidden)
        self._reload_view()
        self.statusBar().showMessage(
            f"{tool.name} is now {'hidden' if hidden else 'visible'}."
        )

    def _open_path(self, path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_logs_folder(self) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self._open_path(LOGS_DIR)

    def _install_deps(self, tool: ToolInfo) -> None:
        DepsDialog(tool, self).exec()

    def _show_tool_menu(self, tool: ToolInfo, global_pos) -> None:
        menu = build_tool_menu(self, tool)
        menu.exec(global_pos)

    # ── Status / filters ─────────────────────────────────────────────────────────
    def refresh_statuses(self) -> None:
        for card in self._cards.values():
            card.refresh_status(self.runner)
        self.tool_list.refresh_status(self.runner)
        self._update_status()

    def _on_processes_changed(self) -> None:
        self.refresh_statuses()

    def _on_search_changed(self, _text: str) -> None:
        self._reload_view()

    def _on_category_changed(self, _index: int) -> None:
        self.config.category = self.category_box.currentData() or ""
        self._reload_view()

    def _on_sort_changed(self, _index: int) -> None:
        self.config.sort_mode = self.sort_box.currentData() or "name"
        self._reload_view()

    def _select_sort(self, mode: str) -> None:
        index = self.sort_box.findData(mode)
        if index >= 0:
            self.sort_box.setCurrentIndex(index)

    def _set_show_hidden(self, checked: bool) -> None:
        self.config.show_hidden = checked
        self._reload_view()

    def _focus_search(self) -> None:
        self.search.setFocus()
        self.search.selectAll()

    def _clear_search(self) -> None:
        if self.search.text():
            self.search.clear()

    def _toggle_theme(self) -> None:
        self.config.theme = other_theme(self.config.theme)
        QApplication.instance().setStyleSheet(get_stylesheet(self.config.theme))
        self.statusBar().showMessage(f"{self.config.theme.title()} theme enabled.")

    def _update_status(self) -> None:
        running = self.runner.running_count()
        message = (
            f"{len(self._visible_tools)}/{len(self._all_tools)} tool(s) · {running} running"
        )
        if self._scan_warnings:
            message += f" · {len(self._scan_warnings)} warning(s)"
        self.statusBar().showMessage(message)

        if self._scan_warnings:
            self._warn_label.setText(
                "⚠ Scan warnings:\n" + "\n".join(f"• {w}" for w in self._scan_warnings)
            )
            self._warn_label.setHidden(False)
        else:
            self._warn_label.setHidden(True)

        self._refresh_tray()

    # ── Tray ─────────────────────────────────────────────────────────────────────
    def _refresh_tray(self) -> None:
        if not hasattr(self, "tray"):
            return
        running_ids = self.runner.running_ids()
        self.tray.setIcon(tray_icon(len(running_ids)))
        self.tray.setToolTip(
            f"{APP_NAME} — {len(running_ids)} running" if running_ids else APP_NAME
        )

        menu = self._tray_menu
        menu.clear()
        menu.addAction("Show MyToolbox", self._show_window)
        menu.addAction("Refresh tools", self.refresh)

        if running_ids:
            menu.addSeparator()
            for tool_id in running_ids:
                name = self._tool_name(tool_id)
                action = menu.addAction(f"↗  {name}")
                action.triggered.connect(
                    lambda _checked=False, tid=tool_id: self._focus_running(tid)
                )
            menu.addAction("Stop all tools", self._stop_all)

        menu.addSeparator()
        menu.addAction("Exit", self._quit)

    def _tool_name(self, tool_id: str) -> str:
        for tool in self._all_tools:
            if tool.id == tool_id:
                return tool.name
        return tool_id

    def _focus_running(self, tool_id: str) -> None:
        pid = self.runner.pid_of(tool_id)
        if pid is not None:
            focus_window_for_pid(pid)
            self.statusBar().showMessage(f"Focused PID {pid}.")

    def _stop_all(self) -> None:
        stopped = self.runner.terminate_all()
        self.refresh_statuses()
        self.statusBar().showMessage(f"Stopped {stopped} tool(s).")

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ── About / geometry / lifecycle ─────────────────────────────────────────────
    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> {APP_VERSION}<br><br>"
            f"A launcher hub for {len(self._all_tools)} local tool(s).<br>"
            f"Tools folder: <code>{TOOLS_DIR}</code><br><br>"
            "Each tool runs as an independent process.<br>"
            "Config: <code>config.json</code> next to the app.",
        )

    def _restore_geometry(self) -> None:
        state = self.config.window_state()
        try:
            width = int(state.get("width", 0))
            height = int(state.get("height", 0))
            if width >= self.minimumWidth() and height >= self.minimumHeight():
                self.resize(width, height)
                self.move(int(state.get("x", 100)), int(state.get("y", 100)))
            else:
                self.resize(980, 680)
            if state.get("maximized"):
                self.showMaximized()
        except (TypeError, ValueError):
            self.resize(980, 680)

    def _store_geometry(self) -> None:
        self.config.store_window_state(
            {
                "x": self.x(),
                "y": self.y(),
                "width": self.width(),
                "height": self.height(),
                "maximized": self.isMaximized(),
            }
        )

    def _quit(self) -> None:
        self._quitting = True
        self._store_geometry()
        QApplication.instance().quit()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt naming)
        self._store_geometry()
        if self._quitting:
            event.accept()
            return
        # Closing the window hides to tray; tools keep running independently.
        event.ignore()
        self.hide()
        if not self._tray_hinted:
            self._tray_hinted = True
            if hasattr(self, "tray"):
                self.tray.showMessage(
                    APP_NAME,
                    "MyToolbox is still running in the tray.\nUse the tray menu → Exit to quit.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2500,
                )
