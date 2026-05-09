# Sample Images

This folder contains small JPG fixtures for manual testing.

Files:

- `plain-no-exif.jpg`
  - no EXIF metadata
- `basic-exif.jpg`
  - basic EXIF fields
  - device make/model
  - software tag
  - capture timestamp
- `gps-exif.jpg`
  - device metadata
  - capture timestamp
  - serial-like metadata
  - GPS latitude/longitude fields
- `tiff-exif.tiff`
  - TIFF sample with device metadata
  - capture timestamp
  - GPS latitude/longitude fields

These files are intended for:

- local MCP Inspector testing
- manual tool-call examples
- smoke-testing the web app upload flow

They are intentionally small and synthetic.
