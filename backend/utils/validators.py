"""
validators.py — secure upload validation + profile sanity rules.

Three layers of defence before a file is accepted:
  1. Extension whitelist (fast, user-friendly)
  2. Size limit (protects bandwidth & storage quota)
  3. Magic-byte sniffing (catches "virus.exe renamed to meal.jpg")

In production you would additionally ship files to an AV scanner
before making them downloadable — see docs/security.md.
"""

import binascii


class FileValidationError(ValueError):
    """Raised when an uploaded file fails a validation rule."""


class FileSizeError(FileValidationError):
    """Oversized upload — mapped to HTTP 413 (Payload Too Large)."""


# Minimal magic-number table for the formats this planner allows.
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "gif": [b"GIF87a", b"GIF89a"],
    "webp": [b"RIFF"],                      # RIFF....WEBP
    "pdf": [b"%PDF"],
    "txt": [],                               # plain text: no reliable signature
    "csv": [],                               # text-based food logs
}

# map common aliases onto canonical keys
_ALIASES = {"jpeg": "jpg", "htm": "html", "tif": "tiff"}


def normalize_extension(filename: str) -> str:
    """Return lowercase extension without the dot ('meal.PNG' -> 'png')."""
    if "." not in filename:
        return ""
    ext = filename.rsplit(".", 1)[1].strip().lower()
    return _ALIASES.get(ext, ext)


def validate_file(
    filename: str,
    data: bytes,
    allowed_extensions: list[str],
    max_size_mb: int,
) -> str:
    """
    Validate an upload. Returns the normalized extension on success.

    Raises FileValidationError with a user-friendly message otherwise.
    """
    # ---- 1. Extension whitelist ----
    ext = normalize_extension(filename)
    allowed = [normalize_extension(f"*.{e}") for e in allowed_extensions]
    if not ext:
        raise FileValidationError("File has no extension")
    if ext not in allowed:
        raise FileValidationError(
            f"File type '.{ext}' not allowed. Allowed: {', '.join('.' + a for a in allowed)}"
        )

    # ---- 2. Size limit (checked BEFORE touching storage) ----
    max_bytes = max_size_mb * 1024 * 1024
    if len(data) == 0:
        raise FileValidationError("File is empty")
    if len(data) > max_bytes:
        raise FileSizeError(
            f"File too large ({len(data) / (1024 * 1024):.1f} MB). Limit is {max_size_mb} MB"
        )

    # ---- 3. Magic-byte sniffing (content must match the extension) ----
    signatures = MAGIC_SIGNATURES.get(ext)
    if signatures:  # empty list = format with no fixed signature (e.g. txt)
        if not any(data.startswith(sig) for sig in signatures):
            raise FileValidationError(
                f"File content does not look like a real .{ext} file"
            )

    return ext


def is_safe_storage_path(storage_path: str) -> bool:
    """Basic sanity check for object keys coming from untrusted places."""
    return ".." not in storage_path and storage_path.startswith("meals/")


# ---------------------------------------------------------------------------
# Profile sanity rules (educational demo — NOT medical ranges)
# ---------------------------------------------------------------------------
def bmi_value(height_cm: int, weight_kg: int) -> float:
    """Educational BMI calculation for the dashboard (not a diagnosis)."""
    meters = height_cm / 100
    return round(weight_kg / (meters * meters), 1)


def bmi_category(bmi: float) -> str:
    """Generic WHO-style label for display only, with a disclaimer."""
    if bmi < 18.5:
        return "underweight (display only)"
    if bmi < 25:
        return "healthy range (display only)"
    if bmi < 30:
        return "overweight (display only)"
    return "obese (display only)"
