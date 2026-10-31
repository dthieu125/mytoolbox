# MyToolbox

A lightweight launcher hub that manages all of your local Python tools as
independent applications — like a portable toolbox: open a tool when you need
it, close it when you're done. Tools run in **separate processes**, so a
crashed or closed tool never affects the toolbox or other tools.

Built with Python + PyQt6, same UI stack as the tools it manages.

## Quick start

```bat
python main.py            # normal launch
python main.py --hidden   # start directly in the system tray
```

## Features

### Managing tools
- **Auto-discovery** — every folder in `tools/` with a `tool.toml` becomes a tool
- **Search** (name, description, category) and **category filter** from the toolbar
- **Sort** by name, recently launched, or most launched (usage stats persist)
- **Pin favourites** to the top of the list (★ badge)
- **Hide tools** you rarely use; toggle "Show hidden tools" in the ⋯ menu
- **Install requirements** for a tool with live pip output (right-click → Install requirements…)
- Per-tool **launch counts**, history log, and per-tool log files

### Running tools
- **Double-click** a card/row to launch; if the tool is already running it is
  **brought to the foreground** (Windows)
- **Restart / terminate** a tool from its right-click menu
- Live status: `○ Idle` / `● Running · PID · start time`, refreshed every 2 s
- Tools are spawned detached (`CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS`), so
  closing MyToolbox never stops a tool; use Terminate or "Stop all tools" in tray

### Display
- **Grid view** with auto-reflowing cards (icon, category chip, name, version,
  description, favourite star, status)
- **List view** with sortable columns (Name, Category, Version, Status, Description);
  each row shows the tool's icon (or a coloured category fallback)
- Switch views with the toolbar button or `Ctrl+G`

### Interface & icons
- **Dark / light theme**, switchable at runtime (`Ctrl+T`) and persisted
- Custom **app icon** (blue toolbox badge) generated in code and exported as a
  multi-size `assets/app.ico` (`python scripts/generate_icons.py`)
- Tray icon shows a **green badge with the running-tool count**; tray menu lists
  running tools (click to focus) and offers "Stop all tools"
- Coloured fallback icons per category when a tool has no icon file
- Window geometry, theme, view mode, favourites, hidden list and stats are stored
  in portable `config.json` next to the app

### Keyboard shortcuts
| Shortcut | Action |
|---|---|
| `Ctrl+F` | Focus search box |
| `Ctrl+R` | Rescan `tools/` |
| `Ctrl+G` | Toggle grid / list view |
| `Ctrl+T` | Toggle dark / light theme |
| `Esc` | Clear search |

### System tray
- Closing the window hides to tray (tools keep running)
- Tray menu: Show, Refresh, running tools, Stop all, Exit

## Adding a new tool

1. Drop your tool folder into `tools/`
2. Add a `tool.toml` at its root:

   ```toml
   name = "My New Tool"
   version = "1.0.0"
   entry = "main.py"
   icon = "resources/icon.ico"          # optional
   category = "Utilities"               # optional, used for chips/filter
   description = "What it does."        # optional
   ```
3. Open MyToolbox (or press `Ctrl+R`) — the card appears automatically

No toolbox code changes are ever needed; `tool.toml` is the entire contract.

## Project structure

```
MyToolbox/
├── main.py                    # entry point
├── config.json                # generated: theme, favourites, stats, geometry
├── assets/app.ico             # generated multi-size app icon
├── scripts/
│   └── generate_icons.py      # regenerates assets/app.ico
├── src/
│   ├── core/
│   │   ├── config.py          # portable persistent settings + usage stats
│   │   ├── state.py           # app paths and constants
│   │   ├── scanner.py         # scans tools/ for tool.toml
│   │   ├── runner.py          # launches/tracks tools as subprocesses
│   │   └── windowing.py       # bring running tool windows to the foreground
│   └── ui/
│       ├── main_window.py     # toolbar, views, tray, tool management
│       ├── tool_card.py       # grid card
│       ├── tool_list.py       # list view
│       ├── tool_menu.py       # shared right-click menu
│       ├── deps_dialog.py     # pip install requirements dialog
│       ├── icons.py           # app/tray/fallback/category icons
│       └── style.py           # dark + light stylesheets
└── tools/
    └── my_autoclick/          # any folder with tool.toml is a tool
        ├── tool.toml
        ├── main.py
        └── ...
```

## Notes

- Tools are started with the same Python interpreter that runs MyToolbox, with
  `cwd` set to the tool folder, so relative paths inside tools keep working.
- Tool stdout/stderr is captured to `logs/<tool_id>-<timestamp>.log`
  (right-click a tool → Open log file).
- `config.json` is written on changes; delete it to reset all preferences.
