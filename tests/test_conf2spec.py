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


def test_manual_brs_are_loaded(config_dir):
    config_path = config_dir + "customized_boutdata.conf"
    config = conf2spec.ConfigFile(config_path)
    expected = [
        "python3dist(setuptools)",
        "python3dist(setuptools-scm[toml]) >= 3.4",
        "python3dist(setuptools-scm-git-archive)",
        "python3dist(pytest)",
    ]
    assert config.get_list("manual_build_requires") == expected


def test_no_manual_brs(config_dir):
    config_path = config_dir + "customized_click.conf"
    config = conf2spec.ConfigFile(config_path)
    assert config.get_list("manual_build_requires") == []


def test_long_description_is_split(config_dir):
    config_path = config_dir + "customized_jupyter-packaging.conf"
    config = conf2spec.ConfigFile(config_path)
    expected = "This package contains utilities for making Python packages with and without\naccompanying JavaScript packages."
    assert conf2spec.wrap_description(config) == expected


@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("customized_boutdata.conf", "%pytest"),
        ("customized_click.conf", "%tox"),
        ("customized_aionotion.conf", ""),
        ("customized_markdown-it-py.conf", "%pytest -k 'not test_file and \\\nnot test_linkify'")
    ]
)
def test_check_is_generated(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
    assert conf2spec.generate_check(config) == expected


@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("customized_boutdata.conf", True),
        ("customized_markdown-it-py.conf", False),
    ]
)
def test_top_level_flag_is_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
    assert config.get_bool("test_top_level") == expected


@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("customized_click.conf", "-t"),
        ("customized_jupyter-packaging.conf", "-x test"),
    ]
)
def test_br_extra_is_generated(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
    assert conf2spec.generate_extra_build_requires(config) == expected


@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("customized_boutdata.conf", ["LICENSE"]),
        ("customized_markdown-it-py.conf", ["LICENSE", "LICENSE.markdown-it"]),
        ("customized_aionotion.conf", []),
    ]
)
def test_license_files_are_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
    assert config.get_list("license_files") == expected


@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("customized_click.conf", ["README.rst", "CHANGES.rst"]),
        ("customized_markdown-it-py.conf", ["README.md"]),
        ("customized_aionotion.conf", []),
    ]
)
def test_doc_files_are_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
    assert config.get_list("doc_files") == expected


@pytest.mark.parametrize(
    ("conf", "expected"), [
        ("customized_click.conf", []),
        ("customized_markdown-it-py.conf", ["markdown-it"]),
    ]
)
def test_binary_files_are_loaded(config_dir, conf, expected):
    config_path = config_dir + conf
    config = conf2spec.ConfigFile(config_path)
    assert config.get_list("binary_files") == expected


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
