"""Shared EXIF write interfaces for single-file and batch cleanup flows."""

from __future__ import annotations

import io
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, cast

from .errors import (
    ExifWriteError,
    InvalidMetadataSelectionError,
    InvalidPathError,
    UnsafeOverwriteError,
)
from .exif_reader import detect_gps_exif, read_exif, read_exif_detailed
from .filetypes import (
    SUPPORTED_IMAGE_EXTENSIONS,
    normalize_path,
    validate_folder_path,
    validate_image_path,
)
from .models import (
    BatchFileResult,
    BatchGpsFileResult,
    BatchSelectedExifFileResult,
    BatchStripExifResult,
    BatchStripGpsExifResult,
    BatchStripSelectedExifResult,
    ExifComparison,
    ExifTagDetail,
    StripExifResult,
    StripGpsExifResult,
    StripSelectedExifResult,
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
except ImportError:
    pil_image_module = None
    pillow_unidentified_image_error = OSError
else:
    pil_image_module = _pil_image_module
    pillow_unidentified_image_error = _pillow_unidentified_image_error

TIFF_EXTENSIONS = {".tif", ".tiff"}
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
PNG_EXTENSIONS = {".png"}
WEBP_EXTENSIONS = {".webp"}


def _require_cleaner_dependencies() -> None:
    if pil_image_module is None or piexif_module is None:
        raise ExifWriteError(
            "EXIF cleaning dependencies are unavailable. Install Pillow and piexif."
        )


def _cleaner_dependencies() -> tuple[Any, Any]:
    """Return Pillow and piexif modules after validating they are available."""

    _require_cleaner_dependencies()
    return cast(Any, pil_image_module), cast(Any, piexif_module)


def _default_output_path(source_path: Path) -> Path:
    """Create the default sibling cleaned-file path."""

    return source_path.with_name(f"{source_path.stem}.cleaned{source_path.suffix.lower()}")


def _image_format_for_extension(extension: str, original_format: str | None) -> str:
    """Resolve the Pillow output format for one file extension."""

    if extension in JPEG_EXTENSIONS:
        return "JPEG"
    if extension in TIFF_EXTENSIONS:
        return "TIFF"
    if extension in PNG_EXTENSIONS:
        return "PNG"
    if extension in WEBP_EXTENSIONS:
        return "WEBP"
    return original_format or "JPEG"


def _resolve_output_path(
    source_path: Path,
    output_path: str | None,
    overwrite: bool,
) -> tuple[Path, list[str]]:
    """Resolve the destination path and generate behavior notes."""

    if output_path is None:
        if overwrite:
            return source_path, ["Overwrote the source image because overwrite=true."]
        target_path = _default_output_path(source_path)
        if target_path.exists():
            raise UnsafeOverwriteError(
                f"Refusing to overwrite existing output file without overwrite=true: {target_path}"
            )
        return target_path, ["Created sibling cleaned file."]

    target_path = normalize_path(output_path)
    if target_path.parent != source_path.parent and not target_path.parent.exists():
        raise InvalidPathError(f"Output folder does not exist: {target_path.parent}")
    if target_path.is_dir():
        raise InvalidPathError(f"Expected an output file path, received directory: {target_path}")
    if target_path == source_path and not overwrite:
        raise UnsafeOverwriteError(
            "Refusing to overwrite the source image without overwrite=true."
        )
    if target_path.exists() and not overwrite:
        raise UnsafeOverwriteError(
            f"Refusing to overwrite existing output file without overwrite=true: {target_path}"
        )

    notes = ["Wrote cleaned image to explicit output path."]
    if target_path == source_path and overwrite:
        notes = ["Overwrote the source image because overwrite=true."]
    elif target_path.exists() and overwrite:
        notes.append("Overwrote an existing output file because overwrite=true.")
    return target_path, notes


def _has_exif_bytes(source_path: Path) -> bool:
    """Check whether an image currently contains EXIF metadata."""

    try:
        return bool(_read_exif_map(source_path))
    except Exception as exc:
        raise ExifWriteError(f"Failed to inspect EXIF metadata for: {source_path}") from exc


def _save_without_exif(source_path: Path, destination_path: Path) -> None:
    """Write a cleaned image copy without EXIF metadata."""

    image_module, _piexif = _cleaner_dependencies()
    try:
        with image_module.open(source_path) as image:
            image.load()
            suffix = destination_path.suffix.lower() or source_path.suffix.lower()
            image_format = _image_format_for_extension(suffix, image.format)
            if image_format == "TIFF":
                clean_image = image_module.frombytes(image.mode, image.size, image.tobytes())
                clean_image.save(destination_path, format="TIFF")
            else:
                save_image: Any = image
                if image_format == "JPEG" and image.mode not in ("RGB", "L"):
                    save_image = image.convert("RGB")
                save_kwargs = {"quality": 95} if image_format == "JPEG" else {}
                save_image.save(destination_path, format=image_format, **save_kwargs)
    except pillow_unidentified_image_error as exc:
        raise ExifWriteError(f"File is not a valid image: {source_path}") from exc
    except OSError as exc:
        raise ExifWriteError(f"Failed to write cleaned image: {destination_path}") from exc


def _overwrite_source_without_exif(source_path: Path) -> None:
    """Rewrite the source path in place without EXIF metadata."""

    with NamedTemporaryFile(
        suffix=source_path.suffix,
        dir=source_path.parent,
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        _save_without_exif(source_path, temp_path)
        temp_path.replace(source_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _overwrite_source_with_bytes(source_path: Path, image_bytes: bytes) -> None:
    """Rewrite the source file in place using already-cleaned image bytes."""

    with NamedTemporaryFile(
        suffix=source_path.suffix,
        dir=source_path.parent,
        delete=False,
    ) as temp_file:
        temp_file.write(image_bytes)
        temp_path = Path(temp_file.name)

    try:
        temp_path.replace(source_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _comparison_from_exif_maps(
    before_exif: dict[str, Any],
    after_exif: dict[str, Any],
) -> ExifComparison:
    """Build a compact before/after EXIF comparison summary."""

    before_fields = set(before_exif)
    after_fields = set(after_exif)
    return {
        "before_has_exif": bool(before_exif),
        "after_has_exif": bool(after_exif),
        "removed_fields": sorted(before_fields - after_fields),
        "remaining_fields": sorted(after_fields),
    }


def _read_exif_map(image_path: Path) -> dict[str, Any]:
    """Return the flattened EXIF mapping for one file path."""

    return read_exif(str(image_path))["exif"]


def _sidecar_report_path(target_path: Path) -> Path:
    """Return the default sidecar JSON report path for one cleaned file."""

    return target_path.with_name(f"{target_path.stem}.exif-report.json")


def _write_json_report(report_path: Path, payload: dict[str, Any], overwrite: bool) -> None:
    """Write one JSON report file with overwrite safeguards."""

    if report_path.exists() and not overwrite:
        raise UnsafeOverwriteError(
            f"Refusing to overwrite existing report file without overwrite=true: {report_path}"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        report_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ExifWriteError(f"Failed to write JSON report: {report_path}") from exc


def _remove_gps_exif_bytes(image_path: Path) -> tuple[bytes, bool]:
    """Return bytes with only the GPS EXIF group removed."""

    image_bytes = image_path.read_bytes()
    cleaned_bytes, removed_count = strip_selected_metadata(
        image_bytes,
        image_path.name,
        remove_groups=["GPS"],
        remove_tags=[],
    )
    if removed_count == -1:
        raise ExifWriteError(
            "Failed to selectively remove GPS EXIF metadata while preserving other EXIF fields."
        )
    return cleaned_bytes, removed_count > 0


def _normalized_selected_fields(field_names: list[str]) -> list[str]:
    """Normalize selected EXIF field names while preserving order."""

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
    """Return all case-insensitive aliases for one flattened EXIF field key."""

    aliases = {field_key.casefold()}
    if "." in field_key:
        aliases.add(field_key.split(".", 1)[1].casefold())
    return aliases


def _matched_tag_details(
    image_path: Path,
    selected_fields: list[str],
) -> list[ExifTagDetail]:
    """Return detailed tag references matching the selected field names."""

    selected_field_set = {field.casefold() for field in selected_fields}
    tag_details = read_exif_detailed(str(image_path))["tags"]
    matched: list[ExifTagDetail] = []
    for tag_detail in tag_details:
        aliases = _field_key_aliases(tag_detail["field_key"])
        if (
            tag_detail["field_name"].casefold() in selected_field_set
            or aliases & selected_field_set
        ):
            matched.append(tag_detail)
    return matched


def _write_image_bytes(
    source_path: Path,
    target_path: Path,
    image_bytes: bytes,
) -> None:
    """Write cleaned image bytes to the resolved target path safely."""

    if target_path == source_path:
        _overwrite_source_with_bytes(source_path, image_bytes)
        return
    try:
        target_path.write_bytes(image_bytes)
    except OSError as exc:
        raise ExifWriteError(f"Failed to write cleaned image: {target_path}") from exc


def strip_selected_metadata(
    image_bytes: bytes,
    filename: str,
    remove_groups: list[str],
    remove_tags: list[dict[str, Any]],
) -> tuple[bytes, int]:
    """Remove selected EXIF groups or tags from raw image bytes.

    Returns the cleaned bytes plus the count of removed items. When piexif
    cannot re-encode the edited metadata safely, the fallback strips all EXIF
    metadata and returns `-1`.
    """

    image_module, piexif_lib = _cleaner_dependencies()
    extension = Path(filename).suffix.lower()

    def strip_all_exif() -> bytes:
        with image_module.open(io.BytesIO(image_bytes)) as image:
            image.load()
            output = io.BytesIO()
            image_to_save: Any = image
            image_format = _image_format_for_extension(extension, image.format)
            if image.mode in ("RGBA", "P") and image_format == "JPEG":
                image_to_save = image.convert("RGB")
            save_kwargs = {"quality": 95} if image_format == "JPEG" else {}
            image_to_save.save(output, format=image_format, **save_kwargs)
            output.seek(0)
            return output.read()

    exif_source: bytes | None
    if extension in TIFF_EXTENSIONS:
        exif_source = image_bytes
    else:
        with image_module.open(io.BytesIO(image_bytes)) as image:
            image.load()
            exif_source = cast(bytes | None, image.info.get("exif"))

    try:
        exif_dict = piexif_lib.load(exif_source)
    except Exception:
        return strip_all_exif(), -1

    removed = 0
    valid_groups = {"0th", "Exif", "GPS", "1st", "Interop"}

    for group_name in remove_groups:
        if group_name in valid_groups and exif_dict.get(group_name):
            removed += len(exif_dict[group_name])
            exif_dict[group_name] = {}

    for tag_info in remove_tags:
        ifd_name = tag_info.get("ifd")
        tag_id = int(tag_info.get("id", -1))
        if ifd_name in valid_groups and tag_id in exif_dict.get(ifd_name, {}):
            del exif_dict[ifd_name][tag_id]
            removed += 1

    try:
        exif_bytes = piexif_lib.dump(exif_dict)
    except Exception:
        try:
            exif_dict.pop("thumbnail", None)
            exif_dict["1st"] = {}
            exif_bytes = piexif_lib.dump(exif_dict)
        except Exception:
            return strip_all_exif(), -1

    with image_module.open(io.BytesIO(image_bytes)) as image:
        image.load()
        output = io.BytesIO()
        image_format = _image_format_for_extension(extension, image.format)
        save_kwargs = {"quality": 95} if image_format == "JPEG" else {}
        image.save(output, format=image_format, exif=exif_bytes, **save_kwargs)
        output.seek(0)
        return output.read(), removed


def strip_exif_from_file(
    image_path: str,
    output_path: str | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> StripExifResult:
    """Remove EXIF metadata from a single file without hidden side effects."""

    source_path = validate_image_path(image_path)
    target_path, notes = _resolve_output_path(source_path, output_path, overwrite)
    had_exif = _has_exif_bytes(source_path)
    before_exif = _read_exif_map(source_path) if include_comparison or write_report else {}

    if dry_run:
        notes.append("Dry run only; no files were written.")
    else:
        if target_path == source_path:
            _overwrite_source_without_exif(source_path)
        else:
            _save_without_exif(source_path, target_path)

    if had_exif:
        notes.append(
            "Dry run would remove EXIF metadata from the output image."
            if dry_run
            else "Removed EXIF metadata from the written image."
        )
    else:
        notes.append(
            "Source image did not contain EXIF metadata."
            if not dry_run
            else "Dry run found no EXIF metadata to remove."
        )

    result: StripExifResult = {
        "source_path": str(source_path),
        "output_path": str(target_path),
        "removed_exif": had_exif,
        "notes": notes,
    }
    if dry_run:
        result["dry_run"] = True

    if include_comparison or write_report:
        after_exif = {} if dry_run else _read_exif_map(target_path)
        comparison = _comparison_from_exif_maps(before_exif, after_exif)
        if include_comparison:
            result["comparison"] = comparison
        if write_report:
            if dry_run:
                notes.append("Dry run skipped writing the sidecar JSON report.")
            else:
                report_path = _sidecar_report_path(target_path)
                report_payload: dict[str, Any] = {
                    "source_path": str(source_path),
                    "output_path": str(target_path),
                    "removed_exif": had_exif,
                    "dry_run": False,
                    "notes": notes,
                    "comparison": comparison,
                }
                _write_json_report(report_path, report_payload, overwrite=overwrite)
                result["report_path"] = str(report_path)
                notes.append("Wrote sidecar JSON report.")

    return result


def strip_gps_exif_from_file(
    image_path: str,
    output_path: str | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> StripGpsExifResult:
    """Remove only the GPS EXIF group from a single file without hidden side effects."""

    source_path = validate_image_path(image_path)
    target_path, notes = _resolve_output_path(source_path, output_path, overwrite)
    had_gps = detect_gps_exif(str(source_path))["has_gps"]
    before_exif = _read_exif_map(source_path) if include_comparison or write_report else {}

    if dry_run:
        notes.append("Dry run only; no files were written.")
    else:
        cleaned_bytes, _removed_gps = _remove_gps_exif_bytes(source_path)
        if target_path == source_path:
            _overwrite_source_with_bytes(source_path, cleaned_bytes)
        else:
            _write_image_bytes(source_path, target_path, cleaned_bytes)

    if had_gps:
        notes.append(
            "Dry run would remove GPS EXIF metadata from the output image."
            if dry_run
            else "Removed GPS EXIF metadata from the written image."
        )
    else:
        notes.append(
            "Source image did not contain GPS EXIF metadata."
            if not dry_run
            else "Dry run found no GPS EXIF metadata to remove."
        )

    result: StripGpsExifResult = {
        "source_path": str(source_path),
        "output_path": str(target_path),
        "removed_gps": had_gps,
        "notes": notes,
    }
    if dry_run:
        result["dry_run"] = True

    if include_comparison or write_report:
        after_exif = {} if dry_run else _read_exif_map(target_path)
        comparison = _comparison_from_exif_maps(before_exif, after_exif)
        if include_comparison:
            result["comparison"] = comparison
        if write_report:
            if dry_run:
                notes.append("Dry run skipped writing the sidecar JSON report.")
            else:
                report_path = _sidecar_report_path(target_path)
                report_payload: dict[str, Any] = {
                    "source_path": str(source_path),
                    "output_path": str(target_path),
                    "removed_gps": had_gps,
                    "dry_run": False,
                    "notes": notes,
                    "comparison": comparison,
                }
                _write_json_report(report_path, report_payload, overwrite=overwrite)
                result["report_path"] = str(report_path)
                notes.append("Wrote sidecar JSON report.")

    return result


def strip_exif_fields_from_file(
    image_path: str,
    field_names: list[str],
    output_path: str | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> StripSelectedExifResult:
    """Remove selected EXIF fields from a single file without hidden side effects."""

    source_path = validate_image_path(image_path)
    selected_fields = _normalized_selected_fields(field_names)
    target_path, notes = _resolve_output_path(source_path, output_path, overwrite)
    before_exif = _read_exif_map(source_path) if include_comparison or write_report else {}
    matched_tags = _matched_tag_details(source_path, selected_fields)
    remove_tags = [{"ifd": tag["ifd"], "id": tag["tag_id"]} for tag in matched_tags]
    removed_fields = sorted({tag["field_key"] for tag in matched_tags})
    removed_tag_count = len(remove_tags)

    if dry_run:
        notes.append("Dry run only; no files were written.")
    else:
        if removed_tag_count > 0:
            image_bytes = source_path.read_bytes()
            cleaned_bytes, removed_count = strip_selected_metadata(
                image_bytes,
                source_path.name,
                remove_groups=[],
                remove_tags=remove_tags,
            )
            if removed_count == -1:
                raise ExifWriteError(
                    "Failed to selectively remove EXIF fields while preserving the remaining "
                    "EXIF metadata."
                )
            _write_image_bytes(source_path, target_path, cleaned_bytes)
        elif target_path != source_path:
            _write_image_bytes(source_path, target_path, source_path.read_bytes())

    if removed_tag_count > 0:
        notes.append(
            "Dry run would remove selected EXIF fields from the output image."
            if dry_run
            else "Removed selected EXIF fields from the written image."
        )
    else:
        notes.append(
            "Dry run found no matching EXIF fields to remove."
            if dry_run
            else "Source image did not contain the selected EXIF fields."
        )

    result: StripSelectedExifResult = {
        "source_path": str(source_path),
        "output_path": str(target_path),
        "removed_fields": removed_fields,
        "removed_tag_count": removed_tag_count,
        "notes": notes,
    }
    if dry_run:
        result["dry_run"] = True

    if include_comparison or write_report:
        if dry_run:
            after_exif = {
                field_name: value
                for field_name, value in before_exif.items()
                if field_name not in set(removed_fields)
            }
        else:
            after_exif = _read_exif_map(target_path)
        comparison = _comparison_from_exif_maps(before_exif, after_exif)
        if include_comparison:
            result["comparison"] = comparison
        if write_report:
            if dry_run:
                notes.append("Dry run skipped writing the sidecar JSON report.")
            else:
                report_path = _sidecar_report_path(target_path)
                report_payload: dict[str, Any] = {
                    "source_path": str(source_path),
                    "output_path": str(target_path),
                    "removed_fields": removed_fields,
                    "removed_tag_count": removed_tag_count,
                    "dry_run": False,
                    "notes": notes,
                    "comparison": comparison,
                }
                _write_json_report(report_path, report_payload, overwrite=overwrite)
                result["report_path"] = str(report_path)
                notes.append("Wrote sidecar JSON report.")

    return result


def _normalized_extensions(extensions: list[str] | None) -> set[str]:
    """Normalize an optional extension filter."""

    if not extensions:
        return set(SUPPORTED_IMAGE_EXTENSIONS)

    normalized: set[str] = set()
    for extension in extensions:
        value = extension.strip().lower()
        if not value:
            continue
        if not value.startswith("."):
            value = f".{value}"
        normalized.add(value)
    return normalized & set(SUPPORTED_IMAGE_EXTENSIONS)


def _candidate_files(folder_path: Path, recursive: bool) -> list[Path]:
    """Return candidate file paths in deterministic order."""

    iterator = folder_path.rglob("*") if recursive else folder_path.iterdir()
    return sorted(
        path
        for path in iterator
        if path.is_file() and not path.stem.endswith(".cleaned")
    )


def _batch_output_path(
    source_path: Path,
    source_root: Path,
    output_root: Path,
    overwrite: bool,
) -> Path:
    """Build the output path for one batch item inside the output folder."""

    relative_parent = source_path.parent.relative_to(source_root)
    target_parent = output_root / relative_parent
    target_parent.mkdir(parents=True, exist_ok=True)
    if overwrite:
        return target_parent / source_path.name
    return target_parent / f"{source_path.stem}.cleaned{source_path.suffix.lower()}"


def batch_strip_exif_in_folder(
    folder_path: str,
    output_folder: str | None = None,
    recursive: bool = False,
    overwrite: bool = False,
    extensions: list[str] | None = None,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> BatchStripExifResult:
    """Remove EXIF metadata from supported files in a folder."""

    source_folder = validate_folder_path(folder_path)
    selected_extensions = _normalized_extensions(extensions)
    output_root = normalize_path(output_folder) if output_folder is not None else None
    if output_root is not None:
        if output_root.exists() and not output_root.is_dir():
            raise InvalidPathError(
                f"Expected output_folder to be a directory path: {output_root}"
            )
        output_root.mkdir(parents=True, exist_ok=True)

    results: list[BatchFileResult] = []

    for file_path in _candidate_files(source_folder, recursive):
        if file_path.suffix.lower() not in selected_extensions:
            results.append(
                {
                    "source_path": str(file_path.resolve()),
                    "status": "skipped",
                    "message": (
                        "Skipped because the file extension is not selected "
                        "for batch processing."
                    ),
                }
            )
            continue

        try:
            per_file_output = None
            if output_root is not None:
                per_file_output = str(
                    _batch_output_path(file_path, source_folder, output_root, overwrite).resolve()
                )
            strip_result = strip_exif_from_file(
                image_path=str(file_path),
                output_path=per_file_output,
                overwrite=overwrite,
                dry_run=dry_run,
                include_comparison=include_comparison,
                write_report=write_report,
            )
            batch_item: BatchFileResult = {
                "source_path": strip_result["source_path"],
                "output_path": strip_result["output_path"],
                "status": "success",
                "message": (
                    "Dry run completed; no files were written."
                    if strip_result.get("dry_run")
                    else (
                        "EXIF removed."
                        if strip_result["removed_exif"]
                        else "No EXIF found; wrote clean copy."
                    )
                ),
                "removed_exif": strip_result["removed_exif"],
            }
            if strip_result.get("dry_run"):
                batch_item["dry_run"] = True
            if "comparison" in strip_result:
                batch_item["comparison"] = strip_result["comparison"]
            if "report_path" in strip_result:
                batch_item["report_path"] = strip_result["report_path"]
            results.append(batch_item)
        except (ExifWriteError, InvalidPathError, UnsafeOverwriteError) as exc:
            results.append(
                {
                    "source_path": str(file_path.resolve()),
                    "status": "failed",
                    "message": str(exc),
                }
            )

    success_count = sum(1 for result in results if result["status"] == "success")
    failed_count = sum(1 for result in results if result["status"] == "failed")
    skipped_count = sum(1 for result in results if result["status"] == "skipped")

    return {
        "folder_path": str(source_folder),
        "processed_count": len(results),
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "results": results,
    }


def batch_strip_gps_exif_in_folder(
    folder_path: str,
    output_folder: str | None = None,
    recursive: bool = False,
    overwrite: bool = False,
    extensions: list[str] | None = None,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> BatchStripGpsExifResult:
    """Remove only GPS EXIF metadata from supported files in a folder."""

    source_folder = validate_folder_path(folder_path)
    selected_extensions = _normalized_extensions(extensions)
    output_root = normalize_path(output_folder) if output_folder is not None else None
    if output_root is not None:
        if output_root.exists() and not output_root.is_dir():
            raise InvalidPathError(
                f"Expected output_folder to be a directory path: {output_root}"
            )
        output_root.mkdir(parents=True, exist_ok=True)

    results: list[BatchGpsFileResult] = []

    for file_path in _candidate_files(source_folder, recursive):
        if file_path.suffix.lower() not in selected_extensions:
            results.append(
                {
                    "source_path": str(file_path.resolve()),
                    "status": "skipped",
                    "message": (
                        "Skipped because the file extension is not selected "
                        "for batch processing."
                    ),
                }
            )
            continue

        try:
            per_file_output = None
            if output_root is not None:
                per_file_output = str(
                    _batch_output_path(file_path, source_folder, output_root, overwrite).resolve()
                )
            strip_result = strip_gps_exif_from_file(
                image_path=str(file_path),
                output_path=per_file_output,
                overwrite=overwrite,
                dry_run=dry_run,
                include_comparison=include_comparison,
                write_report=write_report,
            )
            batch_item: BatchGpsFileResult = {
                "source_path": strip_result["source_path"],
                "output_path": strip_result["output_path"],
                "status": "success",
                "message": (
                    "Dry run completed; no files were written."
                    if strip_result.get("dry_run")
                    else (
                        "GPS EXIF removed."
                        if strip_result["removed_gps"]
                        else "No GPS EXIF found; wrote clean copy."
                    )
                ),
                "removed_gps": strip_result["removed_gps"],
            }
            if strip_result.get("dry_run"):
                batch_item["dry_run"] = True
            if "comparison" in strip_result:
                batch_item["comparison"] = strip_result["comparison"]
            if "report_path" in strip_result:
                batch_item["report_path"] = strip_result["report_path"]
            results.append(batch_item)
        except (ExifWriteError, InvalidPathError, UnsafeOverwriteError) as exc:
            results.append(
                {
                    "source_path": str(file_path.resolve()),
                    "status": "failed",
                    "message": str(exc),
                }
            )

    success_count = sum(1 for result in results if result["status"] == "success")
    failed_count = sum(1 for result in results if result["status"] == "failed")
    skipped_count = sum(1 for result in results if result["status"] == "skipped")

    return {
        "folder_path": str(source_folder),
        "processed_count": len(results),
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "results": results,
    }


def batch_strip_exif_fields_in_folder(
    folder_path: str,
    field_names: list[str],
    output_folder: str | None = None,
    recursive: bool = False,
    overwrite: bool = False,
    extensions: list[str] | None = None,
    dry_run: bool = False,
    include_comparison: bool = False,
    write_report: bool = False,
) -> BatchStripSelectedExifResult:
    """Remove selected EXIF fields from supported files in a folder."""

    source_folder = validate_folder_path(folder_path)
    selected_fields = _normalized_selected_fields(field_names)
    selected_extensions = _normalized_extensions(extensions)
    output_root = normalize_path(output_folder) if output_folder is not None else None
    if output_root is not None:
        if output_root.exists() and not output_root.is_dir():
            raise InvalidPathError(
                f"Expected output_folder to be a directory path: {output_root}"
            )
        output_root.mkdir(parents=True, exist_ok=True)

    results: list[BatchSelectedExifFileResult] = []

    for file_path in _candidate_files(source_folder, recursive):
        if file_path.suffix.lower() not in selected_extensions:
            results.append(
                {
                    "source_path": str(file_path.resolve()),
                    "status": "skipped",
                    "message": (
                        "Skipped because the file extension is not selected "
                        "for batch processing."
                    ),
                }
            )
            continue

        try:
            per_file_output = None
            if output_root is not None:
                per_file_output = str(
                    _batch_output_path(file_path, source_folder, output_root, overwrite).resolve()
                )
            strip_result = strip_exif_fields_from_file(
                image_path=str(file_path),
                field_names=selected_fields,
                output_path=per_file_output,
                overwrite=overwrite,
                dry_run=dry_run,
                include_comparison=include_comparison,
                write_report=write_report,
            )
            batch_item: BatchSelectedExifFileResult = {
                "source_path": strip_result["source_path"],
                "output_path": strip_result["output_path"],
                "status": "success",
                "message": (
                    "Dry run completed; no files were written."
                    if strip_result.get("dry_run")
                    else (
                        "Selected EXIF fields removed."
                        if strip_result["removed_tag_count"] > 0
                        else "No matching EXIF fields found; wrote clean copy."
                    )
                ),
                "removed_fields": strip_result["removed_fields"],
                "removed_tag_count": strip_result["removed_tag_count"],
            }
            if strip_result.get("dry_run"):
                batch_item["dry_run"] = True
            if "comparison" in strip_result:
                batch_item["comparison"] = strip_result["comparison"]
            if "report_path" in strip_result:
                batch_item["report_path"] = strip_result["report_path"]
            results.append(batch_item)
        except (
            ExifWriteError,
            InvalidMetadataSelectionError,
            InvalidPathError,
            UnsafeOverwriteError,
        ) as exc:
            results.append(
                {
                    "source_path": str(file_path.resolve()),
                    "status": "failed",
                    "message": str(exc),
                }
            )

    success_count = sum(1 for result in results if result["status"] == "success")
    failed_count = sum(1 for result in results if result["status"] == "failed")
    skipped_count = sum(1 for result in results if result["status"] == "skipped")

    return {
        "folder_path": str(source_folder),
        "requested_fields": selected_fields,
        "processed_count": len(results),
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "results": results,
    }
