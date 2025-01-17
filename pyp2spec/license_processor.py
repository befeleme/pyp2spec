from __future__ import annotations
from importlib.resources import files
from typing import Any
import json

from packaging.metadata import RawMetadata
from requests import Session
from license_expression import get_spdx_licensing, ExpressionError  # type: ignore

from pyp2spec.utils import Pyp2specError, filter_license_classifiers


TROVE2FEDORA_MAP: dict[str, str | None] = {}
FEDORA_LICENSES: dict[int, Any] = {}


class NoSuchClassifierError(Pyp2specError):
    """Raised when the detected license classifier doesn't exist in pyp2spec's data"""



def _load_package_resource(filename: str) -> dict[Any, Any]:
    with (files("pyp2spec") / filename).open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_from_drive(source_path: str) -> dict[Any, Any]:
    with open(source_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_from_url(url: str, session: Session | None=None) -> dict[Any, Any]:
    s = session or Session()
    response = s.get(url)
    response.raise_for_status()
    return response.json()


def classifiers_to_spdx_identifiers(classifiers: list) -> list | None:
    """Return the list of SPDX identifiers converted from the license classifiers.

    If the conversion of any of the classifiers is not possible, return None.
    Raise KeyError if the source data doesn't contain the found classifier.
    """

    if not TROVE2FEDORA_MAP:
        # Load the file with Python trove classifiers mapped to SPDX identifiers
        TROVE2FEDORA_MAP.update(_load_package_resource("classifiers_to_fedora.json"))

    spdx_identifiers = []
    for classifier in classifiers:
        try:
            fedora_identifier = TROVE2FEDORA_MAP[classifier]
        except KeyError as err:
            err_string = f"{classifier}: Such classifier doesn't exist. " \
            "If you believe that's pyp2spec's error, open an issue at the project's GitHub repo: " \
            "https://github.com/befeleme/pyp2spec"
            raise NoSuchClassifierError(err_string) from err

        # Classifiers that don't map unambiguously to a single Fedora SPDX expression are nulls
        # in the json
        # If the conversion is not possible, return None - meaning that another method of determining the license will be tried
        if fedora_identifier is None:
            return None
        spdx_identifiers.append(fedora_identifier)
    return spdx_identifiers


def license_keyword_to_spdx_identifiers(license_keyword: str | None) -> list | None:
    """Return a sorted list of SPDX identifiers extracted from the license_keyword
    
    If no identifiers were parsed out of the license_keyword or
    the license_keyword is unparseable, return None.
    """
    # nothing to transform, ergo no identifiers
    if not license_keyword:
        return None

    # `Artistic-1.0-Perl` alone is forbidden in Fedora, but the combination is allowed
    # These expressions may be a part of even longer license strings, which is impossible to cover
    # In an unlikely event of such license in the upstream data, raise an explicit exception
    special_cases = [
        "GPL-1.0-or-later OR Artistic-1.0-Perl",
        "GPL-2.0-or-later OR Artistic-1.0-Perl"
    ]
    for case in special_cases:
        if case in license_keyword:
            err_str = f"The detected license contains `{case}` which is handled in a special way in Fedora. " \
            "If you encountered this error, open an issue at https://github.com/befeleme/pyp2spec " \
            "and include the details about the package that causes the issue."
            raise NotImplementedError(err_str)

    licensing = get_spdx_licensing()
    try:
        parsed_license = licensing.parse(license_keyword, validate=True)
        # The objects are stored in sets, sort and return as a list
        return sorted(parsed_license.objects)
    except ExpressionError as err:
        # Don't bubble the error up, the calling function will handle the invalid result
        return None


def _load_fedora_licenses(
    source_path: str | None = None,
    session: Session | None = None
) -> dict[Any, Any]:
    """Load the dictionary of licenses evaluated for Fedora by the Fedora Legal team.

    Try to get them from the hard drive (installed by `fedora-license-data`).
    Fall back to the resources published by Fedora Legal online when the file isn't found.
    """

    fedora_licenses_path = source_path or "/usr/share/fedora-license-data/licenses/fedora-licenses.json"
    try:
        return _load_from_drive(fedora_licenses_path)

    except FileNotFoundError:
        url = "https://gitlab.com/fedora/legal/fedora-license-data/-/jobs/artifacts/main/raw/fedora-licenses.json?job=json"
        return _load_from_url(url, session=session)


def _is_compliant_with_fedora(identifier: str, fedora_licenses: dict[Any, Any]) -> bool:
    """Return True if the given identifier is "allowed" for Fedora and False if not.

    Fedora allows different types of licenses: "allowed for content", "allowed fonts",
    "allowed firmware", "allowed for documentation" and "allowed" for any use.
    For our purposes, only the generally "allowed" licenses are considered good.
    """

    # fedora_licenses doesn't have useful keys, hence iterate only through values
    # {"0": {
    #     "license": {
    #         "expression": "Rdisc",
    #         "status": ["allowed"],
    #         "url": "https://fedoraproject.org/wiki/Licensing/Rdisc_License"
    #     },
    #     "fedora": {
    #         "legacy-name": ["Rdisc License"],
    #         "legacy-abbreviation": ["Rdisc"]
    #     },
    #     "approved": "yes",
    #     "fedora_abbrev": "Rdisc",
    #     "fedora_name": "Rdisc License",
    #     "spdx_abbrev": "Rdisc"}...}

    for entry in fedora_licenses.values():
        license_info = entry.get("license")
        if license_info is not None:
            if identifier == entry["license"]["expression"]:
                return "allowed" in entry["license"]["status"]
    # No such identifier was found, we assume it's not good for Fedora
    return False


def check_compliance(
    license: str, *,
    licenses_dict: dict[Any, Any] | None = None,
    session: Session | None = None
) -> tuple[bool, dict[str, list[str]]]:

    """Determine whether the license is good for Fedora.

    Store the results in the checked_identifiers dictionary, under the
    respective `bad` and `good` keys.
    If no `spdx_identifiers` are given or not all are good, return tuple:
    (False, checked_identifies).
    Otherwise, return (True, checked_identifies).
    """

    # populate FEDORA_LICENSES only if they're still empty and
    # no other dictionary with licenses was given to be used here
    if licenses_dict is None and not FEDORA_LICENSES:
        FEDORA_LICENSES.update(_load_fedora_licenses(session=session))
    fedora_licenses = licenses_dict or FEDORA_LICENSES

    checked_identifies: dict[str, list[str]] = {
        "bad": [],
        "good": [],
    }

    spdx_identifiers = license_keyword_to_spdx_identifiers(license)
    if not spdx_identifiers:
        return (False, checked_identifies)
    for spdx_identifier in spdx_identifiers:
        if _is_compliant_with_fedora(spdx_identifier, fedora_licenses):
            checked_identifies["good"].append(spdx_identifier)
        else:
            checked_identifies["bad"].append(spdx_identifier)
    if checked_identifies["bad"]:
        return (False, checked_identifies)
    return (True, checked_identifies)


def transform_to_spdx(license_field: str | None, classifiers: list) -> tuple[list[str] | None, str | None]:
    """Return SPDX identifiers and expression based on the found
    package license metadata (classifiers or license keyword).

    If multiple identifiers are found, create an expression that's the safest option (with AND as joining operator).
    """

    if classifiers:
        identifiers = classifiers_to_spdx_identifiers(classifiers)
        if identifiers:
            expression = " AND ".join(identifiers)
            return (identifiers, expression)

    identifiers = license_keyword_to_spdx_identifiers(license_field)
    return (identifiers, license_field)


def generate_spdx_expression(license_field: str | None, classifiers: list) -> str | None:
    """Return the license expression based on detected metadata.

    If there are no identifiers, transformation to SPDX was unsuccessful.
    We don't want to process invalid license strings, so return None.
    Otherwise, we treat the expression as valid.
    """

    identifiers, expression = transform_to_spdx(license_field, classifiers)
    if not identifiers:
        return None
    return expression


def resolve_license_expression(data: RawMetadata | dict) -> str | None:
    if (expression := data.get("license_expression")):
        return expression
    return generate_spdx_expression(
        data.get("license"),
        filter_license_classifiers(data.get("classifiers", []))
    )
