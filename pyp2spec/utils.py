"""
This module contains common functions and classes imported in multiple other modules.
"""

import re

from packaging.requirements import Requirement


class Pyp2specError(Exception):
    """Metaexception to derive the custom errors from"""


class SdistNotFoundError(Pyp2specError):
    """Raised when there's no sdist file in the PyPI metadata"""


def normalize_name(package_name):
    """Normalize given package name as defined in PEP 503.
    The resulting string better conforms with Fedora's Packaging Guidelines."""

    return re.sub(r"[-_.]+", "-", package_name).lower()


def normalize_as_wheel_name(package_name):
    """Normalize as in the wheel specification:
    https://packaging.python.org/en/latest/specifications/binary-distribution-format/#escaping-and-unicode
    PEP 625 specifies sdist names to this format."""

    return normalize_name(package_name).replace("-", "_")


def prepend_name_with_python(name, python_alt_version=None):
    """Create a component name for the specfile.

    Prepend the name with 'python' (unless it already starts with it).
    Add the Python alternative version, if it's defined.
    Valid outcomes:
    package name: foo, python_alt_version: 3.11
    -> python3.11-foo

    package name: foo, python_alt_version: None
    -> python-foo

    package name: python-foo, python_alt_version: 3.12
    -> python3.12-foo

    package name: python-foo, python_alt_version: None
    -> python-foo
    """

    alt_version = "" if python_alt_version is None else python_alt_version
    if name.startswith("python"):
        return name.replace("python", f"python{alt_version}")
    return f"python{alt_version}-{name}"


def filter_license_classifiers(classifiers_list):
    """Return the list of license classifiers defined for the package.

    Filter out the parent categories `OSI-/DFSG Approved` which don't have any meaning.
    """

    return  [
        c for c in classifiers_list
        if (
            c.startswith("License")
            and c not in ("License :: OSI Approved", "License :: DFSG approved")
        )
    ]


def summary(raw_summary):
    """Return either a summary or a "..." string.

    Summary is an optional field, so it may be empty or it can consist of
    multi-line strings which we can't use.
    """

    if not raw_summary or len(raw_summary.split("\n")) > 1:
        raw_summary = "..."
    return raw_summary


def extras(requires_dist):
    """Return the sorted list of the found extras names.

    Packages define extras explicitly via `Provides-Extra` and
    indirectly via `Requires-Dist` metadata.
    PyPI metadata doesn't provide the first one, but it is possible to
    derive extras names from the `requires_dist` key.
    Example value of `requires_dist`:
    ["sphinxcontrib-websupport ; extra == 'docs'", "flake8>=3.5.0 ; extra == 'lint'"]
    If package defines an extra with no requirements, we can't detect that.
    """
    extra_from_req = re.compile(r'''\bextra\s+==\s+["']([^"']+)["']''')
    extras = set()
    if requires_dist:
        for required_dist in requires_dist:
            # packaging.Requirement can parse the markers, but it
            # doesn't provide their string representations,
            # hence we need to use regex to pick them out
            req = Requirement(required_dist)
            if found := re.search(extra_from_req, str(req.marker)):
                extras.add(found.group(1))
    return sorted(extras)


def archive_name(archive_urls):
    """Return the given's package version sdist name for further processing.
    Quit the script if not found (bdists can't be processed).
    """
    for entry in archive_urls:
        if entry["packagetype"] == "sdist":
            return entry["filename"]
    raise SdistNotFoundError("Sdist not found, valid spec file cannot be produced")


def is_archful(archive_urls):
    """Determine if package is archful by checking the wheel filenames.

    Wheel name consists of defined fields, one of them being an abi tag.
    Example abi tags:
    - click-0.2-py2.py3-none-any.whl -> "none"
    - cryptography-2.2-cp34-abi3-manylinux1_x86_64.whl -> "abi3"
    If the value is "none", wheel was not built for a specific architecture,
    probably containing pure Python modules.
    Other values indicate build for an architecture, which can mean
    the presence of compiled extensions.
    Packages can publish multiple wheels, the pure-Python alongside the compiled ones.
    For our purposes, if we find at least one wheel with an abi tag different that "none",
    we consider the package archful.
    The compiled extensions bring optimizations and in Fedora,
    it is generally encouraged to bring in the optional features of the packages.
    """

    for entry in archive_urls:
        if entry["packagetype"] == "bdist_wheel":
            abi_tag = entry["filename"].split("-")[-2]
            if abi_tag != "none":
                return True
    # all of the found wheel names had 'none' as abi_tag
    return False


def find_project_url(urls):
    """
    Project urls are an optional field and come in a form of a dict, e.g.:
    {"homepage": "https://mypackagehomepage.com"}.
    There may be multiple urls defined and keys are arbitrary.
    As there's no way to programmatically determine "the best" url for the
    spec file, return the first existing url from the dict.
    """

    return list(urls.values())[0] if urls else "..."
