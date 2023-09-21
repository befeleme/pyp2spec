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


def test_long_description_is_split(config_dir):
    config_path = config_dir + "customized_jupyter-packaging.conf"
    config = conf2spec.ConfigFile(config_path)
    expected = "This package contains utilities for making Python packages with and without\naccompanying JavaScript packages."
    assert conf2spec.wrap_description(config) == expected


@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("customized_boutdata.conf", True),
        ("customized_markdown-it-py.conf", False),
    ]
)
def test_automode_flag_is_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
    assert config.get_bool("automode") == expected



@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("customized_click.conf", False),
        ("customized_tornado.conf", True),
    ]
)
def test_archful_flag_is_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
    assert config.get_bool("archful") is expected


@pytest.mark.parametrize(
    "conf", [
        "default_python-click.conf",
        "customized_markdown-it-py.conf",
        "customized_python-sphinx.conf",
        "default_python-numpy.conf",
        "default_python3.9-pello.conf",
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
