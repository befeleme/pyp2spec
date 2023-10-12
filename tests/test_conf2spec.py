"""Test the functionality of conf2spec part of the tool.
conf2spec can do a bit more that the fully automatic generation of spec files.
The tests test both the automatically generated files and the custom
configurations.
"""

from pathlib import Path
from textwrap import dedent
import pytest

from pyp2spec import conf2spec


@pytest.fixture
def config_dir():
    return "tests/test_configs/"


def test_long_description_is_split(config_dir):
    config_path = config_dir + "customized_markdown-it-py.conf"
    config = conf2spec.ConfigFile(config_path)
    expected = """\
        Markdown parser done right. Its features: Follows the CommonMark spec for
        baseline parsing. Has configurable syntax: you can add new rules and even
        replace existing ones. Pluggable: Adds syntax extensions to extend the parser.
        High speed & safe by default."""
    assert conf2spec.wrap_description(config) == dedent(expected)


@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("default_python-click.conf", False),
        ("customized_markdown-it-py.conf", True),
    ]
)
def test_automode_flag_is_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
    assert config.get_bool("automode") == expected



@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("default_python-click.conf", False),
        ("default_python-numpy.conf", True),
    ]
)
def test_archful_flag_is_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
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
