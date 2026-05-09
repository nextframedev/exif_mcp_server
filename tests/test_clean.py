from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from exif_mcp_server.tools.clean import strip_exif
from exif_mcp_server.tools.inspect import inspect_exif
from tests.error_helpers import parse_tool_error

piexif = pytest.importorskip("piexif")
PIL = pytest.importorskip("PIL.Image")


def test_clean_symbol_exists() -> None:
    assert strip_exif.__name__ == "strip_exif"


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


def test_strip_exif_default_output_behavior(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "photo.jpg",
        exif_dict={
            "0th": {piexif.ImageIFD.Make: "Apple"},
            "Exif": {piexif.ExifIFD.DateTimeOriginal: "2026:04:16 10:30:00"},
        },
    )

    result = strip_exif(str(image_path))

    cleaned_path = image_path.with_name("photo.cleaned.jpg")
    assert result == {
        "source_path": str(image_path.resolve()),
        "output_path": str(cleaned_path.resolve()),
        "removed_exif": True,
        "notes": [
            "Created sibling cleaned file.",
            "Removed EXIF metadata from the written image.",
        ],
    }
    assert cleaned_path.exists()
    assert inspect_exif(str(image_path))["has_exif"] is True
    assert inspect_exif(str(cleaned_path)) == {
        "image_path": str(cleaned_path.resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }


def test_strip_exif_overwrite_true_rewrites_source(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "overwrite.jpg",
        exif_dict={"GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N"}},
    )

    result = strip_exif(str(image_path), overwrite=True)

    assert result == {
        "source_path": str(image_path.resolve()),
        "output_path": str(image_path.resolve()),
        "removed_exif": True,
        "notes": [
            "Overwrote the source image because overwrite=true.",
            "Removed EXIF metadata from the written image.",
        ],
    }
    assert inspect_exif(str(image_path)) == {
        "image_path": str(image_path.resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }


def test_strip_exif_rejects_existing_output_without_overwrite(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "source.jpg",
        exif_dict={"0th": {piexif.ImageIFD.Make: "Canon"}},
    )
    existing_output = _write_jpeg(tmp_path / "existing.jpg")

    with pytest.raises(ValueError) as exc_info:
        strip_exif(str(image_path), output_path=str(existing_output))

    assert parse_tool_error(exc_info.value) == {
        "tool": "strip_exif",
        "code": "unsafe_overwrite",
        "message": (
            "Refusing to overwrite existing output file without overwrite=true: "
            f"{existing_output.resolve()}"
        ),
    }


def test_strip_exif_rejects_existing_default_sibling_without_overwrite(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "source.jpg",
        exif_dict={"0th": {piexif.ImageIFD.Make: "Canon"}},
    )
    _write_jpeg(tmp_path / "source.cleaned.jpg")

    with pytest.raises(ValueError) as exc_info:
        strip_exif(str(image_path))

    assert parse_tool_error(exc_info.value) == {
        "tool": "strip_exif",
        "code": "unsafe_overwrite",
        "message": (
            "Refusing to overwrite existing output file without overwrite=true: "
            f"{(tmp_path / 'source.cleaned.jpg').resolve()}"
        ),
    }


def test_strip_exif_reports_when_source_has_no_exif(tmp_path: Path) -> None:
    image_path = _write_jpeg(tmp_path / "no-exif.jpg")

    result = strip_exif(str(image_path))

    cleaned_path = image_path.with_name("no-exif.cleaned.jpg")
    assert result == {
        "source_path": str(image_path.resolve()),
        "output_path": str(cleaned_path.resolve()),
        "removed_exif": False,
        "notes": [
            "Created sibling cleaned file.",
            "Source image did not contain EXIF metadata.",
        ],
    }
    assert inspect_exif(str(cleaned_path)) == {
        "image_path": str(cleaned_path.resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }


def test_strip_exif_dry_run_with_comparison_does_not_write_files(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "dry-run.jpg",
        exif_dict={"GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N"}},
    )

    result = strip_exif(
        str(image_path),
        dry_run=True,
        include_comparison=True,
        write_report=True,
    )

    cleaned_path = image_path.with_name("dry-run.cleaned.jpg")
    assert result == {
        "source_path": str(image_path.resolve()),
        "output_path": str(cleaned_path.resolve()),
        "removed_exif": True,
        "dry_run": True,
        "comparison": {
            "before_has_exif": True,
            "after_has_exif": False,
            "removed_fields": ["GPSLatitudeRef", "GPSTag"],
            "remaining_fields": [],
        },
        "notes": [
            "Created sibling cleaned file.",
            "Dry run only; no files were written.",
            "Dry run would remove EXIF metadata from the output image.",
            "Dry run skipped writing the sidecar JSON report.",
        ],
    }
    assert cleaned_path.exists() is False
    assert (tmp_path / "dry-run.cleaned.exif-report.json").exists() is False


def test_strip_exif_writes_sidecar_report_with_comparison(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "report.jpg",
        exif_dict={
            "0th": {piexif.ImageIFD.Make: "Apple"},
            "Exif": {piexif.ExifIFD.DateTimeOriginal: "2026:04:16 10:30:00"},
        },
    )

    result = strip_exif(
        str(image_path),
        include_comparison=True,
        write_report=True,
    )

    cleaned_path = image_path.with_name("report.cleaned.jpg")
    report_path = tmp_path / "report.cleaned.exif-report.json"
    assert result["output_path"] == str(cleaned_path.resolve())
    assert result["report_path"] == str(report_path.resolve())
    assert result["comparison"] == {
        "before_has_exif": True,
        "after_has_exif": False,
        "removed_fields": ["DateTimeOriginal", "ExifTag", "Make"],
        "remaining_fields": [],
    }
    assert result["notes"] == [
        "Created sibling cleaned file.",
        "Removed EXIF metadata from the written image.",
        "Wrote sidecar JSON report.",
    ]
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_payload == {
        "comparison": {
            "after_has_exif": False,
            "before_has_exif": True,
            "remaining_fields": [],
            "removed_fields": ["DateTimeOriginal", "ExifTag", "Make"],
        },
        "dry_run": False,
        "notes": [
            "Created sibling cleaned file.",
            "Removed EXIF metadata from the written image.",
        ],
        "output_path": str(cleaned_path.resolve()),
        "removed_exif": True,
        "source_path": str(image_path.resolve()),
    }


def test_strip_exif_supports_tiff(tmp_path: Path) -> None:
    image_path = _write_tiff(
        tmp_path / "photo.tiff",
        exif_dict={
            "0th": {piexif.ImageIFD.Make: "Canon"},
            "Exif": {piexif.ExifIFD.DateTimeOriginal: "2026:04:16 10:30:00"},
        },
    )

    result = strip_exif(str(image_path), include_comparison=True)

    cleaned_path = image_path.with_name("photo.cleaned.tiff")
    assert result["source_path"] == str(image_path.resolve())
    assert result["output_path"] == str(cleaned_path.resolve())
    assert result["removed_exif"] is True
    assert result["comparison"] == {
        "before_has_exif": True,
        "after_has_exif": False,
        "removed_fields": ["DateTimeOriginal", "ExifTag", "Make"],
        "remaining_fields": [],
    }
    assert inspect_exif(str(cleaned_path)) == {
        "image_path": str(cleaned_path.resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }


def test_strip_exif_supports_png(tmp_path: Path) -> None:
    image_path = _write_png(
        tmp_path / "photo.png",
        exif_dict={
            "0th": {piexif.ImageIFD.Make: "Google"},
            "Exif": {piexif.ExifIFD.DateTimeOriginal: "2026:04:16 10:30:00"},
        },
    )

    result = strip_exif(str(image_path), include_comparison=True)

    cleaned_path = image_path.with_name("photo.cleaned.png")
    assert result["source_path"] == str(image_path.resolve())
    assert result["output_path"] == str(cleaned_path.resolve())
    assert result["removed_exif"] is True
    assert result["comparison"] == {
        "before_has_exif": True,
        "after_has_exif": False,
        "removed_fields": ["DateTimeOriginal", "ExifTag", "Make"],
        "remaining_fields": [],
    }
    assert inspect_exif(str(cleaned_path)) == {
        "image_path": str(cleaned_path.resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }


def test_strip_exif_supports_webp(tmp_path: Path) -> None:
    image_path = _write_webp(
        tmp_path / "photo.webp",
        exif_dict={
            "GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N"},
        },
    )

    result = strip_exif(str(image_path))

    cleaned_path = image_path.with_name("photo.cleaned.webp")
    assert result["source_path"] == str(image_path.resolve())
    assert result["output_path"] == str(cleaned_path.resolve())
    assert result["removed_exif"] is True
    assert inspect_exif(str(cleaned_path)) == {
        "image_path": str(cleaned_path.resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }
