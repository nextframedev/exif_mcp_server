"""Prompt templates for common EXIF privacy workflows."""

from __future__ import annotations

from typing import Any


def register_prompts(server: Any) -> None:
    """Register EXIF workflow prompts on the provided MCP server."""

    @server.prompt(
        name="review-photo-privacy",
        title="Review Photo Privacy",
        description=(
            "Guide a client through inspecting EXIF and explaining privacy "
            "risk for one image."
        ),
    )
    def review_photo_privacy(image_path: str) -> list[str]:
        return [
            (
                "Review the privacy implications of this image: "
                f"`{image_path}`."
            ),
            (
                "Call `inspect_exif` first to see the raw EXIF fields, then call "
                "`has_gps_exif` and `summarize_exif_privacy`."
            ),
            (
                "Explain whether the image is safe to share publicly, citing any "
                "GPS, timestamp, device, software, or identifier-like metadata."
            ),
        ]

    @server.prompt(
        name="clean-photos-for-sharing",
        title="Clean Photos For Sharing",
        description=(
            "Guide a client through inspecting and cleaning one folder of "
            "images safely."
        ),
    )
    def clean_photos_for_sharing(folder_path: str, output_folder: str | None = None) -> list[str]:
        output_text = (
            f"Write cleaned images to `{output_folder}`."
            if output_folder
            else "Write sibling cleaned copies next to the original images."
        )
        return [
            f"Prepare images in `{folder_path}` for safer sharing.",
            (
                "Inspect likely JPG/JPEG files first when helpful, summarize the "
                "privacy risk, and then call `batch_strip_exif`."
            ),
            (
                f"{output_text} Do not overwrite originals unless the user has "
                "explicitly asked for overwrite behavior."
            ),
            (
                "After cleaning, summarize how many files were processed, which "
                "ones failed or were skipped, and where the cleaned files were written."
            ),
        ]
