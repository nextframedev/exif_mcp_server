from __future__ import annotations

from pathlib import Path

from exif_mcp_server.tools.inspect import has_gps_exif, inspect_exif
from exif_mcp_server.tools.privacy import summarize_exif_privacy


def test_sample_images_cover_expected_exif_cases() -> None:
    root = Path("examples/sample_images").resolve()

    plain = root / "plain-no-exif.jpg"
    basic = root / "basic-exif.jpg"
    gps = root / "gps-exif.jpg"
    tiff = root / "tiff-exif.tiff"

    assert plain.exists()
    assert basic.exists()
    assert gps.exists()
    assert tiff.exists()

    assert inspect_exif(str(plain))["has_exif"] is False
    assert has_gps_exif(str(plain))["has_gps"] is False
    assert summarize_exif_privacy(str(plain))["privacy_risk"] == "none"

    basic_result = inspect_exif(str(basic))
    assert basic_result["has_exif"] is True
    assert basic_result["exif"]["Make"] == "Apple"
    assert basic_result["exif"]["Model"] == "iPhone 14"
    assert has_gps_exif(str(basic))["has_gps"] is False
    assert summarize_exif_privacy(str(basic))["privacy_risk"] == "medium"

    gps_result = inspect_exif(str(gps))
    assert gps_result["has_exif"] is True
    assert gps_result["exif"]["Make"] == "Canon"
    assert has_gps_exif(str(gps))["has_gps"] is True
    assert summarize_exif_privacy(str(gps))["privacy_risk"] == "high"

    tiff_result = inspect_exif(str(tiff))
    assert tiff_result["has_exif"] is True
    assert tiff_result["exif"]["Make"] == "Canon"
    assert has_gps_exif(str(tiff))["has_gps"] is True
    assert summarize_exif_privacy(str(tiff))["privacy_risk"] == "high"
