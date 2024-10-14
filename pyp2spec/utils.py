import re


class Pyp2specError(Exception):
    """Metaexception to derive the custom errors from"""


def normalize(package_name):
    """Normalize given package name as defined in PEP 503"""

    return re.sub(r"[-_.]+", "-", package_name).lower()


def normalize_as_wheel_name(package_name):
    """Normalize as in the wheel specification:
    https://packaging.python.org/en/latest/specifications/binary-distribution-format/#escaping-and-unicode
    PEP 625 specifies sdist names to this format."""

    return normalize(package_name).replace("-", "_")
