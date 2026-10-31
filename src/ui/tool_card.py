"""Grid card representing a single tool. Double-click activates it."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from src.core.scanner import ToolInfo
from src.ui.icons import category_chip_style, tool_icon_pixmap


class ToolCard(QFrame):
    """A card in the toolbox grid.

    Emits:
      activated(ToolInfo)               — double-clicked (launch or bring to front)
      contextRequested(ToolInfo, QPoint) — right-clicked
    """

    activated = pyqtSignal(object)
    contextRequested = pyqtSignal(object, object)

    CARD_WIDTH = 200
    CARD_HEIGHT = 228

    def __init__(
        self,
        tool: ToolInfo,
        favorite: bool = False,
        hidden: bool = False,
        launch_count: int = 0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.tool = tool
        self._launch_count = launch_count

        self.setObjectName("ToolCard")
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(self._tooltip())
        self.setProperty("hidden", bool(hidden))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(6)

        # Category chip + favourite star
        top = QHBoxLayout()
        top.setSpacing(4)
        chip = QLabel(tool.category or "General")
        chip.setStyleSheet(category_chip_style(tool.category))
        top.addWidget(chip)
        top.addStretch()
        star = QLabel("★")
        star.setObjectName("Star")
        star.setToolTip("Pinned to top")
        star.setVisible(favorite)
        top.addWidget(star)
        layout.addLayout(top)

        # Icon
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(self._icon_pixmap(56))
        layout.addWidget(icon_label)

        # Name
        name_label = QLabel(tool.name)
        name_label.setObjectName("CardTitle")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setText(
            name_label.fontMetrics().elidedText(
                tool.name, Qt.TextElideMode.ElideRight, self.CARD_WIDTH - 30
            )
        )
        layout.addWidget(name_label)

        # Version + status
        meta = QHBoxLayout()
        version = QLabel(f"v{tool.version}" if tool.version else "–")
        version.setObjectName("CardVersion")
        self._status_label = QLabel("○ Idle")
        self._status_label.setObjectName("CardStatus")
        meta.addWidget(version)
        meta.addStretch()
        meta.addWidget(self._status_label)
        layout.addLayout(meta)

        # Description
        desc = QLabel(tool.description or "No description")
        desc.setObjectName("CardDesc")
        desc.setWordWrap(True)
        desc.setMaximumHeight(48)
        layout.addWidget(desc)

        layout.addStretch()

    # ── Status ───────────────────────────────────────────────────────────────────
    def refresh_status(self, runner) -> None:
        running = runner.is_running(self.tool.id)
        if running:
            pid = runner.pid_of(self.tool.id)
            started = runner.started_at_of(self.tool.id)
            started_txt = f" · {started:%H:%M}" if started else ""
            self._status_label.setText(f"● Running · {pid}{started_txt}")
        else:
            self._status_label.setText("○ Idle")
        _set_prop(self._status_label, "running", running)
        _set_prop(self, "running", running)

    # ── Events ───────────────────────────────────────────────────────────────────
    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        self.activated.emit(self.tool)

    def contextMenuEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        self.contextRequested.emit(self.tool, event.globalPos())

    # ── Helpers ──────────────────────────────────────────────────────────────────
    def _icon_pixmap(self, size: int):
        return tool_icon_pixmap(self.tool, size)

    def _tooltip(self) -> str:
        lines = [
            self.tool.name,
            f"Category: {self.tool.category or 'General'}",
            f"Folder: {self.tool.directory}",
            f"Entry: {self.tool.entry}",
        ]
        if self._launch_count:
            lines.append(f"Launched: {self._launch_count}×")
        lines.append("Double-click to launch · right-click for actions")
        return "\n".join(lines)


def _set_prop(widget, name: str, value: bool) -> None:
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
