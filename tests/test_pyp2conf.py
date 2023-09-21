"""Test the functionality of pyp2conf part of the tool.
The data is downloaded from the PyPI and stored in betamax casettes
to prevent loading from the internet on each request.
"""
import pytest

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from pyp2spec.pyp2conf import PypiPackage, create_config_contents
from pyp2spec.pyp2conf import convert_version_to_rpm_scheme, NoLicenseDetectedError, PackageNotFoundError


def test_non_existent_package(betamax_session):
    with pytest.raises(PackageNotFoundError):
        PypiPackage("definitely-nonexisting-package-name", session=betamax_session)


@pytest.mark.parametrize("package, version",
    [
        ("aionotion", "2.0.3"),
        ("click", "7.1.2"),
    ]
)
def test_automatically_generated_config_is_valid(betamax_parametrized_session, package, version):
    """Run the config rendering in fully automated mode and compare the results"""
    config = create_config_contents(
        package=package,
        version=version,
        session=betamax_parametrized_session,
    )

    with open(f"tests/test_configs/default_python-{package}.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config == loaded_contents


@pytest.mark.parametrize("package, version, alt_python",
    [
        ("Pello", "1.0.4", "3.9"),
    ]
)
def test_automatically_generated_config_with_alt_python_is_valid(
        betamax_parametrized_session, package, version, alt_python
    ):
    """Run the config rendering in fully automated mode and compare the results"""
    config = create_config_contents(
        package=package,
        version=version,
        python_alt_version=alt_python,
        session=betamax_parametrized_session,
    )

    with open(f"tests/test_configs/default_python{alt_python}-{package.lower()}.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config == loaded_contents


def test_config_with_customization_is_valid(betamax_session):
    """Get the upstream metadata and modify some fields to get the custom config file.
    This also tests the compliance with Fedora Legal data by making
    a request to the remote resource.
    """
    package = "aionotion"
    config = create_config_contents(
        package=package,
        version="2.0.3",
        automode=True,
        compliant=True,
        session=betamax_session,
    )

    with open(f"tests/test_configs/customized_{package}.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config == loaded_contents


def test_archful_package(betamax_session):
    """Generate config for numpy which is archful"""
    package = "numpy"
    config = create_config_contents(
        package=package,
        license="fake-string",
        version="1.25.2",
        automode=True,
        session=betamax_session,
    )

    with open(f"tests/test_configs/default_python-{package}.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config["archful"] == loaded_contents["archful"]


def test_package_with_extras(betamax_session):
    package = "sphinx"
    config = create_config_contents(
        package=package,
        license="fake-license",
        session=betamax_session,
    )

    with open(f"tests/test_configs/customized_python-{package}.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config["extras"] == loaded_contents["extras"]


def test_license_classifier_read_correctly():
    fake_pkg_data = {"info":{"classifiers": [
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: MIT No Attribution License (MIT-0)",
        "Development Status :: 3 - Alpha",
    ]}}

    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    assert pkg.filter_license_classifiers() == [
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: MIT No Attribution License (MIT-0)"
    ]


def test_no_license_classifiers_and_no_license_keyword():
    pkg = PypiPackage("_", version="1.2.3", package_metadata={"info":{"classifiers": [], "license": ""}})
    assert pkg.filter_license_classifiers() == []
    with pytest.raises(NoLicenseDetectedError):
        pkg.license()


def test_compliant_license_is_returned(fake_fedora_licenses):
    fake_pkg_data = {"info": {"classifiers" : [
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: MIT No Attribution License (MIT-0)",
        "Development Status :: 3 - Alpha",
    ]}}

    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    assert pkg.license(check_compliance=True, licenses_dict=fake_fedora_licenses) == "MIT AND MIT-0"


def test_bad_license_fails_compliance_check(fake_fedora_licenses):
    fake_pkg_data = {"info": {"classifiers" : [
        "License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)"
    ]}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)

    with pytest.raises(NoLicenseDetectedError):
        pkg.license(check_compliance=True, licenses_dict=fake_fedora_licenses)


def test_bad_license_without_compliance_check_is_returned():
    fake_pkg_data = {"info": {"classifiers" : [
        "License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)"
    ]}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)

    assert pkg.license(check_compliance=False) == "EUPL-1.0"


def test_mix_good_bad_licenses_fail_compliance_check(fake_fedora_licenses):
    fake_pkg_data = {"info": {"classifiers" : [
        "License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)",
        "License :: OSI Approved :: MIT License",
    ]}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    with pytest.raises(NoLicenseDetectedError):
        pkg.license(check_compliance=True, licenses_dict=fake_fedora_licenses)


def test_mix_good_bad_licenses_without_compliance_check_are_returned():
    fake_pkg_data = {"info": {"classifiers" : [
        "License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)",
        "License :: OSI Approved :: MIT License",
    ]}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    assert pkg.license(check_compliance=False) == "EUPL-1.0 AND MIT"


def test_license_keyword_without_compliance_check():
    fake_pkg_data = {"info": {"license": "BSD-2-Clause", "classifiers": []}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    assert pkg.license(check_compliance=False) == "BSD-2-Clause"


def test_license_keyword_with_compliance_check(fake_fedora_licenses):
    fake_pkg_data = {"info": {"license": "RSCPL", "classifiers": []}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    with pytest.raises(NoLicenseDetectedError):
        pkg.license(check_compliance=True, licenses_dict=fake_fedora_licenses)


@pytest.mark.parametrize("compliant", (True, False))
def test_empty_license_keyword_fails(compliant, fake_fedora_licenses):
    fake_pkg_data = {"info": {"license": "", "classifiers": []}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    with pytest.raises(NoLicenseDetectedError):
        pkg.license(check_compliance=compliant, licenses_dict=fake_fedora_licenses)


def test_zip_sdist_is_added_to_source_macro():

    fake_pkg_data = {
        "urls": [{
            "filename": "Awesome_TestPkg-1.2.3.zip",
            "packagetype": "sdist",
        }],
    }
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    assert pkg.source() == "%{pypi_source Awesome_TestPkg %{version} zip}"


def test_no_homepage_in_metadata():
    fake_pkg_data = {"info": {"package_url": "https://foo"}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    assert pkg.project_url() == "https://foo"


def test_summary_is_generated_if_not_in_upstream():
    fake_pkg_data = {"info": {"summary": ""}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    assert pkg.summary() == "..."


def test_summary_is_generated_if_upstream_data_is_multiline():
    fake_pkg_data = {"info": {"summary": "I\nforgot\nthat summary\nmust\nbe short"}}
    pkg = PypiPackage("_", version="1.2.3", package_metadata=fake_pkg_data)
    assert pkg.summary() == "..."


def test_capitalized_underscored_pypi_name_is_normalized():
    fake_pkg_data = {"info": {"name": "Awesome_TestPkg"}}
    pkg = PypiPackage("Awesome_TestPkg", version="1.2.3",package_metadata=fake_pkg_data)
    assert pkg.pypi_name == "awesome-testpkg"
    assert pkg.python_name() == "python-awesome-testpkg"


@pytest.mark.parametrize(
    ("pypi_name", "alt_version", "expected"), [
        ("foo", "3.10", "python3.10-foo"),
        ("python-foo", "3.9", "python3.9-foo"),
        ("python_foo", "3.12", "python3.12-foo"),
        ("foo", None, "python-foo"),
        ("python-foo", None, "python-foo"),
        ("python_foo", None, "python-foo"),
    ]
)
def test_python_name(pypi_name, alt_version, expected):
    fake_pkg_data = {"info": {"name": pypi_name}}
    pkg = PypiPackage(pypi_name, version="1.2.3", package_metadata=fake_pkg_data)
    assert pkg.python_name(python_alt_version=alt_version) == expected


@pytest.mark.parametrize(
    ("pypi_version", "rpm_version"), [
        ("1.1.0", "1.1.0"),
        ("1!0.2.13", "1:0.2.13"),
        ("0.0.2-beta1", "0.0.2~b1"),
        ("0.5.40-0", "0.5.40^post0"),
    ]
)
def test_pypi_version_is_converted_to_rpm(pypi_version, rpm_version):
    assert convert_version_to_rpm_scheme(pypi_version) == rpm_version


@pytest.mark.parametrize(
    ("pypi_version", "pypi_version_macro"), [
        ("1.1.0", "%{version}"),  # conversion to RPM doesn't change the string
        ("1!0.2.13", "1!0.2.13"),  # Version string is normalized, see previous test
        ("0.0.2-beta1", "0.0.2-beta1"),
        ("0.5.40-0", "0.5.40-0"),
    ]
)
def test_pypi_version_or_macro(pypi_version, pypi_version_macro):
    # to prevent tests sending requests to PyPI
    fake_pkg_data = {
        "info": "intentionally not empty package metadata"
    }
    pkg = PypiPackage("_", version=pypi_version, package_metadata=fake_pkg_data)
    assert pkg.pypi_version_or_macro() == pypi_version_macro


def test_extras_detected_correctly():
    fake_pkg_data = {
        "info": {
            "requires_dist": [
                "foo ; platform_system == 'Windows'",
                "bar ; python_version < '3.8'",
                "baz",
                "foobar ; extra == 'docs'",
                "foobaz>=5.3.1",
                "spam>=3.5.0 ; extra == 'lint'",
                "ham[eggs]>=0.10; extra == 'test'",
                "eggs>=2.12; implementation_name != 'pypy' and extra == 'dev'",
            ]
        }
    }
    pkg = PypiPackage("_", version="0", package_metadata=fake_pkg_data)
    assert pkg.extras() == ["dev", "docs", "lint", "test"]


@pytest.mark.parametrize(
    ("wheel_name", "archful"), [
        ("sampleproject-3.0.0-py3-none-any.whl", False),
        ("numpy-1.26.0-cp39-cp39-win_amd64.whl", True),
        ("numpy-1.26.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", True),
        ("numpy-1.26.0-cp39-cp39-musllinux_1_1_x86_64.whl", True),
    ]
)
def test_archfulness_is_detected(wheel_name, archful):
    fake_pkg_data = {
        "urls": [
            {
                "packagetype": "bdist_wheel",
                "filename": wheel_name,
            }
        ]
    }
    pkg = PypiPackage("_", version="0", package_metadata=fake_pkg_data)
    assert pkg.is_archful() is archful


def test_archfulness_is_detected_from_multiple_urls_1():
    fake_pkg_data = {
        "urls": [
            {
                "packagetype": "sdist",
                "filename": "sampleproject-3.0.0.tar.gz",
            },
            {
                "packagetype": "bdist_wheel",
                "filename": "sampleproject-3.0.0-py3-none-any.whl",
            },
        ]
    }
    pkg = PypiPackage("_", version="0", package_metadata=fake_pkg_data)
    assert not pkg.is_archful()


def test_archfulness_is_detected_from_multiple_urls_2():
    fake_pkg_data = {
        "urls": [
            {
                "packagetype": "bdist_wheel",
                "filename": "sampleproject-3.0.0-py3-none-any.whl",
            },
            {
                "packagetype": "bdist_wheel",
                "filename": "sampleproject-3.0.0-cp312-abi3-manylinux1_x86_64.whl",
            },

        ]
    }
    pkg = PypiPackage("_", version="0", package_metadata=fake_pkg_data)
    assert pkg.is_archful()


def test_archfulness_is_detected_from_multiple_urls_3():
    fake_pkg_data = {
        "urls": [
            {
                "packagetype": "bdist_wheel",
                "filename": "sampleproject-3.0.0-cp312-abi3-manylinux1_x86_64.whl",
            },
            {
                "packagetype": "bdist_wheel",
                "filename": "sampleproject-3.0.0-cp39-cp39-win_amd64.whl",
            },
            {
                "packagetype": "bdist_wheel",
                "filename": "sampleproject-3.0.0-py3-none-any.whl",
            },
        ]
    }
    pkg = PypiPackage("_", version="0", package_metadata=fake_pkg_data)
    assert pkg.is_archful()
