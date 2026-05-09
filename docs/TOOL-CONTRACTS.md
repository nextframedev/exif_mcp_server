# TOOL CONTRACTS — EXIF MCP SERVER

These contracts define the target shape for tool inputs and outputs.
Keep them stable once implemented.

---

## 1. inspect_exif

### Purpose
Read EXIF metadata from a single image.

### Inputs
- `image_path: str`

### Output
```json
{
  "image_path": "/path/to/image.jpg",
  "has_exif": true,
  "exif": {
    "Make": "Apple",
    "Model": "iPhone 14",
    "DateTimeOriginal": "2026:04:16 10:30:00"
  },
  "warnings": []
}
```

### Notes
- If no EXIF exists, return `has_exif: false` and an empty `exif` object.
- Do not return raw library-specific objects.

---

## 2. has_gps_exif

### Purpose
Check whether the image contains GPS/location EXIF fields.

### Inputs
- `image_path: str`

### Output
```json
{
  "image_path": "/path/to/image.jpg",
  "has_gps": true,
  "gps_fields_present": ["GPSLatitude", "GPSLongitude"]
}
```

### Notes
- Return an empty list if GPS data is absent.
- This tool is read-only.

---

## 3. summarize_exif_privacy

### Purpose
Summarize privacy-relevant EXIF fields in compact form.

### Inputs
- `image_path: str`

### Output
```json
{
  "image_path": "/path/to/image.jpg",
  "has_exif": true,
  "privacy_risk": "high",
  "findings": [
    {
      "field": "GPSLatitude",
      "severity": "high",
      "reason": "Location metadata can reveal where the photo was taken."
    },
    {
      "field": "Model",
      "severity": "low",
      "reason": "Device metadata may reveal camera or phone model."
    }
  ],
  "summary": "This image contains GPS metadata and device information."
}
```

### Notes
- Risk levels should be one of: `none`, `low`, `medium`, `high`
- Keep summaries short and factual.

---

## 4. strip_exif

### Purpose
Remove EXIF metadata from a single image.

### Inputs
- `image_path: str`
- `output_path: str | null = null`
- `overwrite: bool = false`

### Output
```json
{
  "source_path": "/path/to/image.jpg",
  "output_path": "/path/to/image.cleaned.jpg",
  "removed_exif": true,
  "notes": ["Created sibling cleaned file."]
}
```

### Notes
- Must not overwrite by default.
- If `overwrite` is true, document and validate behavior clearly.
- Return the actual path written.

---

## 5. batch_strip_exif

### Purpose
Remove EXIF metadata from supported images in a folder.

### Inputs
- `folder_path: str`
- `output_folder: str | null = null`
- `recursive: bool = false`
- `overwrite: bool = false`
- `extensions: list[str] | null = null`

### Output
```json
{
  "folder_path": "/path/to/folder",
  "processed_count": 3,
  "success_count": 2,
  "failed_count": 1,
  "skipped_count": 0,
  "results": [
    {
      "source_path": "/path/to/folder/a.jpg",
      "output_path": "/path/to/folder/a.cleaned.jpg",
      "status": "success",
      "message": "EXIF removed."
    },
    {
      "source_path": "/path/to/folder/b.jpg",
      "status": "failed",
      "message": "Unsupported image type."
    }
  ]
}
```

### Notes
- Keep going even if one file fails.
- Return per-file outcomes plus an overall summary.

---

## 6. find_images_with_gps_exif

### Purpose
Find images in a folder that contain GPS/location EXIF fields.

### Inputs
- `folder_path: str`
- `recursive: bool = false`
- `extensions: list[str] | null = null`

### Output
```json
{
  "folder_path": "/path/to/folder",
  "scanned_count": 4,
  "matched_count": 2,
  "failed_count": 0,
  "skipped_count": 1,
  "matches": [
    {
      "image_path": "/path/to/folder/a.jpg",
      "gps_fields_present": ["GPSLatitude", "GPSLongitude"]
    }
  ],
  "failures": []
}
```

### Notes
- Return only matched images in `matches`.
- Keep per-file failures explicit in `failures`.
- This tool is read-only.

---

## 7. batch_strip_gps_exif

### Purpose
Remove only GPS EXIF metadata from supported images in a folder.

