"""Domain-specific errors for EXIF validation and file mutation flows."""

from __future__ import annotations


class ExifMcpServerError(Exception):
    """Base class for domain errors surfaced by the shared EXIF core."""


class InvalidPathError(ExifMcpServerError):
    """Raised when a provided file system path is malformed or unsafe."""


class FileNotFoundErrorMapped(ExifMcpServerError):
    """Raised when a requested file or folder does not exist."""


class UnsupportedImageTypeError(ExifMcpServerError):
    """Raised when a file extension is outside the supported EXIF scope."""


class ExifReadError(ExifMcpServerError):
    """Raised when EXIF metadata cannot be read safely."""


class ExifWriteError(ExifMcpServerError):
    """Raised when a cleaned image cannot be written."""


class UnsafeOverwriteError(ExifMcpServerError):
    """Raised when a write would overwrite a file without explicit approval."""


class InvalidMetadataSelectionError(ExifMcpServerError):
    """Raised when metadata field-selection arguments are empty or invalid."""
