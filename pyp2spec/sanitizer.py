"""
Security module for sanitizing PyPI metadata before rendering into RPM spec files.
"""
from __future__ import annotations

import re
from pathlib import Path

from pyp2spec.utils import MissingPackageNameError


# Shell metacharacters to remove (dangerous for command injection)
# Note: { } are preserved for RPM macros like %%{version}
DANGEROUS_CHARS = r'[$`|;&<>()\[\]\\\'"]'


def _sanitize_base(text: str, allow_spaces: bool = False) -> str:
    """Core sanitization function for all spec file fields.

    text: The input text to sanitize
    allow_spaces: Whether to preserve spaces
    Returns a sanitized text safe for spec file insertion
    """
    if not text:
        return text

    # Remove newlines (convert to spaces first, then handle below)
    text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

    # Remove control characters
    text = ''.join(c for c in text if ord(c) >= 32)

    # Remove dangerous %() execution patterns
    text = re.sub(r'%\([^)]*\)?', '', text)

    # Escape % signs for RPM
    text = text.replace('%', '%%')

    # Remove shell metacharacters (preserves Unicode)
    text = re.sub(DANGEROUS_CHARS, '_', text)

    if not allow_spaces:
        text = text.replace(' ', '')

    return text.strip()


def _sanitize_with_spaces(dirty_string: str) -> str:
    return _sanitize_base(dirty_string, allow_spaces=True)


def _sanitize_name(name: str) -> str:
    """Sanitize package name for RPM spec files.

    Returns a name normalized according to PEP 503.
    """
    if not name:
        raise MissingPackageNameError("Cannot create a package without a name")

    result = _sanitize_base(name.lower())
    # Normalize separators and remove leading/trailing ones
    result = re.sub(r"[-_.]+", "-", result).strip('-_')
    return result


def _sanitize_wheel_name(name: str) -> str:
    """Normalize as in the wheel specification:
    https://packaging.python.org/en/latest/specifications/binary-distribution-format/#escaping-and-unicode
    PEP 625 specifies sdist names to this format."""

    return _sanitize_name(name).replace("-", "_")


def _sanitize_archive_name(archive_name: str) -> str:
    """Sanitize archive filenames - prevent path traversal."""
    archive_name = archive_name.replace('\\', '/')
    safe_name = Path(archive_name).name

    return _sanitize_base(safe_name)


def _sanitize_extras_list(extras: list[str]) -> list[str]:
    return [clean for extra in extras if (clean := _sanitize_base(extra))]


def sanitize(field_name: str, value: str | list[str]) -> str | list[str]:
    """Main sanitization entry point for all spec file fields.

    field_name: The name of the field being sanitized
    value: The value to sanitize
    Returns a sanitized value safe for spec file insertion
    """
    sanitizers = {
        "name": _sanitize_name,
        "wheel_name": _sanitize_wheel_name,
        "archive_name": _sanitize_archive_name,
        "license": _sanitize_with_spaces,
        "summary": _sanitize_with_spaces,
        "version": _sanitize_base,
        "url": _sanitize_base,
        "extras": _sanitize_extras_list,
    }

    sanitizer_func = sanitizers.get(field_name)
    return sanitizer_func(value)