### Inputs
- `folder_path: str`
- `output_folder: str | null = null`
- `recursive: bool = false`
- `overwrite: bool = false`
- `extensions: list[str] | null = null`

### Output
```json
{
  "folder_path": "/path/to/folder",
  "processed_count": 2,
  "success_count": 1,
  "failed_count": 0,
  "skipped_count": 1,
  "results": [
    {
      "source_path": "/path/to/folder/a.jpg",
      "output_path": "/path/to/cleaned/a.cleaned.jpg",
      "status": "success",
      "message": "GPS EXIF removed.",
      "removed_gps": true
    }
  ]
}
```

### Notes
- GPS-only cleanup should preserve other EXIF fields where possible.
- Keep going even if one file fails.
- Return per-file outcomes plus an overall summary.

---

## 8. inspect_exif_detailed

### Purpose
Read all EXIF metadata from a single image with per-tag references.

### Inputs
- `image_path: str`

### Output
```json
{
  "image_path": "/path/to/image.jpg",
  "has_exif": true,
  "exif": {
    "Artist": "Blue J.",
    "Make": "Canon"
  },
  "warnings": [],
  "tags": [
    {
      "ifd": "0th",
      "tag_id": 315,
      "field_name": "Artist",
      "field_key": "Artist",
      "value": "Blue J."
    }
  ]
}
```

### Notes
- `tags` is intended for selective cleanup workflows.
- This tool is read-only.

---

## 9. find_images_with_exif_fields

### Purpose
Find images in a folder that contain selected EXIF fields.

### Inputs
- `folder_path: str`
- `field_names: list[str]`
- `match_mode: "any" | "all" = "any"`
- `recursive: bool = false`
- `extensions: list[str] | null = null`

### Output
```json
{
  "folder_path": "/path/to/folder",
  "requested_fields": ["Artist", "XPAuthor", "Copyright"],
  "match_mode": "any",
  "scanned_count": 4,
  "matched_count": 2,
  "failed_count": 0,
  "skipped_count": 1,
  "matches": [
    {
      "image_path": "/path/to/folder/a.jpg",
      "matched_fields": ["Artist"]
    }
  ],
  "failures": []
}
```

### Notes
- Useful for workflows such as finding author-bearing photos before cleanup.
- This tool is read-only.

---

## 10. strip_selected_exif_fields

### Purpose
Remove selected EXIF fields from a single image.

### Inputs
- `image_path: str`
- `field_names: list[str]`
- `output_path: str | null = null`
- `overwrite: bool = false`
- `dry_run: bool = false`
- `include_comparison: bool = false`
- `write_report: bool = false`

### Output
```json
{
  "source_path": "/path/to/image.jpg",
  "output_path": "/path/to/image.cleaned.jpg",
  "removed_fields": ["Artist"],
  "removed_tag_count": 1,
  "notes": ["Created sibling cleaned file."]
}
```

### Notes
- Must not overwrite by default.
- Removes only matched fields and preserves other EXIF fields when possible.

---

## 11. batch_strip_selected_exif_fields

### Purpose
Remove selected EXIF fields from supported images in a folder.

### Inputs
- `folder_path: str`
- `field_names: list[str]`
- `output_folder: str | null = null`
- `recursive: bool = false`
- `overwrite: bool = false`
- `extensions: list[str] | null = null`
- `dry_run: bool = false`
- `include_comparison: bool = false`
- `write_report: bool = false`

### Output
```json
{
  "folder_path": "/path/to/folder",
  "requested_fields": ["Artist", "XPAuthor", "Copyright"],
  "processed_count": 2,
  "success_count": 1,
  "failed_count": 0,
  "skipped_count": 1,
  "results": [
    {
      "source_path": "/path/to/folder/a.jpg",
      "output_path": "/path/to/cleaned/a.cleaned.jpg",
      "status": "success",
      "message": "Selected EXIF fields removed.",
      "removed_fields": ["Artist"],
      "removed_tag_count": 1
    }
  ]
}
```

### Notes
- Keep going even if one file fails.
- Useful for privacy workflows that target author/device/user-identifying fields.

---

## Contract Rules

1. Outputs must be JSON-serializable.
2. Use explicit field names.
3. Keep shapes stable over time.
4. Read-only tools must have no side effects.
5. Mutating tools must make outputs and paths explicit.
