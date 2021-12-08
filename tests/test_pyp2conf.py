import betamax
import click
import pytest
import tomli

from pyp2spec.pyp2conf import PypiPackage, create_config_contents


with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'tests/fixtures/cassettes'


@pytest.fixture
def changelog():
    return ("Wed Nov 03 2021", "Packager", "packager@maint.com")


@pytest.mark.parametrize("package, version",
    [
        ("aionotion", "2.0.3"),
        ("aioflo", "0.4.2"),
        ("click", "7.1.2"),
        ("jupyter-packaging", "0.10.4"),
        ("markdown-it-py", "1.1.0"),
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
        loaded_contents = tomli.load(config_file)

    assert config == loaded_contents


def test_config_with_customization_is_valid(betamax_session):
    """Get the upstream metadata and modify some fields to get the custom config file.
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
        session=betamax_session,
    )

    with open(f"tests/test_configs/customized_{package}.conf", "rb") as config_file:
        loaded_contents = tomli.load(config_file)

    assert config == loaded_contents


def test_license_classifier_read_correctly(betamax_session):
    pkg = PypiPackage("tomli", session=betamax_session)
    assert pkg.read_license_classifiers() == ['License :: OSI Approved :: MIT License']


def test_no_license_classifiers_and_no_license_keyword(betamax_session):
    pkg = PypiPackage("tomli", session=betamax_session)
    pkg.package_data["info"]["classifiers"] = []
    assert pkg.read_license_classifiers() == []
    with pytest.raises(SystemExit):
        pkg.license()


def test_compliant_license_is_returned(betamax_session):
    pkg = PypiPackage("tomli", session=betamax_session)
    pkg.classifiers = pkg.read_license_classifiers()
    assert pkg.get_license_from_classifiers(compliant=True) == "MIT"


def test_bad_license_if_compliant_is_not_returned(betamax_session):
    pkg = PypiPackage("tomli", session=betamax_session)
    pkg.classifiers = ["License :: Eiffel Forum License (EFL)"]
    with pytest.raises(SystemExit):
        pkg.get_license_from_classifiers(compliant=True)


def test_bad_license_if_not_compliant_is_returned(betamax_session):
    pkg = PypiPackage("tomli", session=betamax_session)
    pkg.classifiers = ["License :: Eiffel Forum License (EFL)"]
    pkg.get_license_from_classifiers(compliant=False) == "EFL"


def test_mix_non_compliant_licenses_wont_work_if_strict(betamax_session):
    pkg = PypiPackage("tomli", session=betamax_session)
    pkg.classifiers = [
        "License :: Eiffel Forum License (EFL)",
        "License :: OSI Approved :: MIT License",
    ]
    with pytest.raises(SystemExit):
        pkg.get_license_from_classifiers(compliant=True)


def test_mix_non_compliant_licenses_work_if_not_strict(betamax_session):
    pkg = PypiPackage("tomli", session=betamax_session)
    pkg.classifiers = [
        "License :: Eiffel Forum License (EFL)",
        "License :: OSI Approved :: MIT License",
    ]
    pkg.get_license_from_classifiers(compliant=False) == "EFL and MIT"


@pytest.mark.parametrize("compliant", (True, False))
def test_OSI_Approved_is_ignored(betamax_session, compliant):
    pkg = PypiPackage("tomli", session=betamax_session)
    pkg.classifiers = [
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved",
    ]
    pkg.get_license_from_classifiers(compliant) == "MIT"


def test_zip_sdist_is_added_to_source_macro(betamax_session):
    pkg = PypiPackage("azure-common", session=betamax_session)
    version = pkg.version()
    assert pkg.source_url(version) == "%{pypi_source azure-common zip}"
