"""
This module takes care of loading all sorts of data from PyPI APIs.
"""
from packaging.metadata import parse_email

import requests

from pyp2spec.utils import Pyp2specError


class PackageNotFoundError(Pyp2specError):
    """Raised when there's no such package name on PyPI"""


class CoreMetadataNotFoundError(Pyp2specError):
    """Raised when there's no Metadata file available on PyPI API"""


def _get_from_url(url, error_str, session=None):
    _session = session or requests.Session()
    response = _session.get(url)
    if not response.ok:
        raise PackageNotFoundError(error_str)
    return response


def _get_pypi_package_project_data(package, session=None):
    pkg_index = f"https://pypi.org/pypi/{package}/json"
    error_str = f"Package `{package}` was not found on PyPI"
    return _get_from_url(pkg_index, error_str, session=session).json()


def _get_versioned_pypi_package_data(package, version, *, session=None):
    pkg_index = f"https://pypi.org/pypi/{package}/{version}/json"
    error_str = f"Package `{package}` or version `{version}` was not found on PyPI"
    return _get_from_url(pkg_index, error_str, session=session).json()


def _get_metadata_file(pypi_pkg_data, session=None):
    error_str = "The metadata file could not be located"
    for entry in pypi_pkg_data["urls"]:
        if entry["packagetype"] == "bdist_wheel":
            try:
                response = _get_from_url(entry["url"] + ".metadata", error_str, session=session)
            except PackageNotFoundError:
                raise CoreMetadataNotFoundError(error_str)
            return response.text
    else:
        raise CoreMetadataNotFoundError(error_str)


def load_from_pypi(package, *, version=None, session=None):
    # Looking for the latest version
    if version is None:
        pypi_project_data = _get_pypi_package_project_data(package, session=session)
        version = pypi_project_data["info"]["version"]

    return _get_versioned_pypi_package_data(package, version=version, session=session)


def load_core_metadata_from_pypi(pypi_pkg_data, session=None):
    metadata = _get_metadata_file(pypi_pkg_data, session=session)
    raw, unparsed = parse_email(metadata)
    # in packaging <24.2 `unparsed` still contains 'license-file'
    # For pyp2spec it's ok to gather all unsupported fields and work with them later
    # TODO when F41 goes EOL:
    # - `raw` will be populated with all fields, drop `unparsed`
    # - consider porting to packaging.Metadata instance?
    raw.update(unparsed)
    return raw
