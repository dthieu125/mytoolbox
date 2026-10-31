# Local tools

This folder holds the tools managed by MyToolbox. **Tool folders are not
committed** (see `.gitignore`) — each tool is an independent project, and the
toolbox itself only needs its manifest.

## Adding a tool

1. Copy the tool project into this folder, e.g. `tools/my_tool/`
2. Add a `tool.toml` at the tool's root:

   ```toml
   name = "My Tool"
   version = "1.0.0"
   entry = "main.py"
   icon = "resources/icon.ico"     # optional
   category = "Utilities"          # optional
   description = "What it does."   # optional
   ```

3. Open MyToolbox (or press `Ctrl+R`) — the tool card appears automatically.

A copy of the manifest format lives in `tool.toml.example` at the repository
root.

## How tools are launched

Each tool is started as an independent subprocess:

```python
subprocess.Popen([sys.executable, entry],
                 cwd=tool_directory,
                 creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS)
```

So tools cannot crash the toolbox and keep running after it closes. Tool
stdout/stderr is captured to `logs/<tool-id>-<timestamp>.log`.
