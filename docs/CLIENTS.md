# Clients

This document collects concrete connection examples for common MCP clients.

## Supported Client Styles

- local stdio clients
- remote Streamable HTTP clients
- remote SSE clients when needed

## Quick Recommendation

- Use `MCP Inspector` for manual tool verification.
- Use `Claude Code` for terminal-first workflows.
- Use `VS Code` or `Cursor` for editor-integrated workflows.
- Use `streamable-http` when you want one running server shared by multiple clients.

## Example Config Files

See:

- `examples/client_configs/claude-code.md`
- `examples/client_configs/vscode-mcp.json`
- `examples/client_configs/cursor-mcp.json`
- `examples/client_configs/inspector.md`

## Remote Endpoint

When you run the server with Streamable HTTP:

```bash
python -m exif_mcp_server.server --transport streamable-http
```

The default endpoint is:

```text
http://127.0.0.1:8001/mcp
```

## Notes

- `stdio` remains the simplest local development path.
- `streamable-http` is the recommended remote transport.
- `sse` is supported, but most users should start with `stdio` or `streamable-http`.
