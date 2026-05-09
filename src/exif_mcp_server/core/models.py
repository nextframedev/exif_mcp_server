"""Typed JSON-friendly models aligned with docs/TOOL-CONTRACTS.md."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypeAlias

from typing_extensions import TypedDict

PrivacyRisk: TypeAlias = Literal["none", "low", "medium", "high"]
FindingSeverity: TypeAlias = Literal["low", "medium", "high"]
BatchFileStatus: TypeAlias = Literal["success", "failed", "skipped"]
FieldMatchMode: TypeAlias = Literal["any", "all"]


class InspectExifResult(TypedDict):
    """Contract for the inspect_exif MCP tool."""

    image_path: str
    has_exif: bool
    exif: dict[str, Any]
    warnings: list[str]


class ExifTagDetail(TypedDict):
    """Per-tag EXIF detail entry with stable tag references."""

    ifd: str
    tag_id: int
    field_name: str
    field_key: str
    value: Any


class InspectExifDetailedResult(TypedDict):
    """Detailed EXIF inspection result with per-tag references."""

    image_path: str
    has_exif: bool
    exif: dict[str, Any]
    warnings: list[str]
    tags: list[ExifTagDetail]


class HasGpsExifResult(TypedDict):
    """Contract for the has_gps_exif MCP tool."""

    image_path: str
    has_gps: bool
    gps_fields_present: list[str]


class GpsImageMatch(TypedDict):
    """Matched image entry for folder-level GPS inspection."""

    image_path: str
    gps_fields_present: list[str]


class GpsScanFailure(TypedDict):
    """Failed image entry for folder-level GPS inspection."""

    image_path: str
    message: str


class FindImagesWithGpsExifResult(TypedDict):
    """Contract for a folder-level GPS scan tool."""

    folder_path: str
    scanned_count: int
    matched_count: int
    failed_count: int
    skipped_count: int
    matches: list[GpsImageMatch]
    failures: list[GpsScanFailure]


class ExifFieldImageMatch(TypedDict):
    """Matched image entry for folder-level EXIF field scans."""

    image_path: str
    matched_fields: list[str]


class ExifFieldScanFailure(TypedDict):
    """Failed image entry for folder-level EXIF field scans."""

    image_path: str
    message: str


class FindImagesWithExifFieldsResult(TypedDict):
    """Contract for a folder-level scan by EXIF field names."""

    folder_path: str
    requested_fields: list[str]
    match_mode: FieldMatchMode
    scanned_count: int
    matched_count: int
    failed_count: int
    skipped_count: int
    matches: list[ExifFieldImageMatch]
    failures: list[ExifFieldScanFailure]


class PrivacyFinding(TypedDict):
    """Privacy finding returned by summarize_exif_privacy."""

    field: str
    severity: FindingSeverity
    reason: str


class SummarizeExifPrivacyResult(TypedDict):
    """Contract for the summarize_exif_privacy MCP tool."""

    image_path: str
    has_exif: bool
    privacy_risk: PrivacyRisk
    findings: list[PrivacyFinding]
    summary: str


class StripExifResult(TypedDict):
    """Contract for the strip_exif MCP tool."""

    source_path: str
    output_path: str
    removed_exif: bool
    notes: list[str]
    dry_run: NotRequired[bool]
    comparison: NotRequired["ExifComparison"]
    report_path: NotRequired[str]


class StripGpsExifResult(TypedDict):
    """Contract for a GPS-only cleanup operation."""

    source_path: str
    output_path: str
    removed_gps: bool
    notes: list[str]
    dry_run: NotRequired[bool]
    comparison: NotRequired["ExifComparison"]
    report_path: NotRequired[str]


class StripSelectedExifResult(TypedDict):
    """Contract for selective EXIF field removal from one image."""

    source_path: str
    output_path: str
    removed_fields: list[str]
    removed_tag_count: int
    notes: list[str]
    dry_run: NotRequired[bool]
    comparison: NotRequired["ExifComparison"]
    report_path: NotRequired[str]


class ExifComparison(TypedDict):
    """Optional before/after summary for EXIF cleanup operations."""

    before_has_exif: bool
    after_has_exif: bool
    removed_fields: list[str]
    remaining_fields: list[str]


class BatchFileResult(TypedDict):
    """Per-file status entry for batch_strip_exif."""

    source_path: str
    status: BatchFileStatus
    message: str
    output_path: NotRequired[str]
    removed_exif: NotRequired[bool]
    dry_run: NotRequired[bool]
    comparison: NotRequired[ExifComparison]
    report_path: NotRequired[str]


class BatchGpsFileResult(TypedDict):
    """Per-file status entry for batch_strip_gps_exif."""

    source_path: str
    status: BatchFileStatus
    message: str
    output_path: NotRequired[str]
    removed_gps: NotRequired[bool]
    dry_run: NotRequired[bool]
    comparison: NotRequired[ExifComparison]
    report_path: NotRequired[str]


class BatchSelectedExifFileResult(TypedDict):
    """Per-file status entry for batch_strip_selected_exif_fields."""

    source_path: str
    status: BatchFileStatus
    message: str
    output_path: NotRequired[str]
    removed_fields: NotRequired[list[str]]
    removed_tag_count: NotRequired[int]
    dry_run: NotRequired[bool]
    comparison: NotRequired[ExifComparison]
    report_path: NotRequired[str]


class BatchStripExifResult(TypedDict):
    """Contract for the batch_strip_exif MCP tool."""

    folder_path: str
    processed_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    results: list[BatchFileResult]


class BatchStripGpsExifResult(TypedDict):
    """Contract for the batch_strip_gps_exif MCP tool."""

    folder_path: str
    processed_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    results: list[BatchGpsFileResult]


class BatchStripSelectedExifResult(TypedDict):
    """Contract for batch selective EXIF field removal."""

    folder_path: str
    requested_fields: list[str]
    processed_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    results: list[BatchSelectedExifFileResult]
