"""Theme tokens and stylesheet generation for MyToolbox (dark + light)."""
from __future__ import annotations

from string import Template

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#1b1e21",
        "panel": "#23282c",
        "panel_alt": "#1f2428",
        "hover": "#2c3238",
        "border": "#323a40",
        "border_hover": "#4aa3df",
        "text": "#e8eaed",
        "text_dim": "#9aa0a6",
        "accent": "#4aa3df",
        "accent_text": "#0d1b24",
        "run": "#7bd88f",
        "warn": "#ffb74d",
        "star": "#f5c04a",
    },
    "light": {
        "bg": "#f4f6f8",
        "panel": "#ffffff",
        "panel_alt": "#f0f3f6",
        "hover": "#eaf2f8",
        "border": "#d7dde3",
        "border_hover": "#2f80c9",
        "text": "#1f2328",
        "text_dim": "#5f6b76",
        "accent": "#2f80c9",
        "accent_text": "#ffffff",
        "run": "#2e7d32",
        "warn": "#b26a00",
        "star": "#d99a1f",
    },
}

_QSS = Template("""
QWidget {
    background: $bg;
    color: $text;
    font-size: 12px;
}
QMainWindow, QDialog { background: $bg; }
QLabel { background: transparent; }

QLabel#Title { font-size: 18px; font-weight: 600; color: $text; }
QLabel#Subtitle { color: $text_dim; font-size: 11px; }
QLabel#Warning { color: $warn; }
QLabel#EmptyState { color: $text_dim; font-size: 13px; }
QLabel#Star { color: $star; font-size: 14px; }

/* ── Tool cards ─────────────────────────────────────────────────────── */
QFrame#ToolCard {
    background: $panel;
    border: 1px solid $border;
    border-radius: 10px;
}
QFrame#ToolCard:hover {
    background: $hover;
    border: 1px solid $border_hover;
}
QFrame#ToolCard[running="true"] { border: 1px solid $run; }
QFrame#ToolCard[running="true"]:hover { border: 1px solid $border_hover; }
QFrame#ToolCard[hidden="true"] {
    background: $panel_alt;
    border: 1px dashed $border;
}

QLabel#CardTitle { font-size: 13px; font-weight: 600; color: $text; }
QLabel#CardVersion, QLabel#CardStatus {
    color: $text_dim;
    font-size: 11px;
    background: transparent;
}
QLabel#CardStatus[running="true"] { color: $run; }
QLabel#CardDesc { color: $text_dim; font-size: 11px; }

/* ── Buttons ────────────────────────────────────────────────────────── */
QPushButton, QToolButton {
    background: $panel;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 5px 10px;
    color: $text;
}
QPushButton:hover, QToolButton:hover {
    background: $hover;
    border-color: $border_hover;
}
QPushButton:pressed, QToolButton:pressed { background: $panel_alt; }
QToolButton::menu-indicator { image: none; }

/* ── Inputs ─────────────────────────────────────────────────────────── */
QLineEdit, QComboBox {
    background: $panel;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 5px 8px;
    color: $text;
    selection-background-color: $accent;
    selection-color: $accent_text;
}
QLineEdit:focus, QComboBox:focus, QComboBox:on { border-color: $border_hover; }
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background: $panel;
    border: 1px solid $border;
    color: $text;
    selection-background-color: $accent;
    selection-color: $accent_text;
    outline: none;
}

/* ── List view ──────────────────────────────────────────────────────── */
QTreeWidget {
    background: $panel;
    border: 1px solid $border;
    border-radius: 8px;
    alternate-background-color: $panel_alt;
    outline: none;
}
QTreeWidget::item { padding: 5px 4px; }
QTreeWidget::item:hover { background: $hover; }
QTreeWidget::item:selected { background: $accent; color: $accent_text; }
QHeaderView::section {
    background: $panel_alt;
    color: $text_dim;
    border: none;
    border-bottom: 1px solid $border;
    padding: 6px;
    font-weight: 600;
}

/* ── Chrome ─────────────────────────────────────────────────────────── */
QStatusBar { color: $text_dim; background: transparent; }

QMenu {
    background: $panel;
    border: 1px solid $border;
    padding: 4px;
}
QMenu::item { padding: 5px 20px; border-radius: 4px; }
QMenu::item:selected { background: $hover; }
QMenu::item:disabled { color: $text_dim; }
QMenu::separator { height: 1px; background: $border; margin: 4px 8px; }

QToolTip {
    background: $panel;
    color: $text;
    border: 1px solid $border;
    padding: 4px;
}

QPlainTextEdit {
    background: $panel;
    border: 1px solid $border;
    border-radius: 8px;
    color: $text;
    font-family: Consolas, monospace;
    font-size: 11px;
    selection-background-color: $accent;
}

/* ── Scrolling ──────────────────────────────────────────────────────── */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical {
    background: $border;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: $text_dim; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal {
    background: $border;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover { background: $text_dim; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
""")


def get_stylesheet(theme: str) -> str:
    tokens = THEMES.get(theme, THEMES["dark"])
    return _QSS.safe_substitute(tokens)


def other_theme(theme: str) -> str:
    return "light" if theme == "dark" else "dark"
