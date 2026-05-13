"""Mutating MCP tool wrapper for single-file EXIF cleanup."""

from __future__ import annotations

from typing import Any, cast

from ..core.exif_cleaner import strip_exif_fields_from_file, strip_exif_from_file
from ._errors import run_with_mcp_error_handling


def strip_exif(
    image_path: str,
    output_path: str | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> dict[str, Any]:
    """Remove EXIF metadata from a single image.

    If `output_path` is omitted, the shared core will later generate a sibling
    cleaned file path. Overwrite remains opt-in and defaults to `False`.
    Optional dry-run, comparison, and sidecar-report behavior is available.
    """

    return run_with_mcp_error_handling(
        "strip_exif",
        lambda: cast(
            dict[str, Any],
            strip_exif_from_file(
                image_path=image_path,
                output_path=output_path,
                overwrite=overwrite,
                dry_run=dry_run,
                include_comparison=include_comparison,
                write_report=write_report,
            ),
        ),
    )


def strip_selected_exif_fields(
    image_path: str,
    field_names: list[str],
    output_path: str | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> dict[str, Any]:
    """Remove selected EXIF fields from a single image path."""

    return run_with_mcp_error_handling(
        "strip_selected_exif_fields",
        lambda: cast(
            dict[str, Any],
            strip_exif_fields_from_file(
                image_path=image_path,
                field_names=field_names,
                output_path=output_path,
                overwrite=overwrite,
                dry_run=dry_run,
                include_comparison=include_comparison,
                write_report=write_report,
            ),
        ),
    )


def register_clean_tools(server: Any) -> None:
    """Register single-file cleanup tools on the provided MCP server instance."""

    server.tool()(strip_exif)
    server.tool()(strip_selected_exif_fields)
