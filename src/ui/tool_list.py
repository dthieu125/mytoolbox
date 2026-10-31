"""Compact list view of tools (alternative to the card grid)."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from src.core.scanner import ToolInfo
from src.ui.icons import tool_icon

STATUS_ROLE = Qt.ItemDataRole.UserRole


class ToolListWidget(QTreeWidget):
    """Table-like list with the same interactions as the card grid."""

    activated = pyqtSignal(object)
    contextRequested = pyqtSignal(object, object)

    COLUMNS = ["Name", "Category", "Version", "Status", "Description"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(self.COLUMNS)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setAllColumnsShowFocus(True)
        self.setUniformRowHeights(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setIconSize(QSize(20, 20))

        self._tools_by_id: dict[str, ToolInfo] = {}
        self._items_by_id: dict[str, QTreeWidgetItem] = {}

        self.setColumnWidth(0, 220)
        self.setColumnWidth(1, 120)
        self.setColumnWidth(2, 70)
        self.setColumnWidth(3, 170)
        header = self.header()
        header.setStretchLastSection(True)

        self.itemDoubleClicked.connect(self._on_double_clicked)
        self.customContextMenuRequested.connect(self._on_context_menu)

    # ── Population ───────────────────────────────────────────────────────────────
    def populate(self, tools: list[ToolInfo], config) -> None:
        self.clear()
        self._tools_by_id = {tool.id: tool for tool in tools}
        self._items_by_id = {}

        for tool in tools:
            name = f"★ {tool.name}" if config.is_favorite(tool.id) else tool.name
            if config.is_hidden(tool.id):
                name += "  (hidden)"
            item = QTreeWidgetItem([name, tool.category or "General", tool.version or "–", "○ Idle", tool.description])
            item.setIcon(0, tool_icon(tool, 32))
            item.setData(0, STATUS_ROLE, tool.id)
            item.setToolTip(0, f"{tool.name}\n{tool.directory}")
            item.setToolTip(4, tool.description)
            self.addTopLevelItem(item)
            self._items_by_id[tool.id] = item

    def refresh_status(self, runner) -> None:
        for tool_id, item in self._items_by_id.items():
            running = runner.is_running(tool_id)
            if running:
                pid = runner.pid_of(tool_id)
                started = runner.started_at_of(tool_id)
                clock = f" · {started:%H:%M}" if started else ""
                item.setText(3, f"● Running · {pid}{clock}")
            else:
                item.setText(3, "○ Idle")

    # ── Slots ────────────────────────────────────────────────────────────────────
    def _on_double_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        tool = self._tool_for_item(item)
        if tool is not None:
            self.activated.emit(tool)

    def _on_context_menu(self, pos) -> None:
        item = self.itemAt(pos)
        tool = self._tool_for_item(item) if item is not None else None
        if tool is not None:
            self.contextRequested.emit(tool, self.viewport().mapToGlobal(pos))

    def _tool_for_item(self, item: QTreeWidgetItem | None) -> ToolInfo | None:
        if item is None:
            return None
        tool_id = item.data(0, STATUS_ROLE)
        return self._tools_by_id.get(tool_id)
