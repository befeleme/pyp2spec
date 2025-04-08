"""Test the functionality of pyp2conf part of the tool.
The data is downloaded from the PyPI and stored in betamax cassettes
to prevent loading from the internet on each request.
"""
import pytest

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from pyp2spec.pyp2conf import create_config_contents, prepare_package_info, check_compliance
from pyp2spec.pyp2conf import gather_package_info, create_package_from_pypi, create_package_from_dir
from pyp2spec.pypi_loaders import PackageNotFoundError


def test_non_existent_package(betamax_session):
    with pytest.raises(PackageNotFoundError):
        create_config_contents(
            {"package": "definitely-nonexisting-package-name"},
            session=betamax_session)


@pytest.mark.parametrize("package, version",
    [
        ("aionotion", "2.0.3"),
        ("click", "8.1.7"),
    ]
)
def test_automatically_generated_config_is_valid(betamax_parametrized_session, package, version):
    """Run the config rendering in fully automated mode and compare the results"""
    config = create_config_contents(
        {"package": package,
        "version": version},
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
        {"package": package,
        "version": version,
        "python_alt_version": alt_python},
        session=betamax_parametrized_session,
    )

    with open(f"tests/test_configs/default_python{alt_python}-{package.lower()}.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config == loaded_contents


@pytest.mark.parametrize("package, compat, version",
    [
        ("pytest", "7", None),
        ("pytest", "7.2", "7.2.1")  # not the first, nor latest
    ]
)
def test_automatically_generated_compat_config_is_valid(
        betamax_parametrized_session, package, compat, version
    ):
    config = create_config_contents(
        {"package": package,
        "version": version,
        "compat": compat},
        session=betamax_parametrized_session,
    )

    with open(f"tests/test_configs/default_python-{package}{compat}.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)
    assert config["compat"] == compat
    assert config == loaded_contents


def test_config_with_customization_is_valid(betamax_session):
    """Get the upstream metadata and modify some fields to get the custom config file.
    This also tests the compliance with Fedora Legal data by making
    a request to the remote resource.
    """
    config = create_config_contents(
        {"package": "aionotion",
        "version": "2.0.3",
        "automode": True,
        "compliant": True},
        session=betamax_session,
    )

    with open(f"tests/test_configs/customized_aionotion.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config == loaded_contents


def test_config_from_local_path_is_valid():
    """Get the metadata from locally stored wheel and sdist
    """
    config = create_config_contents(
        {"package": "local_test",
        "path": "tests/local"},
    )

    with open(f"tests/test_configs/default_python-local-test.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)
    # Replace the detected value, we don't want to compare the real one
    config["archive_name"] = "..."
    assert config == loaded_contents


def test_archful_package(betamax_session):
    """Generate config for numpy which is archful"""
    config = create_config_contents(
        {"package": "numpy",
        "version": "1.25.2",
        "automode": True},
        session=betamax_session,
    )

    with open(f"tests/test_configs/default_python-numpy.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config["archful"] == loaded_contents["archful"]
    assert config == loaded_contents


def test_package_with_extras(betamax_session):
    config = create_config_contents(
        {"package": "sphinx"},
        session=betamax_session,
    )

    with open(f"tests/test_configs/customized_python-sphinx.conf", "rb") as config_file:
        loaded_contents = tomllib.load(config_file)

    assert config["extras"] == loaded_contents["extras"]
    assert config == loaded_contents


def test_no_license_classifiers_and_no_license_keyword():
    fake_pkg_data = {
        "name": "foo",
        "classifiers": [],
        "license_keyword": "",
    }
    pkg = prepare_package_info(fake_pkg_data)
    assert pkg.license is None


def test_license_expression_takes_precedence(fake_fedora_licenses):
    fake_pkg_data = {
        "name": "foo",
        "classifiers": ["License :: OSI Approved :: MIT License"],
        "license_keyword": "MIT-0",
        "license_expression": "BSD-2-Clauseo",
    }
    pkg = prepare_package_info(fake_pkg_data)
    assert pkg.license == "BSD-2-Clauseo"
    result, identifiers = check_compliance(pkg.license, licenses_dict=fake_fedora_licenses)
    assert not result
    assert not identifiers["good"]
    # There are none valid identifiers
    assert not identifiers["bad"]


def test_mix_good_bad_licenses_fail_compliance_check(fake_fedora_licenses):
    fake_pkg_data = {
        "name": "foo",
        "classifiers": [
            "License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)",
            "License :: OSI Approved :: MIT License"
        ],
    }
    pkg = prepare_package_info(fake_pkg_data)
    assert pkg.license == "EUPL-1.0 AND MIT"
    result, identifiers = check_compliance(pkg.license, licenses_dict=fake_fedora_licenses)
    assert not result
    assert identifiers["good"] == ["MIT"]
    assert identifiers["bad"] == ["EUPL-1.0"]


def test_summary_is_generated_if_not_in_upstream():
    fake_pkg_data = {
        "name": "foo",
        "summary": "",
    }
    pkg = prepare_package_info(fake_pkg_data)
    assert pkg.summary == "..."


def test_summary_is_generated_if_upstream_data_is_multiline():
    fake_pkg_data = {
        "name": "foo",
        "summary": "I\nforgot\nthat summary\nmust\nbe short",
    }
    pkg = prepare_package_info(fake_pkg_data)
    assert pkg.summary == "..."


def test_capitalized_underscored_pypi_name_is_normalized():
    fake_pkg_data = {
        "name": "Awesome_TestPkg",
    }
    pkg = prepare_package_info(fake_pkg_data)
    assert pkg.pypi_name == "awesome-testpkg"


@pytest.mark.parametrize(
    ("metadata", "lf_present"), [
        (["License.rst"], True),
        (["License.rst", "License.md"], True),
        ([], False),
    ]
)
def test_license_files_in_metadata_files(metadata, lf_present):
    fake_pkg_data = {
        "name": "foo",
        "license_files": metadata,
    }
    pkg = prepare_package_info(fake_pkg_data)
    assert pkg.license_files_present is lf_present


def test_prepare_package_info_pypi_source():
    data = {"info": {
        "name": "example",
        "summary": "A sample project",
        "license_expression": "MIT",
        "license": "MIT License",
        "classifiers": ["License :: OSI Approved :: MIT License"],
        "requires_dist": ["requests"],
        "version": "1.0.0",
        "license_files": ["LICENSE"],
        "project_urls": {"Homepage": "https://example.com"},
        "yanked": False,
        "maintainer": "John Doe",
    }, "releases": [],}
    result = prepare_package_info(data["info"])
    assert result.pypi_name == "example"
    assert result.summary == "A sample project"
    assert result.license_files_present is True
    assert result.license == "MIT"
    assert result.extras == []
    assert result.pypi_version == "1.0.0"
    assert result.url == "https://example.com"


def test_prepare_package_info_core_metadata():
    data = {
        "name": "example",
        "summary": "A sample project",
        "license_expression": "MIT",
        "license": "MIT License",
        "classifiers": ["License :: OSI Approved :: MIT License"],
        "requires_dist": ["requests"],
        "version": "1.0.0",
        "license_files": ["LICENSE"],
        "home_page": "https://example.com",
        "metadata_version": "2.1",
    }
    result = prepare_package_info(data)
    assert result.pypi_name == "example"
    assert result.summary == "A sample project"
    assert result.license_files_present is True
    assert result.license == "MIT"
    assert result.extras == []
    assert result.pypi_version == "1.0.0"
    assert result.url == "https://example.com"


def test_prepare_package_info_missing_keys():
    data = {
        "name": "foo",
    }
    result = prepare_package_info(data)
    assert result.pypi_name == "foo"
    assert result.summary == "..."
    assert result.license_files_present is False
    assert result.license is None
    assert result.extras == []
    assert result.pypi_version == ""
    assert result.url == "..."


def test_prepare_package_info_only_package_url():
    data = {
        "name": "foo",
        "package_url": "https://example.com",
    }
    result = prepare_package_info(data)
    assert result.pypi_name == "foo"
    assert result.summary == "..."
    assert result.license_files_present is False
    assert result.license is None
    assert result.extras == []
    assert result.pypi_version == ""
    assert result.url == "https://example.com"


def test_prepare_package_info_only_project_url():
    data = {
        "name": "foo",
        "project_url": "https://example.com",
    }
    result = prepare_package_info(data)
    assert result.pypi_name == "foo"
    assert result.summary == "..."
    assert result.license_files_present is False
    assert result.license is None
    assert result.extras == []
    assert result.pypi_version == ""
    assert result.url == "https://example.com"


def test_prepare_package_info_project_urls_precedence():
    data = {
        "name": "foo",
        "project_url": "https://example1.com",
        "package_url": "https://example2.com",
        "project_urls": {"Homepage": "https://example3.com"},
    }
    result = prepare_package_info(data)
    assert result.pypi_name == "foo"
    assert result.summary == "..."
    assert result.license_files_present is False
    assert result.license is None
    assert result.extras == []
    assert result.pypi_version == ""
    assert result.url == "https://example3.com"


def test_prepare_package_info_home_page_precedence():
    data = {
        "name": "foo",
        "project_url": "https://example1.com",
        "package_url": "https://example2.com",
        "home_page": "https://example3.com",
    }
    result = prepare_package_info(data)
    assert result.pypi_name == "foo"
    assert result.summary == "..."
    assert result.license_files_present is False
    assert result.license is None
    assert result.extras == []
    assert result.pypi_version == ""
    assert result.url == "https://example3.com"


def test_prepare_package_info_project_url_precedence():
    data = {
        "name": "foo",
        "project_url": "https://example1.com",
        "package_url": "https://example2.com",
    }
    result = prepare_package_info(data)
    assert result.pypi_name == "foo"
    assert result.summary == "..."
    assert result.license_files_present is False
    assert result.license is None
    assert result.extras == []
    assert result.pypi_version == ""
    assert result.url == "https://example1.com"


def test_prepare_package_info_project_url_precedence_with_nulls():
    data = {
        "name": "foo",
        "project_urls": None,
        "project_url": None,
        "home_page": None,
        "package_url": "https://example1.com",
    }
    result = prepare_package_info(data)
    assert result.pypi_name == "foo"
    assert result.summary == "..."
    assert result.license_files_present is False
    assert result.license is None
    assert result.extras == []
    assert result.pypi_version == ""
    assert result.url == "https://example1.com"


def test_gather_package_info_pypi_source():
    pypi = {"info": {
        "name": "example",
        "summary": "A sample project",
        "license_expression": "MIT",
        "license": "MIT License",
        "classifiers": ["License :: OSI Approved :: MIT License"],
        "requires_dist": ["requests"],
        "version": "1.0.0",
        "license_files": ["LICENSE"],
        "project_urls": {"Homepage": "https://example.com"},
        "yanked": False,
        "maintainer": "John Doe",
        }, "releases": [],
        "urls": [{
            "packagetype": "sdist",
            "filename": "example-0.2-tar.gz"
        }, {
            "packagetype": "bdist_wheel",
            "filename": "example-0.2-py2.py3-none-any.whl"
        }]}
    result = gather_package_info(None, pypi)


def test_gather_package_info_core_metadata():
    data = {
        "name": "example",
        "summary": "A sample project",
        "license_expression": "MIT",
        "license": "MIT License",
        "classifiers": ["License :: OSI Approved :: MIT License"],
        "requires_dist": ["requests"],
        "version": "1.0.0",
        "license_files": ["LICENSE"],
        "home_page": "https://example.com",
        "metadata_version": "2.1",
    }
    pypi = {"info": {
        "name": "discarded",
        "summary": "Deliberately different metadata",
        "license_expression": "BSD",
        "license": "BSD",
        "classifiers": ["License :: OSI Approved :: BSD License"],
        "requires_dist": ["click"],
        "version": "7.0.0",
        "license_files": ["LICENSE.txt"],
        "project_urls": {"Source": "https://example.com"},
        "yanked": False,
        "maintainer": "John Doe",
        }, "releases": [],
        "urls": [{
            "packagetype": "sdist",
            "filename": "example-7.0-tar.gz"
        }, {"packagetype": "bdist_wheel",
            "filename": "example-7.0-cp34-abi3-manylinux1_x86_64.whl"
        }]}
    result = gather_package_info(data, pypi)
    assert result.pypi_name == "example"
    assert result.summary == "A sample project"
    assert result.license_files_present is True
    assert result.license == "MIT"
    assert result.extras == []
    assert result.pypi_version == "1.0.0"
    assert result.url == "https://example.com"


def test_create_package_from_pypi():
    data = {
        "name": "example",
        "summary": "A sample project",
        "license_expression": "MIT",
        "license": "MIT License",
        "classifiers": ["License :: OSI Approved :: MIT License"],
        "requires_dist": ["requests"],
        "version": "1.0.0",
        "license_files": ["LICENSE"],
        "home_page": "https://example.com",
        "metadata_version": "2.1",
    }
    pypi = {"info": {
        "name": "discarded",
        "summary": "Deliberately different metadata",
        "license_expression": "BSD",
        "license": "BSD",
        "classifiers": ["License :: OSI Approved :: BSD License"],
        "requires_dist": ["click"],
        "version": "7.0.0",
        "license_files": ["LICENSE.txt"],
        "project_urls": {"Source": "https://example.com"},
        "yanked": False,
        "maintainer": "John Doe",
        }, "releases": [],
        "urls": [{
            "packagetype": "sdist",
            "filename": "example-7.0-tar.gz"
        }, {"packagetype": "bdist_wheel",
            "filename": "example-7.0-cp34-abi3-manylinux1_x86_64.whl"
        }]}
    result = create_package_from_pypi(data, pypi)
    assert result.archive_name == "example-7.0-tar.gz"
    assert result.archful is True
    assert result.source == "PyPI"


def test_create_package_from_dir():
    pkg = create_package_from_dir("local_test", "tests/local/")
    assert pkg.pypi_name == "local-test"
    assert pkg.pypi_version == "0.12.2"
    assert pkg.source == "local"
    assert pkg.archful is False
    assert pkg.archive_name.split("/")[-1] == "local_test-0.12.2.tar.gz"
    assert pkg.license == "MIT AND MIT-0"
