"""Scans tools/ for independent tool projects declared via ``tool.toml``.

A tool is any sub-directory of ``tools/`` that contains a ``tool.toml`` like:

    name = "My AutoClick"
    version = "1.0.0"
    entry = "main.py"
    icon = "resources/icon.ico"     # optional
    description = "Auto clicker"    # optional
    category = "Automation"         # optional

Directories without a manifest are reported as warnings and skipped, so adding
a new tool without touching the toolbox code is just: copy folder + add tool.toml.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from src.core.state import TOOLS_DIR


@dataclass(frozen=True)
class ToolInfo:
    id: str              # folder name, unique key used for process tracking
    name: str
    version: str
    entry: str
    description: str
    category: str
    directory: Path
    icon_path: Path | None

    @property
    def entry_path(self) -> Path:
        return self.directory / self.entry


def scan_tools(tools_dir: Path = TOOLS_DIR) -> tuple[list[ToolInfo], list[str]]:
    """Return (valid_tools, warnings) for everything under ``tools_dir``."""
    tools: list[ToolInfo] = []
    warnings: list[str] = []

    if not tools_dir.exists():
        warnings.append(f"Tools folder not found: {tools_dir}")
        return tools, warnings

    for item in sorted(tools_dir.iterdir(), key=lambda p: p.name.casefold()):
        if not item.is_dir():
            continue
        if item.name in ("__pycache__",) or item.name.startswith((".", "_")):
            continue

        manifest = item / "tool.toml"
        if not manifest.exists():
            warnings.append(f"{item.name}: missing tool.toml — skipped")
            continue

        try:
            data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, OSError) as exc:
            warnings.append(f"{item.name}: bad tool.toml ({exc}) — skipped")
            continue

        entry = str(data.get("entry") or "").strip()
        if not entry:
            warnings.append(f"{item.name}: tool.toml has no 'entry' — skipped")
            continue
        if not (item / entry).exists():
            warnings.append(f"{item.name}: entry '{entry}' not found — skipped")
            continue

        icon_raw = str(data.get("icon") or "").strip()
        icon_path: Path | None = None
        if icon_raw:
            candidate = item / icon_raw
            if candidate.exists():
                icon_path = candidate

        tools.append(
            ToolInfo(
                id=item.name,
                name=str(data.get("name") or item.name),
                version=str(data.get("version") or "").strip(),
                entry=entry,
                description=str(data.get("description") or "").strip(),
                category=str(data.get("category") or "").strip(),
                directory=item,
                icon_path=icon_path,
            )
        )
    return tools, warnings
