import pytest

from pyp2spec.license_processor import classifiers_to_spdx_identifiers, license_keyword_to_spdx_identifiers
from pyp2spec.license_processor import _is_compliant_with_fedora, good_for_fedora


@pytest.mark.parametrize(
    ("classifiers", "spdx_identifiers"),
    (
        (["License :: OSI Approved :: X.Net License"], ["Xnet"]),  # good
        (["License :: OSI Approved :: X.Net License", "License :: OSI Approved :: Artistic License"], None),  # good & bad
        (["License :: OSI Approved :: Artistic License"], None),  # bad
        (["License :: OSI Approved :: Eiffel Forum License", "License :: OSI Approved :: GNU General Public License (GPL)"], None),  # bad & bad
        (["License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)", "License :: OSI Approved :: ISC License (ISCL)"], ["LGPL-3.0-or-later", "ISC"]),  # good & good
    ),
)
def test_classifiers_to_spdx_identifiers(classifiers, spdx_identifiers):
    assert classifiers_to_spdx_identifiers(classifiers) == spdx_identifiers


@pytest.mark.parametrize(
    ("classifiers"),  (
        ["Non-existing-classifier"],
        [""]
    ),
)
def test_conversion_to_spdx_fails_for_invalid_inputs(classifiers):
    with pytest.raises(KeyError):
        classifiers_to_spdx_identifiers(classifiers)


@pytest.mark.parametrize(
    ("expression", "expected"),
    (
        ("LGPL-2.1-only AND MIT AND BSD-2-Clause", ['BSD-2-Clause', 'LGPL-2.1-only', 'MIT']),
        ("MIT AND (LGPL-2.1-or-later OR BSD-3-Clause)", ['BSD-3-Clause', 'LGPL-2.1-or-later', 'MIT']),
        ("(MIT AND (LGPL-2.1+ AND BSD-3-Clause))", ['BSD-3-Clause', 'LGPL-2.1-or-later', 'MIT']),
        ("GPL-3.0-or-later WITH GCC-exception-3.1", ["GPL-3.0-or-later WITH GCC-exception-3.1"]),
        ("GPL-3.0-or-later WITH GCC-exception-3.1 OR Apache-2.0 OR MPL-2.0", ["Apache-2.0", "GPL-3.0-or-later WITH GCC-exception-3.1", "MPL-2.0"]),
        ("", None),
    ),
)
def test_split_expressions_to_identifiers(expression, expected):
    assert license_keyword_to_spdx_identifiers(expression) == expected


def test_perl_license_raises_exception():
    with pytest.raises(NotImplementedError):
        license_keyword_to_spdx_identifiers("MPL-2.0 OR GPL-2.0-or-later OR Artistic-1.0-Perl AND BSD-3-Clause")


@pytest.mark.parametrize(
    ("expression"),
    (
        ("FOO AND bar OR baz WITH EXCEPTION"),
        ("an arbitrary string"),
        ("multiline\nstring"),
        ("BSD BSD AND BSD"),
        ("string"),
    ),
)
def test_invalid_expressions_raise_errors(expression):
    with pytest.raises(ValueError):
        license_keyword_to_spdx_identifiers(expression)



@pytest.mark.parametrize(
    ("identifier", "expected"),
    (
        ("CECILL-C", True),
        ("GPL-3.0-or-later WITH Classpath-exception-2.0", True),
        ("GPL-3.0-or-later WITH GCC-exception-3.1", True),
        ("CC0-1.0", False),  # allowed content license
        ("LicenseRef-LPPL", False),  # allowed font license
        ("EUPL-1.0", False),  # not allowed at all
        ("Bitstream-Vera", False),  # existing SPDX identifiers, but missing in fake_fedora_licenses
    )
)
def test_compliance_check_with_fedora(identifier, expected, fake_fedora_licenses):
    assert _is_compliant_with_fedora(identifier, fake_fedora_licenses) is expected


@pytest.mark.parametrize(
    ("identifiers", "expected"),
    (
        (["AAL", "MIT", "CECILL-B"], (True, [])),
        ([], (False, [])),
        (["LicenseRef-LPPL", "MIT"], (False, ["LicenseRef-LPPL"])),  # mixed not allowed/allowed
        (["LicenseRef-LPPL", "Aladdin", "LicenseRef-OpenFlow", "APL-1.0"], (False, ["LicenseRef-LPPL", "Aladdin", "LicenseRef-OpenFlow", "APL-1.0"])),
    ),
)
def test_is_allowed_in_fedora(identifiers, expected, fake_fedora_licenses):
    """Test the function logic, bear in mind that Fedora status may change in time"""

    assert good_for_fedora(identifiers, licenses_dict=fake_fedora_licenses) == expected
