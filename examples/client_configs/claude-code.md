# Claude Code

Add the local stdio server:

```bash
claude mcp add --transport stdio exif-mcp -- \
  /absolute/path/to/exif_mcp_server/.venv/bin/python \
  -m exif_mcp_server.server
```

Add the remote Streamable HTTP server:

```bash
claude mcp add --transport http exif-mcp-http \
  http://127.0.0.1:8001/mcp
```
