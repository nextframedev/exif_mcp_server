"""EXIF MCP server package."""

from typing import Any


def create_server(*args: Any, **kwargs: Any) -> Any:
	"""Create the server via a lazy import to avoid module preload side effects."""

	from .server import create_server as _create_server

	return _create_server(*args, **kwargs)

__all__ = ["create_server"]

