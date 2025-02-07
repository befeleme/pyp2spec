"""
This module takes care of loading all sorts of data from PyPI APIs.
"""
from __future__ import annotations
from typing import Any

from packaging.metadata import parse_email, RawMetadata
from requests import Response, Session

from pyp2spec.utils import Pyp2specError


class PackageNotFoundError(Pyp2specError):
    """Raised when there's no such package name on PyPI"""


class CoreMetadataNotFoundError(Pyp2specError):
    """Raised when there's no Metadata file available on PyPI API"""


def _get_from_url(url: str, error_str: str, session: Session | None = None) -> Response:
    _session = session or Session()
    response = _session.get(url)
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


def load_from_pypi(
    package: str, *,
    version: str | None = None,
    session: Session | None= None
) -> dict[Any, Any]:
    # Looking for the latest version
    if version is None:
        pypi_project_data = _get_pypi_package_project_data(package, session=session)
        version = pypi_project_data["info"]["version"]

    return _get_versioned_pypi_package_data(package, version=version, session=session)


def load_core_metadata_from_pypi(pypi_pkg_data: dict[Any, Any], session: Session | None = None) -> RawMetadata:
    metadata = _get_metadata_file(pypi_pkg_data, session=session)
    raw, _ = parse_email(metadata)
    # TODO: consider porting to packaging.Metadata instance?
    return raw
