from __future__ import annotations

import json

from exif_mcp_server.tools._errors import ERROR_PREFIX


def parse_tool_error(exc: Exception) -> dict[str, str]:
    message = str(exc)
    assert message.startswith(ERROR_PREFIX)
    return json.loads(message[len(ERROR_PREFIX) :])
