# EXIF MCP Server

Inspect and remove EXIF metadata locally through MCP tools.

This project is a stdio-first Python MCP server for reading EXIF metadata,
detecting GPS/location fields, summarizing privacy-sensitive metadata, and
writing cleaned image copies with full or selective EXIF removal for supported
formats.

## What This Project Does

The server exposes eleven MCP tools for local image paths:

- `inspect_exif`
- `inspect_exif_detailed`
- `has_gps_exif`
- `find_images_with_gps_exif`
- `find_images_with_exif_fields`
- `summarize_exif_privacy`
- `strip_exif`
- `strip_selected_exif_fields`
- `batch_strip_exif`
- `batch_strip_gps_exif`
- `batch_strip_selected_exif_fields`

It also exposes two MCP resources and two MCP prompts:

- resources:
  - `exif://privacy-guide`
  - `exif://supported-formats`
- prompts:
  - `review-photo-privacy`
  - `clean-photos-for-sharing`

It is designed for AI clients and agent workflows, and this repository is
focused on the MCP server itself.

## Project Shape

This repository is MCP-first:

- the shared EXIF logic lives under `src/exif_mcp_server/core/`
- the MCP adapter lives under `src/exif_mcp_server/tools/`, `resources/`, and
  `prompts/`
- tests, examples, and docs are included so the project can work as a sample
  MCP server for learning and reuse

## Supported Formats

Current v1 support is intentionally narrow:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.tif`
- `.tiff`

Do not assume IPTC or XMP support in this MCP server.

## Install

Requirements:

- Python 3.11+

Set up a local virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Why quote `'.[dev]'`:
Some shells such as `zsh` treat brackets as glob patterns.

## Run Tests

Run the full test suite:

```bash
pytest
```

Run one focused test file:

```bash
pytest tests/test_inspect.py
pytest tests/test_privacy.py
pytest tests/test_clean.py
pytest tests/test_batch.py
```

The repo also includes manual-test sample images in `examples/sample_images/`.

## Lint And Type Check

Run Ruff:

```bash
ruff check .
```

Run mypy against the typed source tree:

```bash
mypy
```

The current mypy configuration checks `src/` and ignores missing type stubs for
`piexif`, which does not ship typed metadata.

## Continuous Integration

Use the same core verification steps before publishing changes:

- `ruff check .`
- `mypy`
- `pytest`

## Run The Server

Start the MCP server over stdio:

```bash
python -m exif_mcp_server.server
```

Or use the installed console entrypoint:

```bash
exif-mcp-server
```

The server will appear idle in the terminal because it is waiting for an MCP
client over stdio.

The default transport is still `stdio`. Remote transport is now optional and
must be selected explicitly.

## Remote Transport

The server can now run with:

- `stdio`
- `streamable-http`
- `sse`

Recommended remote transport:

- `streamable-http`

### Streamable HTTP

Run the server over Streamable HTTP on `127.0.0.1:8001`:

```bash
python -m exif_mcp_server.server --transport streamable-http
```

Choose a custom host, port, and endpoint path:

```bash
python -m exif_mcp_server.server \
  --transport streamable-http \
  --host 0.0.0.0 \
  --port 9000 \
  --streamable-http-path /mcp
```

Useful optional flags:

- `--json-response`
- `--stateless-http`

Equivalent environment variables:

- `EXIF_MCP_TRANSPORT=streamable-http`
- `EXIF_MCP_HOST=0.0.0.0`
- `EXIF_MCP_PORT=9000`
- `EXIF_MCP_STREAMABLE_HTTP_PATH=/mcp`
- `EXIF_MCP_JSON_RESPONSE=true`
- `EXIF_MCP_STATELESS_HTTP=true`

### SSE

Run the server over SSE:

```bash
python -m exif_mcp_server.server --transport sse
```

Customize host, port, mount path, and SSE endpoint paths:

```bash
python -m exif_mcp_server.server \
  --transport sse \
  --host 0.0.0.0 \
  --port 9001 \
  --mount-path /github \
  --sse-path /events \
  --message-path /messages/
