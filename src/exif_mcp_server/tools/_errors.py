"""Shared MCP-facing error shaping for tool wrappers."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import TypeVar

from ..core.errors import (
    ExifMcpServerError,
    ExifReadError,
    ExifWriteError,
    FileNotFoundErrorMapped,
    InvalidMetadataSelectionError,
    InvalidPathError,
    UnsafeOverwriteError,
    UnsupportedImageTypeError,
)

T = TypeVar("T")
ERROR_PREFIX = "EXIF_TOOL_ERROR "


class StructuredToolError(ValueError):
    """A predictable tool-facing error string for MCP clients."""

    def __init__(self, tool_name: str, code: str, message: str):
        self.payload = {
            "tool": tool_name,
            "code": code,
            "message": message,
        }
        super().__init__(ERROR_PREFIX + json.dumps(self.payload, sort_keys=True))


def _error_code(error: Exception) -> str:
    """Map domain exceptions into stable public error codes."""

    if isinstance(error, FileNotFoundErrorMapped):
        return "file_not_found"
    if isinstance(error, InvalidPathError):
        return "invalid_path"
    if isinstance(error, InvalidMetadataSelectionError):
        return "invalid_metadata_selection"
    if isinstance(error, UnsupportedImageTypeError):
        return "unsupported_image_type"
    if isinstance(error, ExifReadError):
        return "exif_read_error"
    if isinstance(error, UnsafeOverwriteError):
        return "unsafe_overwrite"
    if isinstance(error, ExifWriteError):
        return "exif_write_error"
    if isinstance(error, ExifMcpServerError):
        return "exif_error"
    return "internal_error"


def run_with_mcp_error_handling(tool_name: str, operation: Callable[[], T]) -> T:
    """Execute one tool operation and raise a stable MCP-facing error on failure."""

    try:
        return operation()
    except Exception as exc:
        raise StructuredToolError(
            tool_name=tool_name,
            code=_error_code(exc),
            message=str(exc),
        ) from exc
