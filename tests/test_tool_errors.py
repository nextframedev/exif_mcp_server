from __future__ import annotations

from pathlib import Path

import pytest

from exif_mcp_server.tools.batch import batch_strip_exif
from exif_mcp_server.tools.privacy import summarize_exif_privacy
from tests.error_helpers import parse_tool_error


def test_batch_strip_exif_returns_structured_invalid_path_error(tmp_path: Path) -> None:
    missing_folder = tmp_path / "missing-folder"

    with pytest.raises(ValueError) as exc_info:
        batch_strip_exif(str(missing_folder))

    assert parse_tool_error(exc_info.value) == {
        "tool": "batch_strip_exif",
        "code": "file_not_found",
        "message": f"Folder does not exist: {missing_folder.resolve()}",
    }


def test_summarize_exif_privacy_returns_structured_invalid_type_error(tmp_path: Path) -> None:
    image_path = tmp_path / "photo.txt"
    image_path.write_text("not an image")

    with pytest.raises(ValueError) as exc_info:
        summarize_exif_privacy(str(image_path))

    assert parse_tool_error(exc_info.value) == {
        "tool": "summarize_exif_privacy",
        "code": "unsupported_image_type",
        "message": "Unsupported image type for v1 EXIF support: .txt",
    }
