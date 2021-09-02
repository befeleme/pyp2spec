from pathlib import Path

import click
from jinja2 import Template

from config import ConfigFile

TEMPLATE_PATH = Path().resolve(__file__) / 'template.spec'


def generate_extra_build_requires(config):
    """If defined in config file, return extra build requires.
    If none were defined, return an empty string."""

    # TODO: This doesn't handle doubles like -xr
    options = {
        "test": "-t",
        "runtime": "-r",
        "extra": "-x",
    }
    extra_brs = config.get_value("extra_build_requires")

    # No extra BuildRequires were defined - return empty string
    if not extra_brs:
        return ""

    generated_brs = []
    add = generated_brs.append
    for extra_br in extra_brs:
        if extra_br == "extra":
            add(options.get(extra_br))
            add(",".join(config.get_value("extra_test_env")))
        else:
            add(options.get(extra_br))

    return " ".join(generated_brs)


def generate_check(config):
    """Generate valid check section.
    If defined in config file, use applicable test macro.
    If no test method was defined, return `%py3_check_import` with module name."""

    test_method = config.get_value("test_method")
    if test_method == "pytest":
        return generate_pytest(config)
    elif test_method == "tox":
        return generate_tox(config)
    else:
        # If no tests were defined, run at least smoke import check
        # This is mandatory as defined in Fedora Packaging Guidelines
        # https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#_tests
        return f"%py3_check_import {config.get_value('module_name')}"


def generate_pytest(config):
    """Return valid pytest macro with unwanted tests (if defined)."""

    if (unwanted_tests := generate_unwanted_tests(config)):
        return f"%pytest {unwanted_tests}"
    return "%pytest"


def generate_tox(config):
    """Return valid tox macro. If additional unwanted are defined,
    raise NotImplementedError."""

    if (unwanted_tests := generate_unwanted_tests(config)):
        raise NotImplementedError
    return "%tox"


def generate_unwanted_tests(config):
    """If defined in config file, get the unwanted tests.
    Given the unwanted tests are [a, b], return `-k "not a and\\\nnot b"`."""

    unwanted_tests = config.get_value("unwanted_tests")
    if not unwanted_tests:
        return ""
    else:
        prep_unwanteds = [f"not {test}" for test in unwanted_tests]
        unwanteds_as_str = " and \\\n".join(prep_unwanteds)
        formatted_unwanteds = f"-k \"{unwanteds_as_str}\""
        return formatted_unwanteds


def fill_in_template(config):
    """Return template rendered with data from config file."""

    with open(TEMPLATE_PATH) as template_file:
        spec_template = Template(template_file.read())

    result = spec_template.render(
        archive_name=config.get_value("archive_name"),
        binary_files=config.get_value("binary_files"),
        changelog_head=config.get_value("changelog_head"),
        changelog_msg=config.get_value("changelog_msg"),
        description=config.get_value("description"),
        doc_files=" ".join(config.get_value("doc_files")),
        extra_build_requires=generate_extra_build_requires(config),
        license_files=" ".join(config.get_value("license_files")),
        license=config.get_value("license"),
        manual_build_requires=config.get_value("manual_build_requires"),
        module_name=config.get_value("module_name"),
        name=config.get_value("pypi_name"),
        python_name=config.get_value("python_name"),
        release=config.get_value("release"),
        source=config.get_value("source"),
        summary=config.get_value("summary"),
        test_method=generate_check(config),
        url=config.get_value("url"),
        version=config.get_value("version"),
    )

    return result


def write_spec_file(config, output=None):
    """Save the spec file in the current directory.
    Return the saved file name"""

    result = fill_in_template(config)
    if output:
        spec_file_name = output
    else:
        spec_file_name = config.get_value("python_name") + ".spec"

    with open(spec_file_name, "w") as spec_file:
        spec_file.write(result)
    print(f"Spec file {spec_file_name} was saved.")
    return spec_file_name


@click.command()
@click.option(
    "--filename", "-f",
    required=True,
    help="Provide configuration file",
)
@click.option(
    "--output", "-o",
    help="Provide custom output where spec file will be saved",
)
def main(filename, output):
    config = ConfigFile(filename)
    write_spec_file(config, output)


if __name__ == "__main__":
    main()