```

Equivalent environment variables:

- `EXIF_MCP_TRANSPORT=sse`
- `EXIF_MCP_HOST=0.0.0.0`
- `EXIF_MCP_PORT=9001`
- `EXIF_MCP_MOUNT_PATH=/github`
- `EXIF_MCP_SSE_PATH=/events`
- `EXIF_MCP_MESSAGE_PATH=/messages/`

## Smoke Test

Quickly verify that the server can be created:

```bash
python -c "from exif_mcp_server.server import create_server; print(type(create_server()).__name__)"
```

Expected output:

```text
FastMCP
```

## MCP Inspector

This project is stdio-first. To test it in an MCP Inspector or another local
MCP client, configure a stdio server with:

- command: `.venv/bin/python`
- args: `-m exif_mcp_server.server`
- working directory: this repo root

If your MCP client expects the installed entrypoint instead, you can use:

- command: `.venv/bin/exif-mcp-server`

For a remote client that supports Streamable HTTP, run:

```bash
python -m exif_mcp_server.server --transport streamable-http --host 127.0.0.1 --port 8001
```

Then connect the client to:

```text
http://127.0.0.1:8001/mcp
```

Expected tools:

- `inspect_exif`
- `inspect_exif_detailed`
- `has_gps_exif`
- `find_images_with_gps_exif`
- `find_images_with_exif_fields`
- `summarize_exif_privacy`
- `strip_exif`
- `strip_selected_exif_fields`
- `batch_strip_exif`
- `batch_strip_gps_exif`
- `batch_strip_selected_exif_fields`

Expected resources:

- `exif://privacy-guide`
- `exif://supported-formats`

Expected prompts:

- `review-photo-privacy`
- `clean-photos-for-sharing`

## Client Examples

The exact configuration shape depends on the MCP client. The examples below
were checked against the official client docs on April 18, 2026.

### Which Client To Use

| Client | Best for | Local stdio | Remote HTTP | Notes |
| --- | --- | --- | --- | --- |
| Claude Code | terminal-first MCP workflows | yes | yes | best fit if you want quick local testing and CLI management |
| VS Code | editor-integrated development | yes | yes | good default if you want MCP tools inside a coding workspace |
| Cursor | editor-integrated AI workflows | yes | yes | good fit if your main coding flow already lives in Cursor |
| MCP Inspector | debugging and manual verification | yes | yes | best choice for checking raw tool/resource/prompt behavior |
| Claude Desktop | end-user desktop app workflows | limited | yes | local setup now centers on desktop extensions rather than raw stdio config |

Recommended starting points:

- use `MCP Inspector` for the first manual smoke test
- use `Claude Code` if you want the fastest terminal-based setup
- use `VS Code` or `Cursor` if you want the server available inside your editor
- use `streamable-http` when you want one running server shared by multiple clients

### Claude Code

Add the local stdio server:

```bash
claude mcp add --transport stdio exif-mcp -- \
  /absolute/path/to/image-mcp-server/.venv/bin/python \
  -m exif_mcp_server.server
```

Add the remote Streamable HTTP server:

```bash
claude mcp add --transport http exif-mcp-http \
  http://127.0.0.1:8001/mcp
```

If you want to use remote transport first, start the server separately:

```bash
python -m exif_mcp_server.server \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8001
```

Useful Claude Code commands:

- `claude mcp list`
- `claude mcp get exif-mcp`
- `/mcp`

### VS Code

VS Code uses `mcp.json` with a `"servers"` object. For a workspace-local setup,
create `.vscode/mcp.json` with:

```json
{
  "servers": {
    "exif-mcp": {
      "command": "/absolute/path/to/image-mcp-server/.venv/bin/python",
      "args": ["-m", "exif_mcp_server.server"]
    }
  }
}
```

For remote Streamable HTTP, use:

```json
{
  "servers": {
    "exif-mcp-http": {
      "type": "http",
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

Notes:

- workspace config lives in `.vscode/mcp.json`
- user-level config is available via `MCP: Open User Configuration`
- VS Code also supports auto-discovery from other apps such as Claude Desktop

### Cursor

Cursor uses `.cursor/mcp.json` in the project, or `~/.cursor/mcp.json`
globally, with an `"mcpServers"` object.

Project-local stdio example:

```json
{
  "mcpServers": {
    "exif-mcp": {
      "type": "stdio",
      "command": "/absolute/path/to/image-mcp-server/.venv/bin/python",
      "args": ["-m", "exif_mcp_server.server"]
    }
  }
}
```

Cursor's docs also support remote MCP configuration with fields such as `url`
and `headers`. For this server, the remote endpoint is:

```text
http://127.0.0.1:8001/mcp
```

### MCP Inspector

For a local stdio session:

```bash
npx @modelcontextprotocol/inspector \
  /absolute/path/to/image-mcp-server/.venv/bin/python \
  -m exif_mcp_server.server
