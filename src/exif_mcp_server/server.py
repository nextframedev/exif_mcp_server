"""Configurable MCP server entrypoint for EXIF tools."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Any, Literal, cast

from .prompts import register_prompts
from .resources import register_resources
from .tools import register_all_tools

Transport = Literal["stdio", "sse", "streamable-http"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

SERVER_NAME = "exif-mcp-server"
SERVER_INSTRUCTIONS = (
    "Inspect EXIF metadata, detect GPS fields, summarize privacy risks, find images "
    "with GPS metadata in a folder, and strip EXIF or GPS EXIF from JPG, JPEG, PNG, "
    "WebP, and TIFF images using explicit local file paths."
)


@dataclass(frozen=True)
class ServerConfig:
    """Runtime configuration for the EXIF MCP server."""

    transport: Transport = "stdio"
    host: str = "127.0.0.1"
    port: int = 8001
    mount_path: str = "/"
    sse_path: str = "/sse"
    message_path: str = "/messages/"
    streamable_http_path: str = "/mcp"
    debug: bool = False
    log_level: LogLevel = "INFO"
    json_response: bool = False
    stateless_http: bool = False


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable safely."""

    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable safely."""

    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


def _env_transport(default: Transport = "stdio") -> Transport:
    """Read the server transport from environment."""

    raw = os.getenv("EXIF_MCP_TRANSPORT")
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized not in {"stdio", "sse", "streamable-http"}:
        raise ValueError(
            "Environment variable EXIF_MCP_TRANSPORT must be one of: "
            "stdio, sse, streamable-http."
        )
    return cast(Transport, normalized)


def config_from_env() -> ServerConfig:
    """Build server configuration from environment variables."""

    log_level = os.getenv("EXIF_MCP_LOG_LEVEL", "INFO").strip().upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(
            "Environment variable EXIF_MCP_LOG_LEVEL must be one of: "
            "DEBUG, INFO, WARNING, ERROR, CRITICAL."
        )

    return ServerConfig(
        transport=_env_transport(),
        host=os.getenv("EXIF_MCP_HOST", "127.0.0.1"),
        port=_env_int("EXIF_MCP_PORT", 8001),
        mount_path=os.getenv("EXIF_MCP_MOUNT_PATH", "/"),
        sse_path=os.getenv("EXIF_MCP_SSE_PATH", "/sse"),
        message_path=os.getenv("EXIF_MCP_MESSAGE_PATH", "/messages/"),
        streamable_http_path=os.getenv("EXIF_MCP_STREAMABLE_HTTP_PATH", "/mcp"),
        debug=_env_bool("EXIF_MCP_DEBUG", False),
        log_level=cast(LogLevel, log_level),
        json_response=_env_bool("EXIF_MCP_JSON_RESPONSE", False),
        stateless_http=_env_bool("EXIF_MCP_STATELESS_HTTP", False),
    )


def parse_args(argv: list[str] | None = None) -> ServerConfig:
    """Parse CLI arguments into server configuration."""

    env_defaults = config_from_env()
    parser = argparse.ArgumentParser(description="Run the EXIF MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=env_defaults.transport,
        help="Transport to run. Defaults to stdio.",
    )
    parser.add_argument(
        "--host",
        default=env_defaults.host,
        help="Host for remote transports.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=env_defaults.port,
        help="Port for remote transports.",
    )
    parser.add_argument(
        "--mount-path",
        default=env_defaults.mount_path,
        help="Mount path for SSE transport.",
    )
    parser.add_argument("--sse-path", default=env_defaults.sse_path, help="SSE endpoint path.")
    parser.add_argument(
        "--message-path",
        default=env_defaults.message_path,
        help="SSE message POST endpoint path.",
    )
    parser.add_argument(
        "--streamable-http-path",
        default=env_defaults.streamable_http_path,
        help="Streamable HTTP endpoint path.",
    )
    parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        default=env_defaults.debug,
        help="Enable debug mode.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=env_defaults.log_level,
        help="Server log level.",
    )
    parser.add_argument(
        "--json-response",
        action=argparse.BooleanOptionalAction,
        default=env_defaults.json_response,
        help="Enable JSON responses for streamable HTTP transport.",
    )
    parser.add_argument(
        "--stateless-http",
        action=argparse.BooleanOptionalAction,
        default=env_defaults.stateless_http,
        help="Enable stateless streamable HTTP sessions.",
    )
    args = parser.parse_args(argv)
    return ServerConfig(
        transport=cast(Transport, args.transport),
        host=args.host,
        port=args.port,
        mount_path=args.mount_path,
        sse_path=args.sse_path,
        message_path=args.message_path,
        streamable_http_path=args.streamable_http_path,
        debug=args.debug,
        log_level=cast(LogLevel, args.log_level),
        json_response=args.json_response,
        stateless_http=args.stateless_http,
    )


def create_server(config: ServerConfig | None = None) -> Any:
    """Create and configure the MCP server."""

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "The MCP Python SDK is required to run the EXIF MCP server. "
            "Install project dependencies first."
        ) from exc

    config = config or ServerConfig()
    server = FastMCP(
        name=SERVER_NAME,
        instructions=SERVER_INSTRUCTIONS,
        host=config.host,
        port=config.port,
        mount_path=config.mount_path,
        sse_path=config.sse_path,
        message_path=config.message_path,
        streamable_http_path=config.streamable_http_path,
        debug=config.debug,
        log_level=config.log_level,
        json_response=config.json_response,
        stateless_http=config.stateless_http,
    )
    register_all_tools(server)
    register_resources(server)
    register_prompts(server)
    return server


def main(argv: list[str] | None = None) -> None:
    """Run the MCP server using the configured transport."""

    config = parse_args(argv)
    server = create_server(config)
    server.run(
        transport=config.transport,
        mount_path=config.mount_path if config.transport == "sse" else None,
    )


if __name__ == "__main__":
    main()
