"""Persistent user preferences and usage stats, stored in config.json next to the app.

Keeping the config file beside the app makes MyToolbox portable: copy the
folder anywhere and favourites, hidden tools, theme and usage stats travel
with it.
"""
from __future__ import annotations

import copy
import json
import time
from pathlib import Path

DEFAULTS: dict = {
    "theme": "dark",            # "dark" | "light"
    "view_mode": "grid",        # "grid" | "list"
    "sort_mode": "name",        # "name" | "recent" | "most"
    "show_hidden": False,
    "category": "",             # "" = all categories
    "favorites": [],
    "hidden": [],
    "launch_counts": {},
    "last_launched": {},
    "window": {},               # {"x","y","width","height","maximized"}
}


class Config:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict = {}
        self._load()

    # ── Persistence ─────────────────────────────────────────────────────────────
    def _load(self) -> None:
        raw: dict = {}
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raw = {}
        self.data = copy.deepcopy(DEFAULTS)
        if isinstance(raw, dict):
            for key in DEFAULTS:
                if key in raw:
                    self.data[key] = raw[key]
        # Normalise list/mapping types in case of hand-edited config files.
        for key in ("favorites", "hidden"):
            value = self.data.get(key)
            if not isinstance(value, list):
                self.data[key] = []
        for key in ("launch_counts", "last_launched", "window"):
            value = self.data.get(key)
            if not isinstance(value, dict):
                self.data[key] = {}

    def save(self) -> None:
        try:
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(self.data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp.replace(self.path)
        except OSError:
            pass  # read-only location: run with defaults, do not crash the UI

    # ── Scalar settings ────────────────────────────────────────────────────────
    @property
    def theme(self) -> str:
        return self.data.get("theme") or "dark"

    @theme.setter
    def theme(self, value: str) -> None:
        self.data["theme"] = value
        self.save()

    @property
    def view_mode(self) -> str:
        return self.data.get("view_mode") or "grid"

    @view_mode.setter
    def view_mode(self, value: str) -> None:
        self.data["view_mode"] = value
        self.save()

    @property
    def sort_mode(self) -> str:
        return self.data.get("sort_mode") or "name"

    @sort_mode.setter
    def sort_mode(self, value: str) -> None:
        self.data["sort_mode"] = value
        self.save()

    @property
    def show_hidden(self) -> bool:
        return bool(self.data.get("show_hidden"))

    @show_hidden.setter
    def show_hidden(self, value: bool) -> None:
        self.data["show_hidden"] = bool(value)
        self.save()

    @property
    def category(self) -> str:
        return self.data.get("category") or ""

    @category.setter
    def category(self, value: str) -> None:
        self.data["category"] = value
        self.save()

    # ── Tool management ────────────────────────────────────────────────────────
    def is_favorite(self, tool_id: str) -> bool:
        return tool_id in self.data["favorites"]

    def toggle_favorite(self, tool_id: str) -> bool:
        favorites = self.data["favorites"]
        if tool_id in favorites:
            favorites.remove(tool_id)
            result = False
        else:
            favorites.append(tool_id)
            result = True
        self.save()
        return result

    def is_hidden(self, tool_id: str) -> bool:
        return tool_id in self.data["hidden"]

    def set_hidden(self, tool_id: str, hidden: bool) -> None:
        hidden_list = self.data["hidden"]
        if hidden and tool_id not in hidden_list:
            hidden_list.append(tool_id)
        elif not hidden and tool_id in hidden_list:
            hidden_list.remove(tool_id)
        self.save()

    # ── Usage stats ────────────────────────────────────────────────────────────
    def record_launch(self, tool_id: str) -> None:
        counts = self.data["launch_counts"]
        counts[tool_id] = int(counts.get(tool_id, 0)) + 1
        self.data["last_launched"][tool_id] = time.time()
        self.save()

    def launch_count(self, tool_id: str) -> int:
        try:
            return int(self.data["launch_counts"].get(tool_id, 0))
        except (TypeError, ValueError):
            return 0

    def last_launched(self, tool_id: str) -> float:
        try:
            return float(self.data["last_launched"].get(tool_id, 0.0))
        except (TypeError, ValueError):
            return 0.0

    # ── Window geometry ────────────────────────────────────────────────────────
    def window_state(self) -> dict:
        return dict(self.data.get("window") or {})

    def store_window_state(self, state: dict) -> None:
        self.data["window"] = state
        self.save()
