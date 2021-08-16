from pathlib import Path
import pytest

import conf2spec


def get_test_cases():
    """Go through all 'tests/' folders and get their names.
    Yield the next folder name."""

    source_path = Path("tests/")
    for path in source_path.glob("pyp2spec_*"):
        yield path.name


@pytest.mark.parametrize(
        ("test_case"),
        get_test_cases(),
        )
def test_generated_specfile(test_case):
    # Get config and expected resulting file
    config_file = Path("tests/") / test_case / f"{test_case}.conf"
    expected_file = Path("tests/") / test_case / f"{test_case}.spec"

    # Run the conf2spec converter
    conf = conf2spec.load_configuration(config_file)
    rendered_file = conf2spec.write_spec_file(conf)

    # Compare the results
    with open(rendered_file, "r") as rendered_f:
        rendered = rendered_f.read()
    with open(expected_file, "r") as expected_f:
        expected = expected_f.read()
    assert rendered == expected

    # Delete rendered file
    Path(rendered_file).unlink()