"""Programmatic icons: app badge, tool fallbacks, category colours, tray badge."""
from __future__ import annotations

import zlib

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
)

# Hues chosen to stay readable on both the dark and light themes.
CATEGORY_COLORS = [
    "#2f80c9",
    "#3a8f4d",
    "#b5771f",
    "#b35353",
    "#7d5fbf",
    "#2f8f88",
]


def _stable_hash(text: str) -> int:
    return zlib.crc32((text or "").encode("utf-8"))


def category_color(category: str) -> str:
    if not category:
        return CATEGORY_COLORS[0]
    return CATEGORY_COLORS[_stable_hash(category) % len(CATEGORY_COLORS)]


def category_chip_style(category: str) -> str:
    """Inline stylesheet for a category chip; works in dark and light themes."""
    color = QColor(category_color(category))
    return (
        f"background: rgba({color.red()},{color.green()},{color.blue()},0.16);"
        f"color: {color.name()};"
        "border-radius: 4px; padding: 0px 6px; font-size: 10px;"
    )


def _rounded_square(painter: QPainter, size: float, top: str, bottom: str) -> None:
    gradient = QLinearGradient(0, 0, 0, size)
    gradient.setColorAt(0.0, QColor(top))
    gradient.setColorAt(1.0, QColor(bottom))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(gradient)
    radius = size * 0.22
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)


def _toolbox_pixmap(size: int) -> QPixmap:
    """MyToolbox app icon: white toolbox in a blue rounded badge."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = float(size)

    _rounded_square(painter, s, "#3d7ea6", "#1f4d6b")

    # Handle of the toolbox (arc).
    pen = QPen(QColor("#ffffff"))
    pen.setWidthF(max(1.0, s * 0.065))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(
        QRectF(s * 0.32, s * 0.24, s * 0.36, s * 0.30),
        0,
        180 * 16,
    )

    # Body.
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 255, 255, 236))
    painter.drawRoundedRect(QRectF(s * 0.18, s * 0.40, s * 0.64, s * 0.36), s * 0.06, s * 0.06)

    # Lid seam.
    pen = QPen(QColor("#2a5f80"))
    pen.setWidthF(max(1.0, s * 0.03))
    painter.setPen(pen)
    painter.drawLine(QPointF(s * 0.18, s * 0.50), QPointF(s * 0.82, s * 0.50))

    # Latch.
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#3d7ea6"))
    painter.drawRoundedRect(QRectF(s * 0.44, s * 0.46, s * 0.12, s * 0.08), s * 0.02, s * 0.02)

    painter.end()
    return pixmap


def build_app_icon() -> QIcon:
    """Crisp multi-size MyToolbox icon."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_toolbox_pixmap(size))
    return icon


def tray_icon(running_count: int = 0) -> QIcon:
    """Tray icon with an optional green badge showing the running-tool count."""
    pixmap = _toolbox_pixmap(64)
    if running_count > 0:
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#43a047"))
        diameter = 26.0
        painter.drawEllipse(QRectF(64 - diameter - 1, 64 - diameter - 1, diameter, diameter))
        painter.setPen(QColor("#ffffff"))
        font = QFont()
        font.setBold(True)
        font.setPixelSize(17 if running_count < 10 else 14)
        painter.setFont(font)
        text = str(running_count) if running_count < 10 else "9+"
        painter.drawText(
            QRectF(64 - diameter - 1, 64 - diameter - 1, diameter, diameter),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )
        painter.end()
    return QIcon(pixmap)


def fallback_tool_pix(letter: str, size: int, category: str = "", seed: str = "") -> QPixmap:
    """Rounded gradient badge with the tool's first letter when no icon file."""
    color = QColor(category_color(category or seed))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    _rounded_square(painter, float(size), color.lighter(118).name(), color.darker(118).name())

    painter.setPen(QColor("#ffffff"))
    font = QFont()
    font.setBold(True)
    font.setPixelSize(max(8, int(size * 0.52)))
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, (letter or "?")[:1].upper())

    painter.end()
    return pixmap


def tool_icon_pixmap(tool, size: int) -> QPixmap:
    """Icon for a tool at an exact pixel size (icon file, else category fallback)."""
    if tool.icon_path:
        pixmap = QIcon(str(tool.icon_path)).pixmap(size, size)
        if pixmap.width() < size:
            pixmap = pixmap.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        return pixmap
    return fallback_tool_pix(
        tool.name,
        size,
        category=tool.category,
        seed=tool.id,
    )


def tool_icon(tool, size: int = 32) -> QIcon:
    """QIcon for a tool, used by list rows and any other compact widget."""
    return QIcon(tool_icon_pixmap(tool, size))
