"""Shared EXIF read interfaces reused by the MCP adapter and web app."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, cast

from .errors import ExifReadError, InvalidMetadataSelectionError
from .filetypes import validate_image_path
from .models import (
    ExifFieldImageMatch,
    ExifFieldScanFailure,
    ExifTagDetail,
    FieldMatchMode,
    FindImagesWithExifFieldsResult,
    FindImagesWithGpsExifResult,
    GpsImageMatch,
    GpsScanFailure,
    HasGpsExifResult,
    InspectExifDetailedResult,
    InspectExifResult,
    PrivacyFinding,
    PrivacyRisk,
    SummarizeExifPrivacyResult,
)

piexif_module: Any | None
try:
    import piexif as _piexif_module
except ImportError:
    piexif_module = None
else:
    piexif_module = _piexif_module

pil_image_module: Any | None
pillow_unidentified_image_error: type[Exception]
try:
    from PIL import Image as _pil_image_module
    from PIL import UnidentifiedImageError as _pillow_unidentified_image_error
    from PIL.ExifTags import GPSTAGS, TAGS
except ImportError:
    pil_image_module = None
    pillow_unidentified_image_error = OSError
    GPSTAGS = {}
    TAGS = {}
else:
    pil_image_module = _pil_image_module
    pillow_unidentified_image_error = _pillow_unidentified_image_error

EXIF_IFD_ORDER = ("0th", "Exif", "GPS", "Interop", "1st")
GPS_COORDINATE_FIELDS = {"GPSLatitude", "GPSLongitude", "GPSLatitudeRef", "GPSLongitudeRef"}
DEVICE_FIELDS = ("Make", "Model")
TIMESTAMP_FIELDS = ("DateTimeOriginal", "DateTimeDigitized", "DateTime")
SOFTWARE_FIELDS = ("Software", "ProcessingSoftware", "HostComputer")
SERIAL_LIKE_FIELDS = ("BodySerialNumber", "LensSerialNumber", "CameraOwnerName")
GROUP_LABELS = {
    "0th": "Image",
    "Exif": "Exif",
    "GPS": "GPS / Location",
    "1st": "Thumbnail",
    "Interop": "Interoperability",
}
SENSITIVE_FIELDS = {
    "DateTimeOriginal",
    "DateTimeDigitized",
    "SubSecTimeOriginal",
    "SubSecTimeDigitized",
    "DateTime",
    "Artist",
    "Copyright",
}
TIFF_EXTENSIONS = {".tif", ".tiff"}
STRUCTURAL_TIFF_FIELDS = {
    "ImageWidth",
    "ImageLength",
    "BitsPerSample",
    "Compression",
    "PhotometricInterpretation",
    "StripOffsets",
    "SamplesPerPixel",
    "RowsPerStrip",
    "StripByteCounts",
    "PlanarConfiguration",
}


def _require_reader_dependencies() -> None:
    if pil_image_module is None or piexif_module is None:
        raise ExifReadError(
            "EXIF reading dependencies are unavailable. Install Pillow and piexif."
        )


def _reader_dependencies() -> tuple[Any, Any]:
    """Return Pillow and piexif modules after validating they are available."""

    _require_reader_dependencies()
    return cast(Any, pil_image_module), cast(Any, piexif_module)


def _load_exif_dict(image_path: str) -> tuple[Path, dict[str, dict[int, Any]]]:
    """Validate an image path and load EXIF data into a consistent shape."""

    image_module, _piexif = _reader_dependencies()
    path = validate_image_path(image_path)

    try:
        with image_module.open(path) as image:
            image.load()
            exif_source: bytes | None
            if path.suffix.lower() in TIFF_EXTENSIONS:
                exif_source = path.read_bytes()
            else:
                exif_source = cast(bytes | None, image.info.get("exif"))
    except pillow_unidentified_image_error as exc:
        raise ExifReadError(f"File is not a valid image: {path}") from exc
    except OSError as exc:
        raise ExifReadError(f"Failed to read image file: {path}") from exc

    return path, _normalized_exif_dict_from_bytes(exif_source, path)


def _empty_exif_dict() -> dict[str, dict[int, Any]]:
    """Return an empty EXIF structure for images without EXIF metadata."""

    return {ifd_name: {} for ifd_name in EXIF_IFD_ORDER}


def _tag_name(ifd_name: str, tag_id: int) -> str:
    """Convert a numeric EXIF tag id into a stable readable field name."""

    if piexif_module is not None:
        try:
            tag_info = piexif_module.TAGS[ifd_name][tag_id]
            return cast(str, tag_info["name"])
        except Exception:
            pass

    if ifd_name == "GPS":
        gps_tag = GPSTAGS.get(tag_id, f"GPS:{tag_id}")
        return gps_tag if isinstance(gps_tag, str) else str(gps_tag)

    tag_name = TAGS.get(tag_id, f"Tag-{tag_id}")
    return tag_name if isinstance(tag_name, str) else str(tag_name)


def _normalized_exif_dict_from_bytes(
    exif_bytes: bytes | None,
    path_hint: Path | None = None,
) -> dict[str, dict[int, Any]]:
    """Normalize raw EXIF bytes into the shared IFD mapping."""

    if not exif_bytes:
        return _empty_exif_dict()

    _image_module, piexif_lib = _reader_dependencies()
    try:
        exif_dict = piexif_lib.load(exif_bytes)
    except Exception as exc:
        location = f" for: {path_hint}" if path_hint is not None else ""
        raise ExifReadError(f"Failed to parse EXIF metadata{location}") from exc

    return {
        ifd_name: cast(dict[int, Any], exif_dict.get(ifd_name, {}))
        for ifd_name in EXIF_IFD_ORDER
    }


def _convert_exif_value(value: Any) -> Any:
    """Convert piexif/Pillow values into JSON-serializable primitives."""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip("\x00")
    if (
        isinstance(value, tuple)
        and len(value) == 2
        and all(isinstance(part, int) for part in value)
    ):
        numerator, denominator = value
        if denominator == 0:
            return str(value)
        return round(numerator / denominator, 6)
    if isinstance(value, (list, tuple)):
        return [_convert_exif_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _convert_exif_value(item) for key, item in value.items()}
    return value


def _flatten_exif(exif_dict: dict[str, dict[int, Any]]) -> tuple[dict[str, Any], list[str]]:
    """Flatten EXIF IFD groups into a compact JSON-friendly mapping."""

    flattened: dict[str, Any] = {}
    warnings: list[str] = []

    for ifd_name in EXIF_IFD_ORDER:
        for tag_id, raw_value in exif_dict.get(ifd_name, {}).items():
            tag_name = _tag_name(ifd_name, tag_id)
            if tag_name in STRUCTURAL_TIFF_FIELDS:
                continue
            key = tag_name
            if key in flattened:
                key = f"{ifd_name}.{tag_name}"
                warnings.append(
                    f"Duplicate EXIF tag name '{tag_name}' was namespaced as '{key}'."
                )
            flattened[key] = _convert_exif_value(raw_value)

    return flattened, warnings


def _tag_details(exif_dict: dict[str, dict[int, Any]]) -> list[ExifTagDetail]:
    """Return stable per-tag EXIF details including removal-friendly references."""

    details: list[ExifTagDetail] = []
    seen_field_names: set[str] = set()

    for ifd_name in EXIF_IFD_ORDER:
        for tag_id, raw_value in exif_dict.get(ifd_name, {}).items():
            field_name = _tag_name(ifd_name, tag_id)
            if field_name in STRUCTURAL_TIFF_FIELDS:
                continue
            field_key = field_name
            if field_name in seen_field_names:
                field_key = f"{ifd_name}.{field_name}"
            seen_field_names.add(field_name)
            details.append(
                {
                    "ifd": ifd_name,
                    "tag_id": tag_id,
                    "field_name": field_name,
                    "field_key": field_key,
                    "value": _convert_exif_value(raw_value),
                }
            )

    return details


def _gps_field_names(exif_dict: dict[str, dict[int, Any]]) -> list[str]:
    """Return stable readable names for GPS fields present in EXIF metadata."""

    gps_fields = [_tag_name("GPS", tag_id) for tag_id in exif_dict.get("GPS", {})]
    return sorted(gps_fields)


def _has_any_exif(exif_dict: dict[str, dict[int, Any]]) -> bool:
    """Check whether any EXIF IFD contains metadata."""

    for ifd_name in EXIF_IFD_ORDER:
        for tag_id in exif_dict.get(ifd_name, {}):
            if _tag_name(ifd_name, tag_id) not in STRUCTURAL_TIFF_FIELDS:
                return True
    return False


def _dms_to_decimal(dms: Any, ref: Any) -> float | None:
    """Convert GPS DMS tuples to decimal degrees when possible."""

    try:
        degrees = dms[0][0] / dms[0][1]
        minutes = dms[1][0] / dms[1][1]
        seconds = dms[2][0] / dms[2][1]
        decimal = degrees + minutes / 60 + seconds / 3600
        if ref in (b"S", b"W", "S", "W"):
            decimal = -decimal
        return round(decimal, 7)
    except Exception:
        return None


def extract_grouped_metadata(image_bytes: bytes, filename: str) -> dict[str, Any]:
    """Extract grouped EXIF metadata for the web UI from raw image bytes."""

    image_module, _piexif = _reader_dependencies()
    result: dict[str, Any] = {"groups": [], "gps_decimal": None, "has_exif": False}
    extension = Path(filename).suffix.lower()

    try:
        exif_source: bytes | None
        if extension in {".jpg", ".jpeg", ".tif", ".tiff"}:
            exif_source = image_bytes
        else:
            with image_module.open(io.BytesIO(image_bytes)) as image:
                image.load()
                exif_source = cast(bytes | None, image.info.get("exif"))
    except (pillow_unidentified_image_error, OSError):
        return result

    try:
        exif_dict = _normalized_exif_dict_from_bytes(exif_source)
    except ExifReadError:
        return result

    for ifd_name in EXIF_IFD_ORDER:
        ifd_data = exif_dict.get(ifd_name, {})
        if not ifd_data:
            continue
        tags: list[dict[str, Any]] = []
        for tag_id, raw_value in ifd_data.items():
            tag_name = _tag_name(ifd_name, tag_id)
            if tag_name in STRUCTURAL_TIFF_FIELDS:
                continue
            tags.append(
                {
                    "id": tag_id,
                    "ifd": ifd_name,
                    "name": tag_name,
                    "value": _convert_exif_value(raw_value),
                    "sensitive": ifd_name == "GPS" or tag_name in SENSITIVE_FIELDS,
                }
            )
        if not tags:
            continue
        result["has_exif"] = True
        result["groups"].append(
            {
                "ifd": ifd_name,
                "label": GROUP_LABELS.get(ifd_name, ifd_name),
                "tags": tags,
            }
        )

    gps_ifd = exif_dict.get("GPS", {})
    if piexif_module is not None and gps_ifd:
        latitude = gps_ifd.get(piexif_module.GPSIFD.GPSLatitude)
        latitude_ref = gps_ifd.get(piexif_module.GPSIFD.GPSLatitudeRef)
        longitude = gps_ifd.get(piexif_module.GPSIFD.GPSLongitude)
        longitude_ref = gps_ifd.get(piexif_module.GPSIFD.GPSLongitudeRef)
        if latitude and latitude_ref and longitude and longitude_ref:
            dec_lat = _dms_to_decimal(latitude, latitude_ref)
            dec_lon = _dms_to_decimal(longitude, longitude_ref)
            if dec_lat is not None and dec_lon is not None:
                result["gps_decimal"] = {"lat": dec_lat, "lon": dec_lon}

    return result


def _build_privacy_findings(flattened_exif: dict[str, Any]) -> list[PrivacyFinding]:
    """Convert EXIF fields into stable privacy findings."""

    findings: list[PrivacyFinding] = []

    gps_fields_present = [field for field in GPS_COORDINATE_FIELDS if field in flattened_exif]
    if gps_fields_present:
        findings.append(
            {
                "field": sorted(gps_fields_present)[0],
                "severity": "high",
                "reason": "Location metadata can reveal where the photo was taken.",
            }
        )

    for field_name in DEVICE_FIELDS:
        if field_name in flattened_exif:
            findings.append(
                {
                    "field": field_name,
                    "severity": "low",
                    "reason": "Device metadata may reveal the camera or phone model used.",
                }
            )

    for field_name in TIMESTAMP_FIELDS:
        if field_name in flattened_exif:
            findings.append(
                {
                    "field": field_name,
                    "severity": "medium",
                    "reason": "Timestamp metadata can reveal when the photo was created.",
                }
            )

    for field_name in SOFTWARE_FIELDS:
        if field_name in flattened_exif:
            findings.append(
                {
                    "field": field_name,
                    "severity": "low",
                    "reason": "Software tags can reveal which app or workflow touched the image.",
                }
            )

    for field_name in SERIAL_LIKE_FIELDS:
        if field_name in flattened_exif:
            findings.append(
                {
                    "field": field_name,
                    "severity": "medium",
                    "reason": (
                        "Identifier-like metadata can make an image more "
                        "traceable to a device or owner."
                    ),
                }
            )

    return findings


def _privacy_risk(findings: list[PrivacyFinding]) -> PrivacyRisk:
    """Collapse per-field findings into one stable privacy risk level."""

    severities = {finding["severity"] for finding in findings}
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    if "low" in severities:
        return "low"
    return "none"


def _privacy_summary(flattened_exif: dict[str, Any], findings: list[PrivacyFinding]) -> str:
    """Generate a short factual summary of privacy-relevant metadata."""

    if not flattened_exif:
        return "This image does not contain EXIF metadata."

    if not findings:
        return "This image contains EXIF metadata but no flagged privacy-sensitive fields."

    categories: list[str] = []
    field_names = {finding["field"] for finding in findings}
    if field_names & GPS_COORDINATE_FIELDS:
        categories.append("GPS metadata")
    if field_names & set(DEVICE_FIELDS):
        categories.append("device information")
    if field_names & set(TIMESTAMP_FIELDS):
        categories.append("timestamp metadata")
    if field_names & set(SOFTWARE_FIELDS):
        categories.append("software tags")
    if field_names & set(SERIAL_LIKE_FIELDS):
        categories.append("identifier-like metadata")

    if len(categories) == 1:
        category_text = categories[0]
    elif len(categories) == 2:
        category_text = f"{categories[0]} and {categories[1]}"
    else:
        category_text = ", ".join(categories[:-1]) + f", and {categories[-1]}"
    return f"This image contains {category_text}."


def _normalized_field_names(field_names: list[str]) -> list[str]:
    """Normalize field-name selection input while preserving stable order."""

    normalized: list[str] = []
    seen: set[str] = set()
    for field_name in field_names:
        value = field_name.strip()
        if not value:
            continue
        lowered = value.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(value)
    if not normalized:
        raise InvalidMetadataSelectionError(
            "At least one non-empty EXIF field name is required."
        )
    return normalized


def _field_key_aliases(field_key: str) -> set[str]:
    """Return all case-insensitive aliases that can match one flattened EXIF key."""

    aliases = {field_key.casefold()}
    if "." in field_key:
        aliases.add(field_key.split(".", 1)[1].casefold())
    return aliases


def _validate_match_mode(match_mode: str) -> FieldMatchMode:
    """Validate one EXIF field-match mode value."""

    normalized_mode = match_mode.strip().lower()
    if normalized_mode not in {"any", "all"}:
        raise InvalidMetadataSelectionError(
            "match_mode must be either 'any' or 'all'."
        )
    return cast(FieldMatchMode, normalized_mode)


def read_exif(image_path: str) -> InspectExifResult:
    """Read EXIF metadata from a single image path."""

    normalized_path, exif_dict = _load_exif_dict(image_path)
    flattened_exif, warnings = _flatten_exif(exif_dict)
    return {
        "image_path": str(normalized_path),
        "has_exif": _has_any_exif(exif_dict),
        "exif": flattened_exif,
        "warnings": warnings,
    }


def read_exif_detailed(image_path: str) -> InspectExifDetailedResult:
    """Read all EXIF metadata from one image with per-tag references."""

    normalized_path, exif_dict = _load_exif_dict(image_path)
    flattened_exif, warnings = _flatten_exif(exif_dict)
    return {
        "image_path": str(normalized_path),
        "has_exif": _has_any_exif(exif_dict),
        "exif": flattened_exif,
        "warnings": warnings,
        "tags": _tag_details(exif_dict),
    }


def detect_gps_exif(image_path: str) -> HasGpsExifResult:
    """Detect whether GPS EXIF fields are present on the image."""

    normalized_path, exif_dict = _load_exif_dict(image_path)
    gps_fields_present = _gps_field_names(exif_dict)
    return {
        "image_path": str(normalized_path),
        "has_gps": bool(gps_fields_present),
        "gps_fields_present": gps_fields_present,
    }


def summarize_exif_privacy(image_path: str) -> SummarizeExifPrivacyResult:
    """Summarize privacy-relevant EXIF fields in a stable JSON shape."""

    normalized_path, exif_dict = _load_exif_dict(image_path)
    flattened_exif, _warnings = _flatten_exif(exif_dict)
    findings = _build_privacy_findings(flattened_exif)
    return {
        "image_path": str(normalized_path),
        "has_exif": _has_any_exif(exif_dict),
        "privacy_risk": _privacy_risk(findings),
        "findings": findings,
        "summary": _privacy_summary(flattened_exif, findings),
    }


def find_images_with_gps_exif_in_folder(
    folder_path: str,
    recursive: bool = False,
    extensions: list[str] | None = None,
) -> FindImagesWithGpsExifResult:
    """Scan one folder and return only the images that contain GPS EXIF metadata."""

    from .exif_cleaner import _candidate_files, _normalized_extensions
    from .filetypes import validate_folder_path

    source_folder = validate_folder_path(folder_path)
    selected_extensions = _normalized_extensions(extensions)

    matches: list[GpsImageMatch] = []
    failures: list[GpsScanFailure] = []
    scanned_count = 0
    skipped_count = 0

    for file_path in _candidate_files(source_folder, recursive):
        if file_path.suffix.lower() not in selected_extensions:
            skipped_count += 1
            continue

        try:
            gps_result = detect_gps_exif(str(file_path))
            scanned_count += 1
            if gps_result["has_gps"]:
                matches.append(
                    {
                        "image_path": gps_result["image_path"],
                        "gps_fields_present": gps_result["gps_fields_present"],
                    }
                )
        except ExifReadError as exc:
            failures.append(
                {
                    "image_path": str(file_path.resolve()),
                    "message": str(exc),
                }
            )

    return {
        "folder_path": str(source_folder),
        "scanned_count": scanned_count,
        "matched_count": len(matches),
        "failed_count": len(failures),
        "skipped_count": skipped_count,
        "matches": matches,
        "failures": failures,
    }


def find_images_with_exif_fields_in_folder(
    folder_path: str,
    field_names: list[str],
    match_mode: str = "any",
    recursive: bool = False,
    extensions: list[str] | None = None,
) -> FindImagesWithExifFieldsResult:
    """Scan one folder and return images that contain selected EXIF fields."""

    from .exif_cleaner import _candidate_files, _normalized_extensions
    from .filetypes import validate_folder_path

    source_folder = validate_folder_path(folder_path)
    normalized_fields = _normalized_field_names(field_names)
    normalized_field_keys = [field.casefold() for field in normalized_fields]
    field_key_set = set(normalized_field_keys)
    normalized_match_mode = _validate_match_mode(match_mode)
    selected_extensions = _normalized_extensions(extensions)

    matches: list[ExifFieldImageMatch] = []
    failures: list[ExifFieldScanFailure] = []
    scanned_count = 0
    skipped_count = 0

    for file_path in _candidate_files(source_folder, recursive):
        if file_path.suffix.lower() not in selected_extensions:
            skipped_count += 1
            continue

        try:
            inspect_result = read_exif(str(file_path))
            scanned_count += 1
            matched_fields: set[str] = set()
            matched_requested: set[str] = set()

            for field_key in inspect_result["exif"]:
                aliases = _field_key_aliases(field_key)
                intersection = aliases & field_key_set
                if not intersection:
                    continue
                matched_fields.add(field_key)
                matched_requested.update(intersection)

            is_match = bool(matched_fields)
            if normalized_match_mode == "all":
                is_match = len(matched_requested) == len(field_key_set)

            if is_match:
                matches.append(
                    {
                        "image_path": inspect_result["image_path"],
                        "matched_fields": sorted(matched_fields),
                    }
                )
        except ExifReadError as exc:
            failures.append(
                {
                    "image_path": str(file_path.resolve()),
                    "message": str(exc),
                }
            )

    return {
        "folder_path": str(source_folder),
        "requested_fields": normalized_fields,
        "match_mode": normalized_match_mode,
        "scanned_count": scanned_count,
        "matched_count": len(matches),
        "failed_count": len(failures),
        "skipped_count": skipped_count,
        "matches": matches,
        "failures": failures,
    }
