"""Mutating MCP tool wrapper for folder-level EXIF cleanup."""

from __future__ import annotations

from typing import Any

from ..core.exif_cleaner import (
    batch_strip_exif_fields_in_folder,
    batch_strip_exif_in_folder,
    batch_strip_gps_exif_in_folder,
)
from ..core.models import (
    BatchStripExifResult,
    BatchStripGpsExifResult,
    BatchStripSelectedExifResult,
)
from ._errors import run_with_mcp_error_handling


def batch_strip_exif(
    folder_path: str,
    output_folder: str | None = None,
    recursive: bool = False,
    overwrite: bool = False,
    extensions: list[str] | None = None,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> BatchStripExifResult:
    """Remove EXIF metadata from supported images in a folder.

    Optional dry-run, comparison, and per-file sidecar-report behavior is available.
    """

    return run_with_mcp_error_handling(
        "batch_strip_exif",
        lambda: batch_strip_exif_in_folder(
            folder_path=folder_path,
            output_folder=output_folder,
            recursive=recursive,
            overwrite=overwrite,
            extensions=extensions,
            dry_run=dry_run,
            include_comparison=include_comparison,
            write_report=write_report,
        ),
    )


def batch_strip_gps_exif(
    folder_path: str,
    output_folder: str | None = None,
    recursive: bool = False,
    overwrite: bool = False,
    extensions: list[str] | None = None,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> BatchStripGpsExifResult:
    """Remove only GPS EXIF metadata from supported images in a folder."""

    return run_with_mcp_error_handling(
        "batch_strip_gps_exif",
        lambda: batch_strip_gps_exif_in_folder(
            folder_path=folder_path,
            output_folder=output_folder,
            recursive=recursive,
            overwrite=overwrite,
            extensions=extensions,
            dry_run=dry_run,
            include_comparison=include_comparison,
            write_report=write_report,
        ),
    )


def batch_strip_selected_exif_fields(
    folder_path: str,
    field_names: list[str],
    output_folder: str | None = None,
    recursive: bool = False,
    overwrite: bool = False,
    extensions: list[str] | None = None,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> BatchStripSelectedExifResult:
    """Remove selected EXIF fields from supported images in a folder."""

    return run_with_mcp_error_handling(
        "batch_strip_selected_exif_fields",
        lambda: batch_strip_exif_fields_in_folder(
            folder_path=folder_path,
            field_names=field_names,
            output_folder=output_folder,
            recursive=recursive,
            overwrite=overwrite,
            extensions=extensions,
            dry_run=dry_run,
            include_comparison=include_comparison,
            write_report=write_report,
        ),
    )


def register_batch_tools(server: Any) -> None:
    """Register batch cleanup tools on the provided MCP server instance."""

    server.tool()(batch_strip_exif)
    server.tool()(batch_strip_gps_exif)
    server.tool()(batch_strip_selected_exif_fields)
