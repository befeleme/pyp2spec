from pathlib import Path

import click
from jinja2 import Template

from config import ConfigFile

TEMPLATE_PATH = Path().resolve(__file__) / "template.spec"


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
    If no test method was defined, return `%py3_check_import` with module name."""

    test_method = config.get_string("test_method")
    if test_method == "pytest":
        return generate_pytest(config)
    elif test_method == "tox":
        return generate_tox(config)
    else:
        # If no tests were defined, run at least smoke import check
        # This is mandatory as defined in Fedora Packaging Guidelines
        # https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#_tests
        modules = " ".join(config.get_list("modules"))
        return f"%py3_check_import {modules}"


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


def fill_in_template(config):
    """Return template rendered with data from config file."""

    with open(TEMPLATE_PATH) as template_file:
        spec_template = Template(template_file.read())

    result = spec_template.render(
        archive_name=config.get_string("archive_name"),
        binary_files=config.get_list("binary_files"),
        changelog_head=config.get_string("changelog_head"),
        changelog_msg=config.get_string("changelog_msg"),
        description=config.get_string("description"),
        doc_files=" ".join(config.get_list("doc_files")),
        extra_build_requires=generate_extra_build_requires(config),
        license_files=" ".join(config.get_list("license_files")),
        license=config.get_string("license"),
        manual_build_requires=config.get_list("manual_build_requires"),
        modules=" ".join(config.get_list("modules")),
        name=config.get_string("pypi_name"),
        python_name=config.get_string("python_name"),
        release=config.get_string("release"),
        source=config.get_string("source"),
        summary=config.get_string("summary"),
        test_method=generate_check(config),
        url=config.get_string("url"),
        version=config.get_string("version"),
    )

    return result


def save_spec_file(config, output=None):
    """Save the spec file in the current directory.
    Return the saved file name"""

    result = fill_in_template(config)
    if output:
        spec_file_name = output
    else:
        spec_file_name = config.get_string("python_name") + ".spec"

    with open(spec_file_name, "w") as spec_file:
        spec_file.write(result)
    print(f"Spec file {spec_file_name} was saved.")
    return spec_file_name


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
