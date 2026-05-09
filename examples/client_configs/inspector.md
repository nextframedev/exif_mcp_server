# MCP Inspector

Run a local stdio session:

```bash
npx @modelcontextprotocol/inspector \
  /absolute/path/to/exif_mcp_server/.venv/bin/python \
  -m exif_mcp_server.server
```

For remote testing:

```bash
python -m exif_mcp_server.server \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8001
```

Then connect the inspector to:

```text
http://127.0.0.1:8001/mcp
```
