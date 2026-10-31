"""
Entry point for MyToolbox — a launcher hub for the tools in tools/.

Usage:
  python main.py            — normal launch
  python main.py --hidden   — start hidden in the system tray

How tools work:
  Each sub-directory of tools/ with a tool.toml is an independent tool.
  Double-click its card to launch it as a standalone subprocess.
"""
from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from src.core.config import Config
from src.core.state import APP_NAME, APP_ROOT, APP_VERSION, CONFIG_PATH
from src.ui.icons import build_app_icon
from src.ui.main_window import MainWindow
from src.ui.style import get_stylesheet


def _application_icon() -> QIcon:
    """Prefer the generated multi-size assets/app.ico; fall back to painting it."""
    ico = APP_ROOT / "assets" / "app.ico"
    if ico.exists():
        return QIcon(str(ico))
    return build_app_icon()


def main() -> int:
    # Qt6 handles PER_MONITOR_AWARE_V2 automatically (same as my_autoclick).
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setWindowIcon(_application_icon())
    # Keep running in the tray even when the window is closed.
    app.setQuitOnLastWindowClosed(False)

    config = Config(CONFIG_PATH)
    app.setStyleSheet(get_stylesheet(config.theme))

    window = MainWindow(config)
    if "--hidden" in sys.argv:
        window.hide()
    else:
        window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
