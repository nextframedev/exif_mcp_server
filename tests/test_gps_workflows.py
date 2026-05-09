from __future__ import annotations

from pathlib import Path

import pytest

from exif_mcp_server.tools.batch import batch_strip_gps_exif
from exif_mcp_server.tools.inspect import find_images_with_gps_exif, has_gps_exif, inspect_exif
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


def test_find_images_with_gps_exif_returns_only_matches(tmp_path: Path) -> None:
    folder = tmp_path / "photos"
    folder.mkdir()
    gps_image = _write_jpeg(
        folder / "gps.jpg",
        exif_dict={
            "0th": {piexif.ImageIFD.Make: "Apple"},
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((49, 1), (16, 1), (0, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((123, 1), (7, 1), (0, 1)),
            },
        },
    )
    _write_jpeg(
        folder / "no-gps.jpg",
        exif_dict={"0th": {piexif.ImageIFD.Make: "Canon"}},
    )
    (folder / "ignore.bmp").write_bytes(b"not-a-bmp")

    result = find_images_with_gps_exif(str(folder))

    assert result == {
        "folder_path": str(folder.resolve()),
        "scanned_count": 2,
        "matched_count": 1,
        "failed_count": 0,
        "skipped_count": 1,
        "matches": [
            {
                "image_path": str(gps_image.resolve()),
                "gps_fields_present": [
                    "GPSLatitude",
                    "GPSLatitudeRef",
                    "GPSLongitude",
                    "GPSLongitudeRef",
                ],
            }
        ],
        "failures": [],
    }


def test_find_images_with_gps_exif_reports_folder_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError) as exc_info:
        find_images_with_gps_exif(str(tmp_path / "missing"))

    assert parse_tool_error(exc_info.value) == {
        "tool": "find_images_with_gps_exif",
        "code": "file_not_found",
        "message": f"Folder does not exist: {(tmp_path / 'missing').resolve()}",
    }


def test_batch_strip_gps_exif_removes_only_gps_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "cleaned"
    source.mkdir()
    gps_image = _write_jpeg(
        source / "gps.jpg",
        exif_dict={
            "0th": {
                piexif.ImageIFD.Make: "Apple",
                piexif.ImageIFD.Model: "iPhone 14",
            },
            "Exif": {piexif.ExifIFD.DateTimeOriginal: "2026:04:16 10:30:00"},
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((49, 1), (16, 1), (0, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((123, 1), (7, 1), (0, 1)),
            },
        },
    )

    result = batch_strip_gps_exif(
        str(source),
        output_folder=str(output),
        include_comparison=True,
    )

    cleaned_path = output / "gps.cleaned.jpg"
    assert result == {
        "folder_path": str(source.resolve()),
        "processed_count": 1,
        "success_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
        "results": [
            {
                "source_path": str(gps_image.resolve()),
                "output_path": str(cleaned_path.resolve()),
                "status": "success",
                "message": "GPS EXIF removed.",
                "removed_gps": True,
                "comparison": {
                    "before_has_exif": True,
                    "after_has_exif": True,
                    "removed_fields": [
                        "GPSLatitude",
                        "GPSLatitudeRef",
                        "GPSLongitude",
                        "GPSLongitudeRef",
                        "GPSTag",
                    ],
                    "remaining_fields": ["DateTimeOriginal", "ExifTag", "Make", "Model"],
                },
            }
        ],
    }
    assert has_gps_exif(str(cleaned_path)) == {
        "image_path": str(cleaned_path.resolve()),
        "has_gps": False,
        "gps_fields_present": [],
    }
    cleaned_exif = inspect_exif(str(cleaned_path))["exif"]
    assert cleaned_exif["Make"] == "Apple"
    assert cleaned_exif["Model"] == "iPhone 14"
    assert cleaned_exif["DateTimeOriginal"] == "2026:04:16 10:30:00"
    assert "GPSLatitude" not in cleaned_exif
    assert "GPSLongitude" not in cleaned_exif


def test_batch_strip_gps_exif_reports_no_gps_but_writes_clean_copy(tmp_path: Path) -> None:
    folder = tmp_path / "photos"
    folder.mkdir()
    image_path = _write_jpeg(
        folder / "plain.jpg",
        exif_dict={"0th": {piexif.ImageIFD.Make: "Canon"}},
    )

    result = batch_strip_gps_exif(str(folder))

    cleaned_path = folder / "plain.cleaned.jpg"
    assert result["results"] == [
        {
            "source_path": str(image_path.resolve()),
            "output_path": str(cleaned_path.resolve()),
            "status": "success",
            "message": "No GPS EXIF found; wrote clean copy.",
            "removed_gps": False,
        }
    ]
    assert inspect_exif(str(cleaned_path))["exif"]["Make"] == "Canon"


def test_batch_strip_gps_exif_supports_png(tmp_path: Path) -> None:
    folder = tmp_path / "photos"
    folder.mkdir()
    image = PIL.new("RGBA", (12, 12), color=(255, 255, 255, 128))
    image.save(
        folder / "gps.png",
        format="PNG",
        exif=piexif.dump(
            {
                "0th": {piexif.ImageIFD.Make: "Google"},
                "GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N"},
            }
        ),
    )

    result = batch_strip_gps_exif(str(folder))

    cleaned_path = folder / "gps.cleaned.png"
    assert result["results"] == [
        {
            "source_path": str((folder / "gps.png").resolve()),
            "output_path": str(cleaned_path.resolve()),
            "status": "success",
            "message": "GPS EXIF removed.",
            "removed_gps": True,
        }
    ]
    assert has_gps_exif(str(cleaned_path))["has_gps"] is False
    assert inspect_exif(str(cleaned_path))["exif"]["Make"] == "Google"
