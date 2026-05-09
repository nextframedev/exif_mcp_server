# Changelog

All notable changes to this project should be documented in this file.

The format is inspired by Keep a Changelog.

## Unreleased

- Clarified CI guidance in README to use local verification steps.
- Improved CLI boolean flags with explicit `--no-*` overrides for env-backed options.
- Normalized GPS cleanup write errors through shared write handling.
- Updated mypy overrides to tolerate missing `mcp` import stubs.
- Updated server registration test to use public FastMCP listing APIs.

## 0.1.0

- Initial EXIF MCP server release
- Added read, privacy, single-file cleanup, and batch cleanup tools
- Added stdio, streamable HTTP, and SSE transports
- Added JPG, JPEG, PNG, WebP, and TIFF support
- Added resources, prompts, examples, tests, and CI
