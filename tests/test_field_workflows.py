from __future__ import annotations

from pathlib import Path

import pytest

from exif_mcp_server.tools.batch import batch_strip_selected_exif_fields
from exif_mcp_server.tools.clean import strip_selected_exif_fields
from exif_mcp_server.tools.inspect import (
    find_images_with_exif_fields,
    inspect_exif,
    inspect_exif_detailed,
)
from tests.error_helpers import parse_tool_error

piexif = pytest.importorskip("piexif")
PIL = pytest.importorskip("PIL.Image")


def _write_jpeg(path: Path, exif_dict: dict[str, object] | None = None) -> Path:
    image = PIL.new("RGB", (12, 12), color="white")
    save_kwargs: dict[str, object] = {}
    if exif_dict is not None:
        save_kwargs["exif"] = piexif.dump(exif_dict)
    image.save(path, format="JPEG", **save_kwargs)
    return path


def test_inspect_exif_detailed_includes_tag_references(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "author.jpg",
        exif_dict={"0th": {piexif.ImageIFD.Artist: "Blue J.", piexif.ImageIFD.Make: "Canon"}},
    )

    result = inspect_exif_detailed(str(image_path))

    assert result["image_path"] == str(image_path.resolve())
    assert result["has_exif"] is True
    assert result["exif"]["Artist"] == "Blue J."
    assert result["exif"]["Make"] == "Canon"
    tag_map = {entry["field_key"]: entry for entry in result["tags"]}
    assert tag_map["Artist"]["ifd"] == "0th"
    assert tag_map["Artist"]["field_name"] == "Artist"
    assert tag_map["Artist"]["value"] == "Blue J."


def test_find_images_with_exif_fields_matches_author_fields(tmp_path: Path) -> None:
    folder = tmp_path / "photos"
    folder.mkdir()
    _write_jpeg(folder / "author.jpg", exif_dict={"0th": {piexif.ImageIFD.Artist: "Blue J."}})
    _write_jpeg(folder / "camera.jpg", exif_dict={"0th": {piexif.ImageIFD.Make: "Canon"}})
    (folder / "skip.bmp").write_bytes(b"not-a-bmp")

    result = find_images_with_exif_fields(
        str(folder),
        field_names=["Artist", "XPAuthor", "Copyright"],
    )

    assert result == {
        "folder_path": str(folder.resolve()),
        "requested_fields": ["Artist", "XPAuthor", "Copyright"],
        "match_mode": "any",
        "scanned_count": 2,
        "matched_count": 1,
        "failed_count": 0,
        "skipped_count": 1,
        "matches": [
            {
                "image_path": str((folder / "author.jpg").resolve()),
                "matched_fields": ["Artist"],
            }
        ],
        "failures": [],
    }


def test_strip_selected_exif_fields_validates_input(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "photo.jpg",
        exif_dict={"0th": {piexif.ImageIFD.Artist: "Blue J."}},
    )

    with pytest.raises(ValueError) as exc_info:
        strip_selected_exif_fields(str(image_path), field_names=[" ", ""])

    assert parse_tool_error(exc_info.value) == {
        "tool": "strip_selected_exif_fields",
        "code": "invalid_metadata_selection",
        "message": "At least one non-empty EXIF field name is required.",
    }


def test_batch_strip_selected_exif_fields_cleans_author_tags_to_output_folder(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    output = tmp_path / "cleaned"
    source.mkdir()
    image_path = _write_jpeg(
        source / "author.jpg",
        exif_dict={
            "0th": {
                piexif.ImageIFD.Artist: "Blue J.",
                piexif.ImageIFD.Make: "Canon",
            }
        },
    )

    result = batch_strip_selected_exif_fields(
        str(source),
        field_names=["Artist", "XPAuthor", "Copyright"],
        output_folder=str(output),
        include_comparison=True,
    )

    cleaned_path = output / "author.cleaned.jpg"
    assert result == {
        "folder_path": str(source.resolve()),
        "requested_fields": ["Artist", "XPAuthor", "Copyright"],
        "processed_count": 1,
        "success_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
        "results": [
            {
                "source_path": str(image_path.resolve()),
                "output_path": str(cleaned_path.resolve()),
                "status": "success",
                "message": "Selected EXIF fields removed.",
                "removed_fields": ["Artist"],
                "removed_tag_count": 1,
                "comparison": {
                    "before_has_exif": True,
                    "after_has_exif": True,
                    "removed_fields": ["Artist"],
                    "remaining_fields": ["Make"],
                },
            }
        ],
    }
    cleaned_exif = inspect_exif(str(cleaned_path))["exif"]
    assert cleaned_exif == {"Make": "Canon"}
    assert inspect_exif(str(image_path))["exif"]["Artist"] == "Blue J."
