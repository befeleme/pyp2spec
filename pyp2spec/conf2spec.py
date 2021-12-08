from importlib.resources import read_text
from textwrap import fill

import click
import tomli

from jinja2 import Template


TEMPLATE_FILENAME = 'template.spec'


class ConfigFile:
    """Load configuration file and return its validated values."""

    def __init__(self, filename):
        self.filename = filename
        self.contents = self.load_configuration

    @property
    def load_configuration(self):
        """Return loaded TOML configuration file contents."""

        with open(self.filename, "rb") as configuration_file:
            loaded_contents = tomli.load(configuration_file)

        return loaded_contents

    def get_string(self, key):
        """Return a value for given key. Validate the value is a string.
        Raise TypeError otherwise."""

        return self._get_value(key, str)

    def get_list(self, key):
        """Return a value for given key. Validate the value is a list.
        Raise TypeError otherwise."""

        return self._get_value(key, list)

    def get_bool(self, key):
        """Return a value for given key. Validate the value is a boolean.
        Raise TypeError otherwise."""

        return self._get_value(key, bool)

    def _get_value(self, key, val_type):
        val = self.contents.get(key, val_type())
        if not isinstance(val, val_type):
            raise TypeError(f"{val} must be a {val_type}")
        return val


def generate_extra_build_requires(config):
    """If defined in config file, return extra build requires.
    If none were defined, return `-r` - runtime extra BRs`."""

    # TODO: custom tox env (-e)
    options = {
        "tox": "-t",
        "extra": "-x",
    }
    extra_brs = config.get_list("extra_build_requires")

    # No extra BuildRequires were defined - return `-r` = runtime
    if not extra_brs:
        return "-r"

    generated_brs = []
    add = generated_brs.append
    for extra_br in extra_brs:
        if extra_br == "extra":
            add(options.get(extra_br))
            add(",".join(config.get_list("extra_test_env")))
        else:
            add(options.get(extra_br))

    return " ".join(generated_brs)


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
        raise NotImplementedError
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
        formatted_unwanteds = f'-k "{unwanteds_as_str}"'
        return formatted_unwanteds


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

    spec_template = Template(read_text("pyp2spec", TEMPLATE_FILENAME))

    result = spec_template.render(
        archive_name=config.get_string("archive_name"),
        binary_files=config.get_list("binary_files"),
        changelog_head=config.get_string("changelog_head"),
        changelog_msg=config.get_string("changelog_msg"),
        description=wrap_description(config),
        doc_files=" ".join(config.get_list("doc_files")),
        extra_build_requires=generate_extra_build_requires(config),
        license_files=" ".join(config.get_list("license_files")),
        license=config.get_string("license"),
        manual_build_requires=config.get_list("manual_build_requires"),
        name=config.get_string("pypi_name"),
        python_name=config.get_string("python_name"),
        release=config.get_string("release"),
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
    with open(output, "w") as spec_file:
        click.secho(f"Saving spec file to '{output}'", fg='yellow')
        spec_file.write(result)
    click.secho("Spec file was saved successfully", fg="green")
    return output


def create_spec_file(config_file, spec_output=None):
    """Create and save the generate spec file."""
    config = ConfigFile(config_file)
    return save_spec_file(config, spec_output)


@click.command()
@click.argument("config")
@click.option(
    "--spec-output",
    "-s",
    help="Provide custom output for spec file",
)
def main(config, spec_output):
    create_spec_file(config, spec_output)


if __name__ == "__main__":
    main()
