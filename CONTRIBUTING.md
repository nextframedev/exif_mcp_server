# Contributing

Thanks for contributing to `exif-mcp-server`.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Development Checks

Run these before opening a pull request:

```bash
ruff check .
mypy
pytest
```

## Project Guidelines

- Keep the MCP adapter thin.
- Put EXIF logic in `src/exif_mcp_server/core/`.
- Keep tool names and output shapes stable.
- Do not overwrite files by default.
- Only claim format support when it is tested.

## Pull Requests

Please include:

- a short description of the change
- notes on any user-facing behavior changes
- updated docs when behavior changes
- tests for new supported behavior
