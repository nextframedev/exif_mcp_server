from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from exif_mcp_server.tools.inspect import has_gps_exif, inspect_exif
from tests.error_helpers import parse_tool_error

piexif = pytest.importorskip("piexif")
PIL = pytest.importorskip("PIL.Image")


def test_inspection_symbols_exist() -> None:
    assert inspect_exif.__name__ == "inspect_exif"
    assert has_gps_exif.__name__ == "has_gps_exif"


def _write_jpeg(path: Path, exif_dict: dict[str, object] | None = None) -> Path:
    image = PIL.new("RGB", (12, 12), color="white")
    save_kwargs: dict[str, object] = {}
    if exif_dict is not None:
        save_kwargs["exif"] = piexif.dump(exif_dict)
    image.save(path, format="JPEG", **save_kwargs)
    return path


def _write_tiff(path: Path, exif_dict: dict[str, object] | None = None) -> Path:
    image = PIL.new("RGB", (12, 12), color="white")
    save_kwargs: dict[str, object] = {}
    if exif_dict is not None:
        save_kwargs["exif"] = piexif.dump(exif_dict)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"Corrupt EXIF data\..*",
            module=r"PIL\.TiffImagePlugin",
        )
        image.save(path, format="TIFF", **save_kwargs)
    return path


def _write_png(path: Path, exif_dict: dict[str, object] | None = None) -> Path:
    image = PIL.new("RGBA", (12, 12), color=(255, 255, 255, 128))
    save_kwargs: dict[str, object] = {}
    if exif_dict is not None:
        save_kwargs["exif"] = piexif.dump(exif_dict)
    image.save(path, format="PNG", **save_kwargs)
    return path


def _write_webp(path: Path, exif_dict: dict[str, object] | None = None) -> Path:
    image = PIL.new("RGBA", (12, 12), color=(255, 255, 255, 128))
    save_kwargs: dict[str, object] = {}
    if exif_dict is not None:
        save_kwargs["exif"] = piexif.dump(exif_dict)
    image.save(path, format="WEBP", **save_kwargs)
    return path


def test_inspect_exif_contract_shape(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "with-exif.jpg",
        exif_dict={
            "0th": {
                piexif.ImageIFD.Make: "Apple",
                piexif.ImageIFD.Model: "iPhone 14",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2026:04:16 10:30:00",
            },
        },
    )

    result = inspect_exif(str(image_path))

    assert result["image_path"] == str(image_path.resolve())
    assert result["has_exif"] is True
    assert result["exif"]["Make"] == "Apple"
    assert result["exif"]["Model"] == "iPhone 14"
    assert result["exif"]["DateTimeOriginal"] == "2026:04:16 10:30:00"
    assert result["warnings"] == []


def test_inspect_exif_returns_empty_mapping_when_exif_absent(tmp_path: Path) -> None:
    image_path = _write_jpeg(tmp_path / "without-exif.jpg")

    result = inspect_exif(str(image_path))

    assert result == {
        "image_path": str(image_path.resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }


def test_has_gps_exif_reports_gps_fields(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "with-gps.jpg",
        exif_dict={
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((49, 1), (16, 1), (0, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((123, 1), (7, 1), (0, 1)),
            },
        },
    )

    result = has_gps_exif(str(image_path))

    assert result["image_path"] == str(image_path.resolve())
    assert result["has_gps"] is True
    assert result["gps_fields_present"] == [
        "GPSLatitude",
        "GPSLatitudeRef",
        "GPSLongitude",
        "GPSLongitudeRef",
    ]


def test_has_gps_exif_returns_false_when_gps_absent(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "without-gps.jpg",
        exif_dict={
            "0th": {piexif.ImageIFD.Make: "Canon"},
        },
    )

    result = has_gps_exif(str(image_path))

    assert result == {
        "image_path": str(image_path.resolve()),
        "has_gps": False,
        "gps_fields_present": [],
    }


def test_inspect_exif_supports_tiff(tmp_path: Path) -> None:
    image_path = _write_tiff(
        tmp_path / "with-exif.tiff",
        exif_dict={
            "0th": {
                piexif.ImageIFD.Make: "Canon",
                piexif.ImageIFD.Model: "EOS R6",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2026:04:16 12:15:00",
            },
        },
    )

    result = inspect_exif(str(image_path))

    assert result["image_path"] == str(image_path.resolve())
    assert result["has_exif"] is True
    assert result["exif"]["Make"] == "Canon"
    assert result["exif"]["Model"] == "EOS R6"
    assert result["exif"]["DateTimeOriginal"] == "2026:04:16 12:15:00"


def test_has_gps_exif_supports_tiff(tmp_path: Path) -> None:
    image_path = _write_tiff(
        tmp_path / "with-gps.tif",
        exif_dict={
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((49, 1), (16, 1), (0, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((123, 1), (7, 1), (0, 1)),
            },
        },
    )

    result = has_gps_exif(str(image_path))

    assert result["image_path"] == str(image_path.resolve())
    assert result["has_gps"] is True
    assert result["gps_fields_present"] == [
        "GPSLatitude",
        "GPSLatitudeRef",
        "GPSLongitude",
        "GPSLongitudeRef",
    ]


def test_inspect_exif_supports_png(tmp_path: Path) -> None:
    image_path = _write_png(
        tmp_path / "with-exif.png",
        exif_dict={
            "0th": {
                piexif.ImageIFD.Make: "Google",
                piexif.ImageIFD.Model: "Pixel 9",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2026:04:16 14:20:00",
            },
        },
    )

    result = inspect_exif(str(image_path))

    assert result["image_path"] == str(image_path.resolve())
    assert result["has_exif"] is True
    assert result["exif"]["Make"] == "Google"
    assert result["exif"]["Model"] == "Pixel 9"
    assert result["exif"]["DateTimeOriginal"] == "2026:04:16 14:20:00"


def test_has_gps_exif_supports_webp(tmp_path: Path) -> None:
    image_path = _write_webp(
        tmp_path / "with-gps.webp",
        exif_dict={
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((49, 1), (16, 1), (0, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((123, 1), (7, 1), (0, 1)),
            },
        },
    )

    result = has_gps_exif(str(image_path))

    assert result["image_path"] == str(image_path.resolve())
    assert result["has_gps"] is True
    assert result["gps_fields_present"] == [
        "GPSLatitude",
        "GPSLatitudeRef",
        "GPSLongitude",
        "GPSLongitudeRef",
    ]


def test_inspect_exif_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError) as exc_info:
        inspect_exif(str(tmp_path / "missing.jpg"))

    assert parse_tool_error(exc_info.value) == {
        "tool": "inspect_exif",
        "code": "file_not_found",
        "message": f"Image file does not exist: {(tmp_path / 'missing.jpg').resolve()}",
    }


def test_has_gps_exif_raises_for_unsupported_extension(tmp_path: Path) -> None:
    image_path = tmp_path / "photo.bmp"
    image_path.write_bytes(b"not-a-bmp")

    with pytest.raises(ValueError) as exc_info:
        has_gps_exif(str(image_path))

    assert parse_tool_error(exc_info.value) == {
        "tool": "has_gps_exif",
        "code": "unsupported_image_type",
        "message": "Unsupported image type for v1 EXIF support: .bmp",
    }
