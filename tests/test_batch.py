from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from exif_mcp_server.tools.batch import batch_strip_exif
from exif_mcp_server.tools.inspect import inspect_exif

piexif = pytest.importorskip("piexif")
PIL = pytest.importorskip("PIL.Image")


def test_batch_symbol_exists() -> None:
    assert batch_strip_exif.__name__ == "batch_strip_exif"


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


def test_batch_strip_exif_mixed_outcomes(tmp_path: Path) -> None:
    folder = tmp_path / "photos"
    folder.mkdir()

    success_file = _write_jpeg(
        folder / "a.jpg",
        exif_dict={"0th": {piexif.ImageIFD.Make: "Apple"}},
    )
    failed_file = _write_jpeg(
        folder / "b.jpg",
        exif_dict={"Exif": {piexif.ExifIFD.DateTimeOriginal: "2026:04:16 10:30:00"}},
    )
    _write_jpeg(folder / "b.cleaned.jpg")
    (folder / "skip.bmp").write_bytes(b"not-a-bmp")

    result = batch_strip_exif(str(folder))

    assert result["folder_path"] == str(folder.resolve())
    assert result["processed_count"] == 3
    assert result["success_count"] == 1
    assert result["failed_count"] == 1
    assert result["skipped_count"] == 1

    results_by_path = {entry["source_path"]: entry for entry in result["results"]}

    assert results_by_path[str(success_file.resolve())] == {
        "source_path": str(success_file.resolve()),
        "output_path": str((folder / "a.cleaned.jpg").resolve()),
        "status": "success",
        "message": "EXIF removed.",
        "removed_exif": True,
    }
    assert results_by_path[str(failed_file.resolve())]["status"] == "failed"
    assert "Refusing to overwrite existing output file" in results_by_path[
        str(failed_file.resolve())
    ]["message"]
    assert results_by_path[str((folder / "skip.bmp").resolve())] == {
        "source_path": str((folder / "skip.bmp").resolve()),
        "status": "skipped",
        "message": "Skipped because the file extension is not selected for batch processing.",
    }
    assert inspect_exif(str(folder / "a.cleaned.jpg")) == {
        "image_path": str((folder / "a.cleaned.jpg").resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }


def test_batch_strip_exif_recursive_output_folder(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    nested = source_root / "nested" / "deeper"
    nested.mkdir(parents=True)
    image_path = _write_jpeg(
        nested / "photo.jpg",
        exif_dict={"GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N"}},
    )
    output_root = tmp_path / "cleaned"

    result = batch_strip_exif(
        str(source_root),
        output_folder=str(output_root),
        recursive=True,
    )

    expected_output = output_root / "nested" / "deeper" / "photo.cleaned.jpg"
    assert result == {
        "folder_path": str(source_root.resolve()),
        "processed_count": 1,
        "success_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
        "results": [
            {
                "source_path": str(image_path.resolve()),
                "output_path": str(expected_output.resolve()),
                "status": "success",
                "message": "EXIF removed.",
                "removed_exif": True,
            }
        ],
    }
    assert inspect_exif(str(expected_output)) == {
        "image_path": str(expected_output.resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }


def test_batch_strip_exif_dry_run_with_comparison(tmp_path: Path) -> None:
    folder = tmp_path / "dry-batch"
    folder.mkdir()
    image_path = _write_jpeg(
        folder / "photo.jpg",
        exif_dict={"GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N"}},
    )

    result = batch_strip_exif(
        str(folder),
        dry_run=True,
        include_comparison=True,
        write_report=True,
    )

    cleaned_path = folder / "photo.cleaned.jpg"
    assert result == {
        "folder_path": str(folder.resolve()),
        "processed_count": 1,
        "success_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
        "results": [
            {
                "source_path": str(image_path.resolve()),
                "output_path": str(cleaned_path.resolve()),
                "status": "success",
                "message": "Dry run completed; no files were written.",
                "removed_exif": True,
                "dry_run": True,
                "comparison": {
                    "before_has_exif": True,
                    "after_has_exif": False,
                    "removed_fields": ["GPSLatitudeRef", "GPSTag"],
                    "remaining_fields": [],
                },
            }
        ],
    }
    assert cleaned_path.exists() is False
    assert (folder / "photo.cleaned.exif-report.json").exists() is False


def test_batch_strip_exif_writes_per_file_sidecar_reports(tmp_path: Path) -> None:
    folder = tmp_path / "reports"
    folder.mkdir()
    image_path = _write_jpeg(
        folder / "photo.jpg",
        exif_dict={"0th": {piexif.ImageIFD.Make: "Canon"}},
    )

    result = batch_strip_exif(
        str(folder),
        include_comparison=True,
        write_report=True,
    )

    cleaned_path = folder / "photo.cleaned.jpg"
    report_path = folder / "photo.cleaned.exif-report.json"
    assert result["results"] == [
        {
            "source_path": str(image_path.resolve()),
            "output_path": str(cleaned_path.resolve()),
            "status": "success",
            "message": "EXIF removed.",
            "removed_exif": True,
            "comparison": {
                "before_has_exif": True,
                "after_has_exif": False,
                "removed_fields": ["Make"],
                "remaining_fields": [],
            },
            "report_path": str(report_path.resolve()),
        }
    ]
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_payload["output_path"] == str(cleaned_path.resolve())
    assert report_payload["source_path"] == str(image_path.resolve())
    assert report_payload["removed_exif"] is True


def test_batch_strip_exif_supports_tiff(tmp_path: Path) -> None:
    folder = tmp_path / "tiffs"
    folder.mkdir()
    image_path = _write_tiff(
        folder / "photo.tif",
        exif_dict={"GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N"}},
    )

    result = batch_strip_exif(str(folder))

    cleaned_path = folder / "photo.cleaned.tif"
    assert result == {
        "folder_path": str(folder.resolve()),
        "processed_count": 1,
        "success_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
        "results": [
            {
                "source_path": str(image_path.resolve()),
                "output_path": str(cleaned_path.resolve()),
                "status": "success",
                "message": "EXIF removed.",
                "removed_exif": True,
            }
        ],
    }
    assert inspect_exif(str(cleaned_path)) == {
        "image_path": str(cleaned_path.resolve()),
        "has_exif": False,
        "exif": {},
        "warnings": [],
    }


def test_batch_strip_exif_supports_png_and_webp(tmp_path: Path) -> None:
    folder = tmp_path / "modern-formats"
    folder.mkdir()
    png_path = _write_png(
        folder / "photo.png",
        exif_dict={"0th": {piexif.ImageIFD.Make: "Google"}},
    )
    webp_path = _write_webp(
        folder / "photo.webp",
        exif_dict={"GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N"}},
    )

    result = batch_strip_exif(str(folder))

    results_by_path = {entry["source_path"]: entry for entry in result["results"]}
    assert result["processed_count"] == 2
    assert result["success_count"] == 2
    assert results_by_path[str(png_path.resolve())]["output_path"] == str(
        (folder / "photo.cleaned.png").resolve()
    )
    assert results_by_path[str(webp_path.resolve())]["output_path"] == str(
        (folder / "photo.cleaned.webp").resolve()
    )
