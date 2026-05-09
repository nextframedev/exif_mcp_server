"""MCP tool wrapper for privacy-oriented EXIF summaries."""

from __future__ import annotations

from typing import Any

from ..core.exif_reader import summarize_exif_privacy as summarize_exif_privacy_core
from ..core.models import SummarizeExifPrivacyResult
from ._errors import run_with_mcp_error_handling


def summarize_exif_privacy(image_path: str) -> SummarizeExifPrivacyResult:
    """Summarize privacy-sensitive EXIF fields for a single image path."""

    return run_with_mcp_error_handling(
        "summarize_exif_privacy",
        lambda: summarize_exif_privacy_core(image_path=image_path),
    )


def register_privacy_tools(server: Any) -> None:
    """Register privacy tools on the provided MCP server instance."""

    server.tool()(summarize_exif_privacy)
