"""Read-only MCP tools for EXIF inspection and GPS detection."""

from __future__ import annotations

from typing import Any

from ..core.exif_reader import (
    detect_gps_exif,
    find_images_with_exif_fields_in_folder,
    find_images_with_gps_exif_in_folder,
    read_exif,
    read_exif_detailed,
)
from ..core.models import (
    FindImagesWithExifFieldsResult,
    FindImagesWithGpsExifResult,
    HasGpsExifResult,
    InspectExifDetailedResult,
    InspectExifResult,
)
from ._errors import run_with_mcp_error_handling


def inspect_exif(image_path: str) -> InspectExifResult:
    """Read EXIF metadata from a single image path.

    This tool is read-only and must not modify the target file.
    """

    return run_with_mcp_error_handling(
        "inspect_exif",
        lambda: read_exif(image_path=image_path),
    )


def has_gps_exif(image_path: str) -> HasGpsExifResult:
    """Check whether an image contains GPS/location EXIF fields.

    This tool is read-only and must not modify the target file.
    """

    return run_with_mcp_error_handling(
        "has_gps_exif",
        lambda: detect_gps_exif(image_path=image_path),
    )


def inspect_exif_detailed(image_path: str) -> InspectExifDetailedResult:
    """Read EXIF metadata with per-tag references for selective cleanup."""

    return run_with_mcp_error_handling(
        "inspect_exif_detailed",
        lambda: read_exif_detailed(image_path=image_path),
    )


def find_images_with_gps_exif(
    folder_path: str,
    recursive: bool = False,
    extensions: list[str] | None = None,
) -> FindImagesWithGpsExifResult:
    """Find images in one folder that contain GPS/location EXIF fields."""

    return run_with_mcp_error_handling(
        "find_images_with_gps_exif",
        lambda: find_images_with_gps_exif_in_folder(
            folder_path=folder_path,
            recursive=recursive,
            extensions=extensions,
        ),
    )


def find_images_with_exif_fields(
    folder_path: str,
    field_names: list[str],
    match_mode: str = "any",
    recursive: bool = False,
    extensions: list[str] | None = None,
) -> FindImagesWithExifFieldsResult:
    """Find images in one folder containing selected EXIF fields."""

    return run_with_mcp_error_handling(
        "find_images_with_exif_fields",
        lambda: find_images_with_exif_fields_in_folder(
            folder_path=folder_path,
            field_names=field_names,
            match_mode=match_mode,
            recursive=recursive,
            extensions=extensions,
        ),
    )


def register_inspection_tools(server: Any) -> None:
    """Register inspection tools on the provided MCP server instance."""

    server.tool()(inspect_exif)
    server.tool()(has_gps_exif)
    server.tool()(inspect_exif_detailed)
    server.tool()(find_images_with_gps_exif)
    server.tool()(find_images_with_exif_fields)
