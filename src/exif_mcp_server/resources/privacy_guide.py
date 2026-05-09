"""Static MCP resources for EXIF guidance."""

from __future__ import annotations

from typing import Any

PRIVACY_GUIDE = """
EXIF metadata can reveal where and when a photo was taken, which device created
it, and which software last edited it.

Privacy-sensitive EXIF fields commonly include:
- GPS coordinates and related location tags
- device make and model
- capture timestamps
- software/editor tags
- serial-like identifiers

This server can inspect EXIF, check GPS fields, summarize privacy risk, remove
EXIF from one JPG/JPEG/PNG/WebP/TIFF image, and batch-clean folders of
JPG/JPEG/PNG/WebP/TIFF images.

What the server removes:
- EXIF metadata when you call `strip_exif`
- EXIF metadata across supported images when you call `batch_strip_exif`

What the server does not do:
- change image pixels intentionally beyond re-saving needed to remove EXIF
- edit IPTC or XMP metadata
- support cloud uploads or remote storage
""".strip()

SUPPORTED_FORMATS = """
Supported image formats in the current MCP server release:
- .jpg
- .jpeg
- .png
- .webp
- .tif
- .tiff

Safety defaults:
- read-only tools do not modify files
- `strip_exif` creates a sibling `*.cleaned.<ext>` file by default
- existing outputs are not overwritten unless `overwrite=true`
- `batch_strip_exif` continues on file-level failures and returns per-file results

Caveats:
- the server intentionally does not claim IPTC or XMP support
- stdio remains the default transport, but optional `streamable-http` and `sse`
  transports are now available
""".strip()


def register_resources(server: Any) -> None:
    """Register static EXIF guidance resources on the provided MCP server."""

    @server.resource(
        "exif://privacy-guide",
        name="privacy-guide",
        title="EXIF Privacy Guide",
        description="Short practical guidance on EXIF privacy risks and server behavior.",
        mime_type="text/markdown",
    )
    def get_privacy_guide() -> str:
        return PRIVACY_GUIDE

    @server.resource(
        "exif://supported-formats",
        name="supported-formats",
        title="Supported Formats",
        description="Current image format support and safety defaults for the EXIF MCP server.",
        mime_type="text/markdown",
    )
    def get_supported_formats() -> str:
        return SUPPORTED_FORMATS
