"""Thin MCP tool registration layer."""

from __future__ import annotations

from typing import Any

from .batch import register_batch_tools
from .clean import register_clean_tools
from .inspect import register_inspection_tools
from .privacy import register_privacy_tools


def register_all_tools(server: Any) -> None:
    """Register the initial EXIF tool set on an MCP server instance."""

    register_inspection_tools(server)
    register_privacy_tools(server)
    register_clean_tools(server)
    register_batch_tools(server)