```

For remote testing, first start the server:

```bash
python -m exif_mcp_server.server \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8001
```

Then connect the Inspector to:

```text
http://127.0.0.1:8001/mcp
```

### Claude Desktop

Claude Desktop's current official direction is different for local and remote
servers:

- local tools are now primarily packaged as desktop extensions (`.mcpb`)
- remote MCP servers are added through `Settings > Connectors`

This repo does not currently ship a Claude Desktop extension bundle, so the
most straightforward client setups today are Claude Code, VS Code, Cursor, or
MCP Inspector.

## MCP Resources

The server publishes two short static resources:

- `exif://privacy-guide`
  - practical explanation of EXIF privacy risk
  - what the server removes
  - what the server does not remove
- `exif://supported-formats`
  - currently supported image formats
  - overwrite behavior summary
  - stdio-first transport note

## MCP Prompts

The server publishes two prompt templates:

- `review-photo-privacy`
  - guides a client through `inspect_exif`, `has_gps_exif`, and `summarize_exif_privacy`
- `clean-photos-for-sharing`
  - guides a client through safe folder cleanup with `batch_strip_exif`

## Example Tool Calls

Useful local sample paths from this repo:

- `examples/sample_images/plain-no-exif.jpg`
- `examples/sample_images/basic-exif.jpg`
- `examples/sample_images/gps-exif.jpg`
- `examples/sample_images/tiff-exif.tiff`

`inspect_exif`

Input:

```json
{
  "image_path": "/absolute/path/to/photo.jpg"
}
```

Example output:

```json
{
  "image_path": "/absolute/path/to/photo.jpg",
  "has_exif": true,
  "exif": {
    "Make": "Apple",
    "Model": "iPhone 14",
    "DateTimeOriginal": "2026:04:16 10:30:00"
  },
  "warnings": []
}
```

`inspect_exif_detailed`

Input:

```json
{
  "image_path": "/absolute/path/to/photo.jpg"
}
```

Example output (trimmed):

```json
{
  "image_path": "/absolute/path/to/photo.jpg",
  "has_exif": true,
  "exif": {
    "Artist": "Blue J.",
    "Make": "Canon"
  },
  "warnings": [],
  "tags": [
    {
      "ifd": "0th",
      "tag_id": 315,
      "field_name": "Artist",
      "field_key": "Artist",
      "value": "Blue J."
    }
  ]
}
```

`has_gps_exif`

Input:

```json
{
  "image_path": "/absolute/path/to/photo.jpg"
}
```

`find_images_with_gps_exif`

Input:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "recursive": false,
  "extensions": null
}
```

Example output:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "scanned_count": 2,
  "matched_count": 1,
  "failed_count": 0,
  "skipped_count": 1,
  "matches": [
    {
      "image_path": "/absolute/path/to/folder/photo.jpg",
      "gps_fields_present": [
        "GPSLatitude",
        "GPSLatitudeRef",
        "GPSLongitude",
        "GPSLongitudeRef"
      ]
    }
  ],
  "failures": []
}
```

Example output:

```json
{
  "image_path": "/absolute/path/to/photo.jpg",
  "has_gps": true,
  "gps_fields_present": [
    "GPSLatitude",
    "GPSLatitudeRef",
    "GPSLongitude",
    "GPSLongitudeRef"
  ]
}
```

`find_images_with_exif_fields`

Input:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "field_names": ["Artist", "XPAuthor", "Copyright"],
  "match_mode": "any",
  "recursive": false,
  "extensions": null
}
```

Example output:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "requested_fields": ["Artist", "XPAuthor", "Copyright"],
  "match_mode": "any",
  "scanned_count": 2,
  "matched_count": 1,
  "failed_count": 0,
  "skipped_count": 1,
  "matches": [
    {
      "image_path": "/absolute/path/to/folder/author.jpg",
      "matched_fields": ["Artist"]
    }
  ],
  "failures": []
}
```

`summarize_exif_privacy`

Input:

```json
{
  "image_path": "/absolute/path/to/photo.jpg"
}
```

Example output:

```json
{
  "image_path": "/absolute/path/to/photo.jpg",
  "has_exif": true,
  "privacy_risk": "high",
  "findings": [
    {
      "field": "GPSLatitude",
      "severity": "high",
      "reason": "Location metadata can reveal where the photo was taken."
    }
  ],
  "summary": "This image contains GPS metadata."
}
```

`strip_exif`

Input:

```json
{
  "image_path": "/absolute/path/to/photo.jpg",
  "output_path": null,
  "overwrite": false,
  "dry_run": false,
  "include_comparison": false,
  "write_report": false
}
```

Example output:

