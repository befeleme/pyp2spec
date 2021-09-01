from pathlib import Path

import click
import tomli

from jinja2 import Template


TEMPLATE_PATH = Path().resolve(__file__) / 'template.spec'


def load_configuration(filename):
    """Load TOML configuration file.
    Raise exception if file's contents is not a valid TOML."""

    with open(filename, "rb") as configuration_file:
        try:
            return tomli.load(configuration_file)
        except tomli.TOMLDecodeError as err:
            print("That's not a valid TOML file.")
            raise err


def generate_extra_build_requires(config):
    """If defined in config file, return extra build requires.
    If none were defined, return an empty string."""

    # TODO: This doesn't handle doubles like -xr
    options = {
        "test": "-t",
        "runtime": "-r",
        "extra": "-x",
    }
    extra_brs = config.get("extra_build_requires", None)

    # No extra BuildRequires were defined - return empty string
    if not extra_brs:
        return ""

    generated_brs = []
    add = generated_brs.append
    for extra_br in extra_brs:
        if extra_br == "extra":
            add(options.get(extra_br))
            add(",".join(config["extra_test_env"]))
        else:
            add(options.get(extra_br))

    return " ".join(generated_brs)


def generate_check(config):
    """Generate valid check section.
    If defined in config file, use applicable test macro.
    If no test method was defined, return `%py3_check_import` with module name."""

    test_method = config.get("test_method")
    if test_method == "pytest":
        return generate_pytest(config)
    elif test_method == "tox":
        return generate_tox(config)
    else:
        # If no tests were defined, run at least smoke import check
        # This is mandatory as defined in Fedora Packaging Guidelines
        # https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#_tests
        return f"%py3_check_import {config['module_name']}"


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

    unwanted_tests = config.get("unwanted_tests")
    if not unwanted_tests:
        return ""
    else:
        prep_unwanteds = [f"not {test}" for test in unwanted_tests]
        unwanteds_as_str = " and \\\n".join(prep_unwanteds)
        formatted_unwanteds = f"-k \"{unwanteds_as_str}\""
        return formatted_unwanteds


def generate_manual_build_requires(config):
    """If defined in config file, return manual build requires.
    If none were defined, return an empty string."""

    return config.get("manual_build_requires", "")


def generate_binary_files(config):
    """If defined in config file, return binary_files.
    If none were defined, return an empty string."""

    return config.get("binary_files", "")


def fill_in_template(config):
    """Return template rendered with data from config file."""

    with open(TEMPLATE_PATH) as template_file:
        spec_template = Template(template_file.read())

    result = spec_template.render(
        name=config["pypi_name"],
        python_name=config["python_name"],
        version=config["version"],
        release=config["release"],
        summary=config["summary"],
        license=config["license"],
        url=config["url"],
        source=config["source"],
        description=config["description"],
        module_name=config["module_name"],
        archive_name=config["archive_name"],
        manual_build_requires=generate_manual_build_requires(config),
        extra_build_requires=generate_extra_build_requires(config),
        test_method=generate_check(config),
        license_files=" ".join(config["license_files"]),
        doc_files=" ".join(config["doc_files"]),
        binary_files=generate_binary_files(config),
        changelog_head=config["changelog_head"],
        changelog_msg=config["changelog_msg"],
    )

    return result


def write_spec_file(config):
    """Save the spec file in the current directory.
    Return the saved file name"""

    # TODO: make it possible to write the file to a given directory
    result = fill_in_template(config)
    spec_file_name = config["python_name"] + ".spec"
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
def main(filename):
    config = load_configuration(filename)
    print(f"{filename} loaded successful")
    write_spec_file(config)


if __name__ == "__main__":
    main()