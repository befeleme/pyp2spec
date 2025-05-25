"""
This module takes care of loading all sorts of data from PyPI APIs.
"""
from __future__ import annotations
from typing import Any

from packaging.metadata import parse_email, RawMetadata
from packaging.version import Version
from requests import Response, Session

from pyp2spec.utils import Pyp2specError


class PackageNotFoundError(Pyp2specError):
    """Raised when there's no such package name on PyPI"""


class CoreMetadataNotFoundError(Pyp2specError):
    """Raised when there's no Metadata file available on PyPI API"""


class CompatibleVersionNotFoundError(Pyp2specError):
    """Raised when project doesn't have a version compatible with the requested one"""


def _get_from_url(url: str, error_str: str, session: Session | None = None) -> Response:
    _session = session or Session()
    response = _session.get(url, headers={
        'User-Agent': 'My User Agent 1.0',
    })
    if not response.ok:
        raise PackageNotFoundError(error_str)
    return response


def _get_pypi_package_project_data(package: str, session: Session | None= None) -> dict[Any, Any]:
    pkg_index = f"https://pypi.org/pypi/{package}/json"
    error_str = f"Package `{package}` was not found on PyPI"
    return _get_from_url(pkg_index, error_str, session=session).json()


def _get_versioned_pypi_package_data(
    package: str,
    version: str, *,
    session: Session | None = None
) -> dict[Any, Any]:
    pkg_index = f"https://pypi.org/pypi/{package}/{version}/json"
    error_str = f"Package `{package}` or version `{version}` was not found on PyPI"
    return _get_from_url(pkg_index, error_str, session=session).json()


def _get_metadata_file(pypi_pkg_data: dict[Any, Any], session: Session | None = None) -> str:
    error_str = "The metadata file could not be located"
    for entry in pypi_pkg_data["urls"]:
        if entry["packagetype"] == "bdist_wheel":
            try:
                response = _get_from_url(entry["url"] + ".metadata", error_str, session=session)
            except PackageNotFoundError as exc:
                raise CoreMetadataNotFoundError(error_str) from exc
            return response.text
    else:
        raise CoreMetadataNotFoundError(error_str)


def _find_available_versions(project_releases: dict) -> list[str]:
    available_versions = []
    for release in project_releases:
        available_versions.append(release)
    return available_versions


def _find_compatible_version(compat: str, available_versions: list[str]) -> str | None:
    compatible_versions = [v for v in available_versions if v.startswith(compat)]
    if not compatible_versions:
        raise CompatibleVersionNotFoundError(f"There's no version compatible with the requested: `{compat}`")
    return max(compatible_versions, key=Version)


def load_from_pypi(
    package: str, *,
    version: str | None = None,
    compat: str | None = None,
    session: Session | None= None
) -> dict[Any, Any]:

    if version is None:
        pypi_project_data = _get_pypi_package_project_data(package, session=session)
        # Looking for the latest version
        if compat is None:
            version = pypi_project_data["info"]["version"]
        # Looking for the latest version of the compat version line
        else:
            available_versions = _find_available_versions(pypi_project_data["releases"])
            version = _find_compatible_version(compat, available_versions)

    return _get_versioned_pypi_package_data(package, version=version, session=session)


def load_core_metadata_from_pypi(pypi_pkg_data: dict[Any, Any], session: Session | None = None) -> RawMetadata:
    metadata = _get_metadata_file(pypi_pkg_data, session=session)
    raw, _ = parse_email(metadata)
    # TODO: consider porting to packaging.Metadata instance?
    return raw
