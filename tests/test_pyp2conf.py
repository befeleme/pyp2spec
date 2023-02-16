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
from pyp2spec.pyp2conf import convert_version_to_rpm_scheme


@pytest.fixture
def changelog():
    return ("Wed Nov 03 2021", "Packager", "packager@maint.com")


@pytest.mark.parametrize("package, version",
    [
        ("aionotion", "2.0.3"),
        ("click", "7.1.2"),
    ]
)
def test_automatically_generated_config_is_valid(betamax_parametrized_session, changelog, package, version):
    """Run the config rendering in fully automated mode and compare the results"""
    config = create_config_contents(
        package=package,
        version=version,
        date=changelog[0],
        name=changelog[1],
        email=changelog[2],
        session=betamax_parametrized_session,
    )

    with open(f"tests/test_configs/default_python-{package}.conf", "rb") as config_file:
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
        description="A asyncio-friendly library for Notion Home Monitoring devices.\n",
        release="4",
        message="Rebuilt for Python 3.10",
        email="package@manager.com",
        name="Package Manager",
        version="2.0.3",
        summary="Python library for Notion Home Monitoring",
        date="Fri Jun 04 2021",
        top_level=True,
        compliant=True,
        session=betamax_session,
    )

    with open(f"tests/test_configs/customized_{package}.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config == loaded_contents


def test_archful_package(betamax_session, changelog):
    """Generate config for tornado which is archful"""
    package = "tornado"
    config = create_config_contents(
        package=package,
        date=changelog[0],
        name=changelog[1],
        email=changelog[2],
        top_level=True,
        license="Apache 2.0",
        archful=True,
        session=betamax_session,
    )

    with open(f"tests/test_configs/customized_{package}.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config["archful"] == loaded_contents["archful"]


def test_license_classifier_read_correctly():
    fake_pkg_data = {"info":{"classifiers": [
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: MIT No Attribution License (MIT-0)",
        "Development Status :: 3 - Alpha",
    ]}}

    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    assert pkg.filter_license_classifiers() == [
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: MIT No Attribution License (MIT-0)"
    ]


def test_no_license_classifiers_and_no_license_keyword():
    pkg = PypiPackage("_", package_metadata={"info":{"classifiers": []}})
    assert pkg.filter_license_classifiers() == []
    with pytest.raises(SystemExit):
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

    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    assert pkg.license(check_compliance=True, licenses_dict=fake_fedora_licenses) == "MIT AND MIT-0"


def test_bad_license_fails_compliance_check(fake_fedora_licenses):
    fake_pkg_data = {"info": {"classifiers" : [
        "License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)"
    ]}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)

    with pytest.raises(SystemExit):
        pkg.license(check_compliance=True, licenses_dict=fake_fedora_licenses)


def test_bad_license_without_compliance_check_is_returned():
    fake_pkg_data = {"info": {"classifiers" : [
        "License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)"
    ]}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)

    assert pkg.license(check_compliance=False) == "EUPL-1.0"


def test_mix_good_bad_licenses_fail_compliance_check(fake_fedora_licenses):
    fake_pkg_data = {"info": {"classifiers" : [
        "License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)",
        "License :: OSI Approved :: MIT License",
    ]}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    with pytest.raises(SystemExit):
        pkg.license(check_compliance=True, licenses_dict=fake_fedora_licenses)


def test_mix_good_bad_licenses_without_compliance_check_are_returned():
    fake_pkg_data = {"info": {"classifiers" : [
        "License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)",
        "License :: OSI Approved :: MIT License",
    ]}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    assert pkg.license(check_compliance=False) == "EUPL-1.0 AND MIT"


def test_license_keyword_without_compliance_check():
    fake_pkg_data = {"info": {"license": "BSD-2-Clause", "classifiers": []}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    assert pkg.license(check_compliance=False) == "BSD-2-Clause"


def test_license_keyword_with_compliance_check(fake_fedora_licenses):
    fake_pkg_data = {"info": {"license": "RSCPL", "classifiers": []}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    with pytest.raises(SystemExit):
        pkg.license(check_compliance=True, licenses_dict=fake_fedora_licenses)


@pytest.mark.parametrize("compliant", (True, False))
def test_multiline_license_keyword_fails(compliant, fake_fedora_licenses):
    fake_pkg_data = {"info": {"license": "This is absolutely\nhorrible\nidea\nto\ndo..."}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    with pytest.raises(SystemExit):
        pkg.license(check_compliance=compliant, licenses_dict=fake_fedora_licenses)


@pytest.mark.parametrize("compliant", (True, False))
def test_empty_license_keyword_fails(compliant, fake_fedora_licenses):
    fake_pkg_data = {"info": {"license": "", "classifiers": []}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    with pytest.raises(SystemExit):
        pkg.license(check_compliance=compliant, licenses_dict=fake_fedora_licenses)


def test_nonexisting_classifiers():
    fake_pkg_data = {"info": {"classifiers": ["License :: OSI Approved :: XXXXXX"]}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    with pytest.raises(SystemExit):
        pkg.license()


def test_zip_sdist_is_added_to_source_macro():

    fake_pkg_data = {
        "releases": {
            "1.2.3": [{
                "filename": "Awesome_TestPkg-1.2.3.zip",
                "packagetype": "sdist"}]
                },
        "info": {"version": "1.2.3"}
    }
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    version = pkg.version()
    assert pkg.source(version) == "%{pypi_source Awesome_TestPkg %{version} zip}"


def test_no_homepage_in_metadata():
    fake_pkg_data = {"info": {"package_url": "https://foo"}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    assert pkg.project_url() == "https://foo"


def test_summary_is_generated_if_not_in_upstream():
    fake_pkg_data = {"info": {"summary": ""}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    assert pkg.summary() == "..."


def test_summary_is_generated_if_upstream_data_is_multiline():
    fake_pkg_data = {"info": {"summary": "I\nforgot\nthat summary\nmust\nbe short"}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    assert pkg.summary() == "..."


def test_capitalized_underscored_pypi_name_is_normalized():
    fake_pkg_data = {"info": {"name": "Awesome_TestPkg"}}
    pkg = PypiPackage("Awesome_TestPkg", package_metadata=fake_pkg_data)
    assert pkg.pypi_name == "awesome-testpkg"
    assert pkg.python_name() == "python-awesome-testpkg"


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
    fake_pkg_data = {"info": {"version": pypi_version}}
    pkg = PypiPackage("_", package_metadata=fake_pkg_data)
    assert pkg.pypi_version_or_macro(pypi_version) == pypi_version_macro
