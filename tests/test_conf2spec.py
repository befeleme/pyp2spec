from pathlib import Path
import pytest

import conf2spec


def get_config_files():
    """Yield the relative paths to the config files placed in 'tests/test_configs'."""

    source_path = Path("tests/test_configs")
    for path in source_path.iterdir():
        yield path


@pytest.mark.parametrize(("config"), get_config_files())
def test_generated_specfile(file_regression, config):
    # Run the conf2spec converter
    conf = conf2spec.load_configuration(config)
    rendered_file = conf2spec.write_spec_file(conf)

    # Compare the results
    with open(rendered_file, "r") as rendered_f:
        rendered = rendered_f.read()

    file_regression.check(rendered, basename=config.stem, extension=".spec")
