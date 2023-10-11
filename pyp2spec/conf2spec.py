import sys

from importlib.resources import files
from textwrap import fill

import click

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from jinja2 import Template

from pyp2spec.utils import Pyp2specError


TEMPLATE_FILENAME = "template.spec"
ADDITIONAL_BUILD_REQUIRES_ARCHFUL = ["gcc"]
ADDITIONAL_BUILD_REQUIRES_NOARCH = []


class ConfigError(Pyp2specError):
    """Raised when a config value has got a wrong type"""


class ConfigFile:
    """Load configuration file and return its validated values."""

    def __init__(self, filename):
        self.filename = filename
        self.contents = self.load_configuration

    @property
    def load_configuration(self):
        """Return loaded TOML configuration file contents."""

        with open(self.filename, "rb") as configuration_file:
            loaded_contents = tomllib.load(configuration_file)

        return loaded_contents

    def get_string(self, key):
        """Return a value for given key. Validate the value is a string.
        Raise ConfigError otherwise."""

        return self._get_value(key, str)

    def get_list(self, key):
        """Return a value for given key. Validate the value is a list.
        Raise ConfigError otherwise."""

        return self._get_value(key, list)

    def get_bool(self, key):
        """Return a value for given key. Validate the value is a boolean.
        Raise ConfigError otherwise."""

        return self._get_value(key, bool)

    def _get_value(self, key, val_type):
        val = self.contents.get(key, val_type())
        if not isinstance(val, val_type):
            raise ConfigError(f"{val} must be a {val_type}")
        return val


def generate_check(config):
    """Generate valid check section.
    If defined in config file, use applicable test macro.
    If no test method was defined, return an empty string."""

    test_method = config.get_string("test_method")
    if test_method == "pytest":
        return generate_pytest(config)
    elif test_method == "tox":
        return generate_tox(config)
    else:
        return ""


def generate_pytest(config):
    """Return valid pytest macro with unwanted tests (if defined)."""

    if unwanted_tests := generate_unwanted_tests(config):
        return f"%pytest {unwanted_tests}"
    return "%pytest"


def generate_tox(config):
    """Return valid tox macro. If additional unwanted are defined,
    raise NotImplementedError."""

    if unwanted_tests := generate_unwanted_tests(config):
        raise NotImplementedError("It's currently impossible to filter out tests with %tox")
    return "%tox"


def generate_unwanted_tests(config):
    """If defined in config file, get the unwanted tests.
    Given the unwanted tests are [a, b], return `-k "not a and\\\nnot b"`."""

    unwanted_tests = config.get_list("unwanted_tests")
    if not unwanted_tests:
        return ""
    else:
        prep_unwanteds = [f"not {test}" for test in unwanted_tests]
        unwanteds_as_str = " and \\\n".join(prep_unwanteds)
        formatted_unwanteds = f"-k '{unwanteds_as_str}'"
        return formatted_unwanteds


def list_additional_build_requires(config):
    """Returns a list of additionally defined BuildRequires,

    The list differs for packages that are or aren't archful.
    """
    if config.get_bool("archful"):
        return ADDITIONAL_BUILD_REQUIRES_ARCHFUL
    return ADDITIONAL_BUILD_REQUIRES_NOARCH


def wrap_description(config):
    """Wrap description line to 79 characters at most.

    If the description line length exceeds 79 lines, tools like rpmlint start
    emit warnings. Use newlines to prevent exceeding the max. length.
    Return the modified description string.
    """
    return fill(
        config.get_string("description"),
        width=79,
        break_long_words=False
    )

def fill_in_template(config):
    """Return template rendered with data from config file."""

    with (files("pyp2spec") / TEMPLATE_FILENAME).open("r", encoding="utf-8") as f:
        spec_template = Template(f.read())

    result = spec_template.render(
        additional_build_requires=list_additional_build_requires(config),
        archful=config.get_bool("archful"),
        archive_name=config.get_string("archive_name"),
        binary_files=config.get_list("binary_files"),
        description=wrap_description(config),
        doc_files=" ".join(config.get_list("doc_files")),
        extras=",".join(config.get_list("extras")),
        license_files=" ".join(config.get_list("license_files")),
        license=config.get_string("license"),
        name=config.get_string("pypi_name"),
        python_name=config.get_string("python_name"),
        pypi_version=config.get_string("pypi_version"),
        source=config.get_string("source"),
        summary=config.get_string("summary"),
        test_method=generate_check(config),
        test_top_level=config.get_bool("test_top_level"),
        url=config.get_string("url"),
        version=config.get_string("version"),
    )

    return result


def save_spec_file(config, output):
    """Save the spec file in the current directory if custom output is not set.
    Return the saved file name."""

    result = fill_in_template(config)
    if output is None:
        output = config.get_string("python_name") + ".spec"
    with open(output, "w", encoding="utf-8") as spec_file:
        spec_file.write(result)
    click.secho(f"Spec file was saved successfully to '{output}'", fg="green")
    return output


def create_spec_file(config_file, spec_output=None):
    """Create and save the generate spec file."""
    config = ConfigFile(config_file)
    return save_spec_file(config, spec_output)


@click.command()
@click.argument("config")
@click.option(
    "--spec-output",
    "-o",
    help="Provide custom output for spec file",
)
def main(config, spec_output):
    try:
        create_spec_file(config, spec_output)
    except (Pyp2specError, NotImplementedError) as exc:
        click.secho(f"Fatal exception occurred: {exc}", fg="red")
        sys.exit(1)

if __name__ == "__main__":
    main()
