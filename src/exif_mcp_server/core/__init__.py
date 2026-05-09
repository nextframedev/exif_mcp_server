"""Shared EXIF core interfaces for the MCP adapter and future web integration."""

from .errors import (
    ExifMcpServerError,
    ExifReadError,
    ExifWriteError,
    FileNotFoundErrorMapped,
    InvalidMetadataSelectionError,
    InvalidPathError,
    UnsafeOverwriteError,
    UnsupportedImageTypeError,
)
from .exif_cleaner import (
    batch_strip_exif_fields_in_folder,
    batch_strip_exif_in_folder,
    batch_strip_gps_exif_in_folder,
    strip_exif_fields_from_file,
    strip_exif_from_file,
    strip_gps_exif_from_file,
    strip_selected_metadata,
)
from .exif_reader import (
    detect_gps_exif,
    extract_grouped_metadata,
    find_images_with_exif_fields_in_folder,
    find_images_with_gps_exif_in_folder,
    read_exif,
    read_exif_detailed,
    summarize_exif_privacy,
)

__all__ = [
    "ExifMcpServerError",
    "ExifReadError",
    "ExifWriteError",
    "FileNotFoundErrorMapped",
    "InvalidMetadataSelectionError",
    "InvalidPathError",
    "UnsafeOverwriteError",
    "UnsupportedImageTypeError",
    "batch_strip_exif_fields_in_folder",
    "batch_strip_exif_in_folder",
    "batch_strip_gps_exif_in_folder",
    "detect_gps_exif",
    "extract_grouped_metadata",
    "find_images_with_exif_fields_in_folder",
    "find_images_with_gps_exif_in_folder",
    "read_exif",
    "read_exif_detailed",
    "strip_exif_fields_from_file",
    "strip_exif_from_file",
    "strip_gps_exif_from_file",
    "strip_selected_metadata",
    "summarize_exif_privacy",
]
