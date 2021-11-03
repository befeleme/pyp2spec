"""Test the functionality of conf2spec part of the tool.
conf2spec can do a bit more that the fully automatic generation of spec files.
The test configs contain some additional tweaks a maintainer might do with
their packages.
"""

from pathlib import Path
import pytest

import conf2spec


def get_config_files():
    """Yield the relative paths to the config files placed in 'tests/test_configs'."""

    source_path = Path("tests/test_configs")
    for path in source_path.iterdir():
        if path.name.startswith("conf2spec"):
            yield path


@pytest.mark.parametrize(("config_file"), get_config_files())
def test_custom_generated_specfile(file_regression, config_file):
    # Run the conf2spec converter
    rendered_file = conf2spec.create_spec_file(config_file)

    # Compare the results
    with open(rendered_file, "r") as rendered_f:
        rendered = rendered_f.read()

    try:
        file_regression.check(
            rendered,
            fullpath=f"tests/expected_specfiles/{rendered_file}",
        )

    finally:
        # Cleanup - remove created file
        Path.unlink(Path(rendered_file))
