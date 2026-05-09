from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from exif_mcp_server.tools.privacy import summarize_exif_privacy

piexif = pytest.importorskip("piexif")
PIL = pytest.importorskip("PIL.Image")


def test_privacy_symbol_exists() -> None:
    assert summarize_exif_privacy.__name__ == "summarize_exif_privacy"


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


def test_summarize_exif_privacy_high_risk_contract_shape(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "privacy-high.jpg",
        exif_dict={
            "0th": {
                piexif.ImageIFD.Make: "Apple",
                piexif.ImageIFD.Model: "iPhone 14",
                piexif.ImageIFD.Software: "Photos 3.0",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2026:04:16 10:30:00",
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((49, 1), (16, 1), (0, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((123, 1), (7, 1), (0, 1)),
            },
        },
    )

    result = summarize_exif_privacy(str(image_path))

    assert result["image_path"] == str(image_path.resolve())
    assert result["has_exif"] is True
    assert result["privacy_risk"] == "high"
    assert result["summary"] == (
        "This image contains GPS metadata, device information, "
        "timestamp metadata, and software tags."
    )
    assert result["findings"] == [
        {
            "field": "GPSLatitude",
            "severity": "high",
            "reason": "Location metadata can reveal where the photo was taken.",
        },
        {
            "field": "Make",
            "severity": "low",
            "reason": "Device metadata may reveal the camera or phone model used.",
        },
        {
            "field": "Model",
            "severity": "low",
            "reason": "Device metadata may reveal the camera or phone model used.",
        },
        {
            "field": "DateTimeOriginal",
            "severity": "medium",
            "reason": "Timestamp metadata can reveal when the photo was created.",
        },
        {
            "field": "Software",
            "severity": "low",
            "reason": "Software tags can reveal which app or workflow touched the image.",
        },
    ]


def test_summarize_exif_privacy_medium_risk_without_gps(tmp_path: Path) -> None:
    image_path = _write_jpeg(
        tmp_path / "privacy-medium.jpg",
        exif_dict={
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2026:04:16 10:30:00",
                piexif.ExifIFD.BodySerialNumber: "ABC123456",
            },
        },
    )

    result = summarize_exif_privacy(str(image_path))

    assert result["has_exif"] is True
    assert result["privacy_risk"] == "medium"
    assert result["summary"] == (
        "This image contains timestamp metadata and identifier-like metadata."
    )
    assert result["findings"] == [
        {
            "field": "DateTimeOriginal",
            "severity": "medium",
            "reason": "Timestamp metadata can reveal when the photo was created.",
        },
        {
            "field": "BodySerialNumber",
            "severity": "medium",
            "reason": (
                "Identifier-like metadata can make an image more traceable "
                "to a device or owner."
            ),
        },
    ]


def test_summarize_exif_privacy_handles_no_exif(tmp_path: Path) -> None:
    image_path = _write_jpeg(tmp_path / "privacy-none.jpg")

    result = summarize_exif_privacy(str(image_path))

    assert result == {
        "image_path": str(image_path.resolve()),
        "has_exif": False,
        "privacy_risk": "none",
        "findings": [],
        "summary": "This image does not contain EXIF metadata.",
    }


def test_summarize_exif_privacy_supports_tiff(tmp_path: Path) -> None:
    image_path = _write_tiff(
        tmp_path / "privacy-high.tiff",
        exif_dict={
            "0th": {
                piexif.ImageIFD.Make: "Canon",
                piexif.ImageIFD.Model: "EOS R6",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2026:04:16 12:15:00",
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((49, 1), (16, 1), (0, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((123, 1), (7, 1), (0, 1)),
            },
        },
    )

    result = summarize_exif_privacy(str(image_path))

    assert result["has_exif"] is True
    assert result["privacy_risk"] == "high"
    assert result["summary"] == (
        "This image contains GPS metadata, device information, "
        "and timestamp metadata."
    )


def test_summarize_exif_privacy_supports_png(tmp_path: Path) -> None:
    image_path = _write_png(
        tmp_path / "privacy-high.png",
        exif_dict={
            "0th": {
                piexif.ImageIFD.Make: "Google",
                piexif.ImageIFD.Model: "Pixel 9",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2026:04:16 12:15:00",
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((49, 1), (16, 1), (0, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((123, 1), (7, 1), (0, 1)),
            },
        },
    )

    result = summarize_exif_privacy(str(image_path))

    assert result["has_exif"] is True
    assert result["privacy_risk"] == "high"


def test_summarize_exif_privacy_supports_webp(tmp_path: Path) -> None:
    image_path = _write_webp(
        tmp_path / "privacy-high.webp",
        exif_dict={
            "0th": {
                piexif.ImageIFD.Make: "Google",
                piexif.ImageIFD.Model: "Pixel 9",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: "2026:04:16 12:15:00",
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((49, 1), (16, 1), (0, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
                piexif.GPSIFD.GPSLongitude: ((123, 1), (7, 1), (0, 1)),
            },
        },
    )

    result = summarize_exif_privacy(str(image_path))

    assert result["has_exif"] is True
    assert result["privacy_risk"] == "high"
