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
