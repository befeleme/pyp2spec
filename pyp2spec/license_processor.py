from importlib.resources import open_text
import json

import requests
from license_expression import get_spdx_licensing, ExpressionError


TROVE2FEDORA_MAP = {}
FEDORA_LICENSES = {}


def _load_package_resource(filename):
    with open_text("pyp2spec", filename) as f:
        return json.load(f)


def _load_from_drive(source_path):
    with open(source_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_from_url(url, session=None):
    s = session or requests.Session()
    response = s.get(url)
    response.raise_for_status()
    return response.json()


def classifiers_to_spdx_identifiers(classifiers):
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
            raise KeyError(err_string) from err

        # Classifiers that don't map unambiguously to a single Fedora SPDX expression are nulls
        # in the json
        # If the conversion is not possible, return None - meaning that another method of determining the license will be tried
        if fedora_identifier is None:
            return None
        spdx_identifiers.append(fedora_identifier)
    return spdx_identifiers


def license_keyword_to_spdx_identifiers(license_keyword):
    """Return a sorted list of SPDX identifiers extracted from the license_keyword
    
    If no identifiers were parsed out of the license_keyword, return None.
    Raise ValueError if the license_keyword isn't a valid SPDX expression.
    """

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
        if parsed_license is None:  # license keyword is probably empty
            return None
        # The objects are stored in sets, sort and return as a list
        return sorted(parsed_license.objects)
    except ExpressionError as err:
        raise ValueError(f"Invalid SPDX expression: {license_keyword}") from err


def _load_fedora_licenses(source_path=None, session=None):
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


def _is_compliant_with_fedora(identifier, fedora_licenses):
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


def good_for_fedora(spdx_identifiers, *, licenses_dict=None, session=None):
    """Determine whether all of the given SPDX identifiers are good for Fedora.

    If no `spdx_identifiers` are given, return tuple: (False, []).
    If all of the given identifiers are good, return (True, []),
    otherwise return (False, [<all bad identifiers>]).
    bad_identifiers are returned in the same order as the given spdx_identifiers.
    """

    # populate FEDORA_LICENSES only if they're still empty and
    # no other dictionary with licenses was given to be used here
    if licenses_dict is None and not FEDORA_LICENSES:
        FEDORA_LICENSES.update(_load_fedora_licenses(session=session))
    fedora_licenses = licenses_dict or FEDORA_LICENSES

    if not spdx_identifiers:
        return (False, [])
    bad_identifiers = []
    for spdx_identifier in spdx_identifiers:
        if not _is_compliant_with_fedora(spdx_identifier, fedora_licenses):
            bad_identifiers.append(spdx_identifier)
    if bad_identifiers:
        return (False, bad_identifiers)
    return (True, [])