```json
{
  "source_path": "/absolute/path/to/photo.jpg",
  "output_path": "/absolute/path/to/photo.cleaned.jpg",
  "removed_exif": true,
  "notes": [
    "Created sibling cleaned file.",
    "Removed EXIF metadata from the written image."
  ]
}
```

`strip_selected_exif_fields`

Input:

```json
{
  "image_path": "/absolute/path/to/photo.jpg",
  "field_names": ["Artist", "XPAuthor", "Copyright"],
  "output_path": null,
  "overwrite": false,
  "dry_run": false,
  "include_comparison": false,
  "write_report": false
}
```

Example output:

```json
{
  "source_path": "/absolute/path/to/photo.jpg",
  "output_path": "/absolute/path/to/photo.cleaned.jpg",
  "removed_fields": ["Artist"],
  "removed_tag_count": 1,
  "notes": [
    "Created sibling cleaned file.",
    "Removed selected EXIF fields from the written image."
  ]
}
```

`batch_strip_exif`

Input:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "output_folder": null,
  "recursive": false,
  "overwrite": false,
  "extensions": null,
  "dry_run": false,
  "include_comparison": false,
  "write_report": false
}
```

`batch_strip_selected_exif_fields`

Input:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "field_names": ["Artist", "XPAuthor", "Copyright"],
  "output_folder": "/absolute/path/to/cleaned",
  "recursive": false,
  "overwrite": false,
  "extensions": null,
  "dry_run": false,
  "include_comparison": false,
  "write_report": false
}
```

Example output:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "requested_fields": ["Artist", "XPAuthor", "Copyright"],
  "processed_count": 1,
  "success_count": 1,
  "failed_count": 0,
  "skipped_count": 0,
  "results": [
    {
      "source_path": "/absolute/path/to/folder/author.jpg",
      "output_path": "/absolute/path/to/cleaned/author.cleaned.jpg",
      "status": "success",
      "message": "Selected EXIF fields removed.",
      "removed_fields": ["Artist"],
      "removed_tag_count": 1
    }
  ]
}
```

`batch_strip_gps_exif`

Input:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "output_folder": "/absolute/path/to/cleaned",
  "recursive": false,
  "overwrite": false,
  "extensions": null,
  "dry_run": false,
  "include_comparison": false,
  "write_report": false
}
```

