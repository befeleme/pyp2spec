"""Test the functionality of functions getting the data from PyPI.
The data is downloaded and stored in betamax cassettes
to prevent loading from the internet on each request.
"""

import pytest

from pyp2spec.pypi_loaders import load_from_pypi, load_core_metadata_from_pypi
from pyp2spec.pypi_loaders import PackageNotFoundError, CompatibleVersionNotFoundError
from pyp2spec.pypi_loaders import _find_available_versions, _find_compatible_version


def test_load_from_pypi_no_version_given(betamax_session):
    result = load_from_pypi("Sphinx", session=betamax_session)
    assert result["info"]["version"] == "8.1.3"


def test_load_from_pypi_particular_version(betamax_session):
    result = load_from_pypi("Sphinx", version="7.3.7", session=betamax_session)
    assert result["info"]["version"] == "7.3.7"


def test_load_from_pypi_package_not_found(betamax_session):
    package = "non-existent-package"
    with pytest.raises(PackageNotFoundError):
        load_from_pypi(package, session=betamax_session)


def test_load_core_metadata(betamax_session):
    pypi_pkg_data = load_from_pypi("Sphinx", session=betamax_session)
    result = load_core_metadata_from_pypi(pypi_pkg_data, betamax_session)
    assert result["name"] == "Sphinx"
    assert result["version"] == "8.1.3"
    assert result["provides_extra"] == ["docs", "lint", "test"]



{"2.0.0":["..."],"2.0.1":["..."],"3.0.0":["..."],"6.0.1":["..."],"2.1.0":["..."],"2.1.1":["..."]}
def test_find_available_versions():
    releases = {
        "2.0.0":["..."],"2.0.1":["..."],"3.0.0":["..."],
        "6.0.1":["..."],"2.1.0":["..."],"2.1.1":["..."]
    }
    expected = ["2.0.0", "2.0.1", "3.0.0", "6.0.1", "2.1.0", "2.1.1"]
    assert _find_available_versions(releases) == expected


@pytest.mark.parametrize(
    ("compat", "available_versions", "expected"), [
        ("7", ["6.0.0", "7.0.0", "7.9.1"], "7.9.1"),
        ("7.4", ["7.4.2", "6.0.0", "7.4.3", "7.0.0", "7.0.1"], "7.4.3"),
        ("7.2", ["7.4.2", "7.2.3", "7.4.3", "6.0.0", "7.0.1"], "7.2.3"),
        ("7.4.2", ["7.4.2", "7.2.3", "7.4.3", "6.0.0", "7.0.1"], "7.4.2"),
    ]
)
def test_find_compatible_version(compat, available_versions, expected):
    assert _find_compatible_version(compat, available_versions) == expected


def test_no_compatible_version_available():
    with pytest.raises(CompatibleVersionNotFoundError):
        _find_compatible_version("9", ["6.0.0", "7.0.0", "7.9.1"])
