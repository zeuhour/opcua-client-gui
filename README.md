# opcua-client

Simple OPC-UA GUI client built on [asyncua](https://github.com/FreeOpcUa/opcua-asyncio)
and PyQt6.

![Screenshot](/screenshot.png?raw=true "Screenshot")

PRs welcome for any wished improvements.

## Features

- Connect / disconnect, with automatic reconnect when the transport drops:
  views grey out and a status-bar banner is shown while the supervisor
  re-establishes the session.
- Browse the address space with per-node-type icons.
- Show attributes and references for the selected node.
- Subscribe to variable data changes and to events.
- Write variable values.
- GUI for application certificates and per-server security mode / policy.
- Call methods (with dialog).
- Live-plot subscribed variables (pyqtgraph).
- Persist connection history, the last-browsed node per server, and window
  layout via `QSettings`.
- Context menu with handy helpers: copy NodeId, or copy the full browse path
  so you can paste it into your own code:
  `client.nodes.root.get_child(['0:Objects', '2:MyNode'])`.

## Install

PyQt6 is required. Python 3.14 or newer.

```
pip install opcua-client
opcua-client
```

`pip install opcua-client --upgrade` to update.

## Development

The project uses [`uv`](https://docs.astral.sh/uv/) for environment and build
management.

```
uv sync             # install deps + dev tools into .venv
uv run python app.py
uv run python tests.py           # integration tests need a free port
uv run mypy uaclient uawidgets   # type check
```

After editing any `.ui` or `.qrc` source, run `make` to regenerate
`uaclient/*_ui.py`, `uaclient/theme/breeze_resources.py`, and
`uawidgets/resources.py`. Targets:

- `make` — regenerate UI / resource Python from Qt sources.
- `make run` — launch the GUI.
- `make edit` — open the main `.ui` in Qt Creator.

Cutting a release:

```
uv run python release.py    # bumps pyproject.toml, tags, uv build, uv publish
```

`asyncua` is currently consumed via a local path source
(`[tool.uv.sources] asyncua = { path = "../opcua-asyncio", editable = true }`)
because the 2.x line is still in pre-release. Drop the source entry once
`asyncua>=2.0` is on PyPI.

## TODO

- History read.