Example output:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "processed_count": 1,
  "success_count": 1,
  "failed_count": 0,
  "skipped_count": 0,
  "results": [
    {
      "source_path": "/absolute/path/to/folder/photo.jpg",
      "output_path": "/absolute/path/to/cleaned/photo.cleaned.jpg",
      "status": "success",
      "message": "GPS EXIF removed.",
      "removed_gps": true
    }
  ]
}
```

Example output:

```json
{
  "folder_path": "/absolute/path/to/folder",
  "processed_count": 2,
  "success_count": 1,
  "failed_count": 0,
  "skipped_count": 1,
  "results": [
    {
      "source_path": "/absolute/path/to/folder/photo.jpg",
      "output_path": "/absolute/path/to/folder/photo.cleaned.jpg",
      "status": "success",
      "message": "EXIF removed."
    },
    {
      "source_path": "/absolute/path/to/folder/ignore.bmp",
      "status": "skipped",
      "message": "Skipped because the file extension is not selected for batch processing."
    }
  ]
}
```

## Overwrite Safety

The server is safe by default:

- read-only tools do not modify files
- `strip_exif` does not overwrite the source file unless `overwrite=true`
- default sibling outputs such as `photo.cleaned.jpg` or `photo.cleaned.png`
  will not overwrite an
  existing file unless `overwrite=true`
- `batch_strip_exif` continues even if one file fails
- selective cleanup tools follow the same safe defaults:
  - `strip_selected_exif_fields`
  - `batch_strip_selected_exif_fields`

When `overwrite=true`, the server may rewrite the source image or replace an
existing target file.

## Optional Cleanup Features

`strip_exif`, `strip_selected_exif_fields`, `batch_strip_exif`,
`batch_strip_gps_exif`, and `batch_strip_selected_exif_fields` support three
optional features:

- `dry_run`
  - validate the request and show the predicted output path
  - no image files or report files are written
- `include_comparison`
  - include a compact before/after EXIF summary in the result
  - fields:
    - `before_has_exif`
    - `after_has_exif`
    - `removed_fields`
    - `remaining_fields`
- `write_report`
  - write a sidecar JSON report next to each cleaned output image
  - example sidecar path:
    - `photo.cleaned.exif-report.json`

Example `strip_exif` dry run:

```json
{
  "image_path": "/absolute/path/to/photo.jpg",
  "dry_run": true,
  "include_comparison": true,
  "write_report": true
}
```

Example dry-run result:

```json
{
  "source_path": "/absolute/path/to/photo.jpg",
  "output_path": "/absolute/path/to/photo.cleaned.jpg",
  "removed_exif": true,
  "dry_run": true,
  "comparison": {
    "before_has_exif": true,
    "after_has_exif": false,
    "removed_fields": ["DateTimeOriginal", "Make"],
    "remaining_fields": []
  },
  "notes": [
    "Created sibling cleaned file.",
    "Dry run only; no files were written.",
    "Dry run would remove EXIF metadata from the output image.",
    "Dry run skipped writing the sidecar JSON report."
  ]
}
```

Example sidecar report output:

```json
{
  "source_path": "/absolute/path/to/photo.jpg",
  "output_path": "/absolute/path/to/photo.cleaned.jpg",
  "removed_exif": true,
  "dry_run": false,
  "comparison": {
    "before_has_exif": true,
    "after_has_exif": false,
    "removed_fields": ["DateTimeOriginal", "Make"],
    "remaining_fields": []
  },
  "notes": [
    "Created sibling cleaned file.",
    "Removed EXIF metadata from the written image."
  ]
}
```

## Manual Testing With Sample Images

The repo includes small synthetic images under `examples/sample_images/`:

- `plain-no-exif.jpg`
- `basic-exif.jpg`
- `gps-exif.jpg`
- `tiff-exif.tiff`

Useful manual checks:

1. Call `inspect_exif` on `basic-exif.jpg` and confirm device/timestamp fields are present.
2. Call `has_gps_exif` on `gps-exif.jpg` and confirm GPS fields are detected.
3. Call `summarize_exif_privacy` on `gps-exif.jpg` and confirm the risk is `high`.
4. Call `strip_exif` on `gps-exif.jpg` and confirm the cleaned output has `has_exif: false`.
5. Call `find_images_with_gps_exif` on a folder and confirm only GPS-bearing files are returned.
6. Call `batch_strip_gps_exif` on a folder and confirm GPS data is removed while other EXIF fields remain when possible.
7. Call `batch_strip_exif` on `examples/sample_images/` and confirm supported files are processed and pre-existing `*.cleaned.<ext>` outputs are not overwritten unless requested.
8. Call `inspect_exif` or `strip_exif` on `tiff-exif.tiff` and confirm TIFF EXIF is inspected and cleaned correctly.
9. Call `find_images_with_exif_fields` with `["Artist", "XPAuthor", "Copyright"]` and confirm only author-bearing files match.
10. Call `batch_strip_selected_exif_fields` with an `output_folder` and confirm selected fields are removed while non-selected EXIF remains.

## Tool Error Format

Successful tool responses keep their normal JSON result shapes.

Tool failures are exposed with a stable error string prefix so MCP clients can
recognize and parse them predictably:

```text
EXIF_TOOL_ERROR {"code":"file_not_found","message":"...","tool":"inspect_exif"}
```

Current public error codes include:

- `file_not_found`
- `invalid_path`
- `invalid_metadata_selection`
- `unsupported_image_type`
- `exif_read_error`
- `exif_write_error`
- `unsafe_overwrite`
- `exif_error`
- `internal_error`

## Architecture Overview

The project is structured in three layers:

1. Shared core in `src/exif_mcp_server/core/`
2. Thin MCP tool wrappers in `src/exif_mcp_server/tools/`
3. Stdio server bootstrap in `src/exif_mcp_server/server.py`

The MCP layer is intentionally thin. EXIF reading, GPS detection, privacy
summary logic, GPS-folder scanning, single-file cleaning, and batch cleaning
live in the shared core.

## Current Status

The required MVP tools are implemented and the project now goes beyond the
original MVP:

- stdio, `streamable-http`, and `sse` transports are available
- JPG/JPEG/PNG/WebP/TIFF support is implemented and tested
- optional MCP resources and prompts are implemented
- GPS-focused folder scan and GPS-only batch cleanup tools are implemented

Still out of scope or future-facing:

- IPTC or XMP editing
- cloud storage workflows
- production auth and deployment hardening for remote transport


## License

MIT

## Books by the Authors

<p align="center">
  <a href="https://www.amazon.com/stores/Quiet-Line-Press/author/B0GR1QS773/allbooks">
    <img src="assets/books-qr.png" alt="QR code to our books on Amazon" width="200">
  </a>
  <br>
  <em>Scan to check out our books on Amazon</em>
</p>
