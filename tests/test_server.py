from __future__ import annotations

import asyncio
from typing import Any, get_type_hints

from exif_mcp_server.server import ServerConfig, config_from_env, create_server, parse_args
from exif_mcp_server.tools.batch import (
    batch_strip_exif,
    batch_strip_gps_exif,
    batch_strip_selected_exif_fields,
)
from exif_mcp_server.tools.clean import strip_exif, strip_selected_exif_fields


def test_server_registers_expected_tools_resources_and_prompts() -> None:
    server = create_server()

    tool_names = sorted(tool.name for tool in asyncio.run(server.list_tools()))
    resource_uris = sorted(str(resource.uri) for resource in asyncio.run(server.list_resources()))
    prompt_names = sorted(prompt.name for prompt in asyncio.run(server.list_prompts()))

    assert tool_names == [
        "batch_strip_exif",
        "batch_strip_gps_exif",
        "batch_strip_selected_exif_fields",
        "find_images_with_exif_fields",
        "find_images_with_gps_exif",
        "has_gps_exif",
        "inspect_exif",
        "inspect_exif_detailed",
        "strip_exif",
        "strip_selected_exif_fields",
        "summarize_exif_privacy",
    ]
    assert resource_uris == [
        "exif://privacy-guide",
        "exif://supported-formats",
    ]
    assert prompt_names == [
        "clean-photos-for-sharing",
        "review-photo-privacy",
    ]


def test_server_applies_remote_transport_settings() -> None:
    config = ServerConfig(
        transport="streamable-http",
        host="0.0.0.0",
        port=9100,
        streamable_http_path="/remote-mcp",
        json_response=True,
        stateless_http=True,
    )
    server = create_server(config)

    assert server.settings.host == "0.0.0.0"
    assert server.settings.port == 9100
    assert server.settings.streamable_http_path == "/remote-mcp"
    assert server.settings.json_response is True
    assert server.settings.stateless_http is True


def test_mutating_tool_wrappers_expose_plain_dict_results() -> None:
    assert get_type_hints(strip_exif)["return"] == dict[str, Any]
    assert get_type_hints(strip_selected_exif_fields)["return"] == dict[str, Any]
    assert get_type_hints(batch_strip_exif)["return"] == dict[str, Any]
    assert get_type_hints(batch_strip_gps_exif)["return"] == dict[str, Any]
    assert get_type_hints(batch_strip_selected_exif_fields)["return"] == dict[str, Any]


def test_parse_args_supports_remote_transport_flags() -> None:
    config = parse_args(
        [
            "--transport",
            "sse",
            "--host",
            "0.0.0.0",
            "--port",
            "9200",
            "--mount-path",
            "/github",
            "--sse-path",
            "/events",
            "--message-path",
            "/messages/",
        ]
    )

    assert config == ServerConfig(
        transport="sse",
        host="0.0.0.0",
        port=9200,
        mount_path="/github",
        sse_path="/events",
        message_path="/messages/",
        streamable_http_path="/mcp",
        debug=False,
        log_level="INFO",
        json_response=False,
        stateless_http=False,
    )


def test_config_from_env_supports_streamable_http(monkeypatch) -> None:
    monkeypatch.setenv("EXIF_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("EXIF_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("EXIF_MCP_PORT", "9300")
    monkeypatch.setenv("EXIF_MCP_STREAMABLE_HTTP_PATH", "/http-mcp")
    monkeypatch.setenv("EXIF_MCP_JSON_RESPONSE", "true")

    assert config_from_env() == ServerConfig(
        transport="streamable-http",
        host="0.0.0.0",
        port=9300,
        mount_path="/",
        sse_path="/sse",
        message_path="/messages/",
        streamable_http_path="/http-mcp",
        debug=False,
        log_level="INFO",
        json_response=True,
        stateless_http=False,
    )
