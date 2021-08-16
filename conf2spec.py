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
    }
    return options.get(config["extra_build_requires"], "")


def generate_check(config):
    """    If defined in config file, return the applicable macro invocation.
    If none was defined, return %py3_check_import with module name."""

    # TODO: This list is far from complete
    options = {
        "tox": "%tox",
        "pytest": "%pytest",
    }
    fallback = f"%py3_check_import {config['module_name']}"
    return options.get(config["test"], fallback)


def generate_manual_build_requires(config):
    """If defined in config file, return manual build requires.
    If none were defined, return an empty string."""

    return config.get("manual_build_requires", "")


def fill_in_template(config):
    """Return template rendered with data from config file."""

    with open(TEMPLATE_PATH) as template_file:
        spec_template = Template(template_file.read())

    result = spec_template.render(
        name=config["name"],
        python_name=config["python_name"],
        version=config["version"],
        release=config["release"],
        summary=config["summary"],
        license=config["license"],
        url=config["url"],
        source=config["source"],
        description=config["description"],
        module_name=config["module_name"],
        manual_build_requires=generate_manual_build_requires(config),
        extra_build_requires=generate_extra_build_requires(config),
        test=generate_check(config),
        license_files=" ".join(config["files"]["license_files"]),
        doc_files=" ".join(config["files"]["doc_files"]),

        changelog_head=config["changelog"]["changelog_head"],
        changelog_msg=config["changelog"]["changelog_msg"],
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