"""Test the functionality of conf2spec part of the tool.
conf2spec can do a bit more that the fully automatic generation of spec files.
The tests test both the automatically generated files and the custom
configurations.
"""

from pathlib import Path

import pytest

from pyp2spec import conf2spec


@pytest.fixture
def config_dir():
    return "tests/test_configs/"


@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("default_python-click.conf", False),
        ("customized_markdown-it-py.conf", True),
    ]
)
def test_automode_flag_is_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(conf2spec.load_config_file(config_path))
    assert config.get_bool("automode") == expected



@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("default_python-click.conf", False),
        ("default_python-numpy.conf", True),
    ]
)
def test_archful_flag_is_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(conf2spec.load_config_file(config_path))
    assert config.get_bool("archful") is expected


@pytest.mark.parametrize(
    "conf", [
        "default_python-click.conf",  # default, noarch, no quirks
        "customized_markdown-it-py.conf",  # automode on
        "customized_python-sphinx.conf",  # contains extras
        "default_python-numpy.conf",  # archful
        "default_python3.9-pello.conf",  # custom Python version
        "default_python-pytest7.2.conf",  # compat version
        "default_python-pytest7.conf",  # compat version - lower granularity
        "default_python-urllib3_2.conf",  # compat version - pkgname with a digit
    ]
)
def test_default_generated_specfile(file_regression, config_dir, conf):
    # Run the conf2spec converter
    rendered_file = conf2spec.create_spec_file(config_dir + conf)

    # Compare the results
    with open(rendered_file, "r", encoding="utf-8") as rendered_f:
        rendered = rendered_f.read()
    try:
        file_regression.check(
            rendered,
            fullpath=f"tests/expected_specfiles/{rendered_file}",
        )
    finally:
        # Cleanup - remove created file
        Path.unlink(Path(rendered_file))


@pytest.mark.parametrize(
    ("pypi_version", "rpm_version"), [
        ("1.1.0", "1.1.0"),
        ("1!0.2.13", "1:0.2.13"),
        ("0.0.2-beta1", "0.0.2~b1"),
        ("0.5.40-0", "0.5.40^post0"),
    ]
)
def test_pypi_version_is_converted_to_rpm(pypi_version, rpm_version):
    assert conf2spec.convert_version_to_rpm_scheme(pypi_version) == rpm_version


@pytest.mark.parametrize(
    ("version", "expected"), [
        ("1.2-3", False),
        ("1.2.3", True),
    ]
)
def test_source_macro(version, expected):
    assert conf2spec.same_as_rpm(version) is expected


def test_additional_build_requires_if_archful():
    fake_config_data = {"archful": True}
    fake_config = conf2spec.ConfigFile(fake_config_data)
    assert "gcc" in conf2spec.list_additional_build_requires(fake_config)


def test_additional_build_requires_if_noarch():
    fake_config_data = {"archful": False}
    fake_config = conf2spec.ConfigFile(fake_config_data)
    assert "gcc" not in conf2spec.list_additional_build_requires(fake_config)


@pytest.mark.parametrize(
    ("version", "expected"), [
        ("4.2", "%{python3_pkgversion}"),
        ("3.15", "%{python3_pkgversion}"),
        ("", "3"),
    ]
)
def test_python3_pkgversion_or_3(version, expected):
    fake_config_data = {"python_alt_version": version}
    fake_config = conf2spec.ConfigFile(fake_config_data)
    assert conf2spec.python3_pkgversion_or_3(fake_config) == expected


def test_empty_license_string():
    fake_config_data = {"archful": False}
    fake_config = conf2spec.ConfigFile(fake_config_data)
    license_data = conf2spec.get_license_string(fake_config)
    assert license_data[0] == "..."
    assert license_data[1] == "# No license information obtained, it's up to the packager to fill it in"


def test_license_strings():
    fake_config_data = {"license": "MIT"}
    fake_config = conf2spec.ConfigFile(fake_config_data)
    license_data = conf2spec.get_license_string(fake_config)
    assert license_data[0] == "MIT"
    assert "# Check if the automatically generated License and its spelling is correct for Fedora" in license_data[1] 


@pytest.mark.parametrize(
    ("version", "extension", "expected"), [
        ("1.2", "tar.gz", "%{pypi_source foo}"),
        ("1.2", "zip", "%{pypi_source foo %{version} zip}"),
        ("1.2-3", "tar.gz", "%{pypi_source foo 1.2-3}"),
        ("0.0.2-beta1", "zip", "%{pypi_source foo 0.0.2-beta1 zip}"),
    ]
)
def test_source(version, extension, expected):
    fake_config_data = {"pypi_name": "foo", "archive_name": f"foo-{version}.{extension}", "source": "PyPI"}
    fake_config = conf2spec.ConfigFile(fake_config_data)
    assert conf2spec.source(fake_config, version) == expected


@pytest.mark.parametrize(
    ("version", "expected"), [
        ("1.2", "%{version}"),
        ("1.2-3", "1.2-3"),
        ("0.0.2-beta1", "0.0.2-beta1"),
    ]
)
def test_pypi_version_or_macro(version, expected):
    assert conf2spec.pypi_version_or_macro(version) == expected
