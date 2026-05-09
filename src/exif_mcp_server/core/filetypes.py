"""Path and file-type helpers for the shared EXIF core."""

from __future__ import annotations

from pathlib import Path

from .errors import FileNotFoundErrorMapped, InvalidPathError, UnsupportedImageTypeError

SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")


def normalize_path(path_value: str) -> Path:
    """Expand user input into a normalized absolute path."""

    if not path_value or not path_value.strip():
        raise InvalidPathError("A non-empty path is required.")
    return Path(path_value).expanduser().resolve()


def validate_image_path(image_path: str) -> Path:
    """Validate a single supported image path for read-only operations."""

    path = normalize_path(image_path)
    if not path.exists():
        raise FileNotFoundErrorMapped(f"Image file does not exist: {path}")
    if not path.is_file():
        raise InvalidPathError(f"Expected a file path, received: {path}")
    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise UnsupportedImageTypeError(
            f"Unsupported image type for v1 EXIF support: {path.suffix or '<none>'}"
        )
    return path


def validate_folder_path(folder_path: str) -> Path:
    """Validate a folder path for batch operations."""

    path = normalize_path(folder_path)
    if not path.exists():
        raise FileNotFoundErrorMapped(f"Folder does not exist: {path}")
    if not path.is_dir():
        raise InvalidPathError(f"Expected a folder path, received: {path}")
    return path
