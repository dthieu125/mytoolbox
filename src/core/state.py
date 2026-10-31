"""Application-wide constants and paths for MyToolbox."""
from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "MyToolbox"
APP_VERSION = "2.0.0"

if getattr(sys, "frozen", False):
    # Running as a PyInstaller bundle
    APP_ROOT = Path(sys.executable).resolve().parent
else:
    # src/core/state.py -> src/core -> src -> MyToolbox
    APP_ROOT = Path(__file__).resolve().parents[2]

TOOLS_DIR = APP_ROOT / "tools"
LOGS_DIR = APP_ROOT / "logs"
ASSETS_DIR = APP_ROOT / "assets"
CONFIG_PATH = APP_ROOT / "config.json"
