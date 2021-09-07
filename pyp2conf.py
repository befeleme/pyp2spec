import sys

from datetime import date
from subprocess import check_output

import click
import requests
import tomli_w


def get_pypi_metadata(package_name):
    pypi_index = f'https://pypi.org/pypi/{package_name}/json'
    response = requests.get(pypi_index)
    return response.json()


def changelog_head(email, name, changelog_date):
    """ :returns f'{date} {name} <{email}>'"""
    if not changelog_date:
        changelog_date = (date.today()).strftime('%a %b %d %Y')

    if email or name:
        return f'{changelog_date} {name} <{email}>'

    result = check_output(['rpmdev-packager'])
    result = result.decode().strip()
    return f'{changelog_date} {result}'


def changelog_msg(message):
    if message:
        return message
    return f"Package generated with pyp2spec"


def get_release(release):
    if release:
        return release
    return "1"


def get_project_url(package_data):
    try:
        return package_data["info"]["project_urls"]["Homepage"]
    # It may happen that no Homepage is listed with the project
    # In this case fall back to the safe PyPI URL
    except KeyError:
        return package_data["info"]["package_url"]


def get_python_name(pypi_name):
    if pypi_name.startswith("python"):
        return pypi_name
    else:
        return f"python-{pypi_name}"


def get_module_name(pypi_name):
    """A naive way to get probable module name: replace any occurrence
    of '-' in package PyPI name with '_' and return the result."""

    return [pypi_name.replace("-", "_")]


def get_source_url(pypi_name):
    return "%{pypi_source " + pypi_name + "}"


def get_archive_name(filename):
    return "-".join(filename.split("-")[:-1])


def get_version(version, package_data):
    if version:
        return version
    # Custom version was not provided, return the latest available
    return package_data["info"]["version"]


def get_summary(summary, package_data):
    if summary:
        return summary
    return package_data["info"]["summary"]


def create_config_contents(package_data, description=None, release=None,
    message=None, email=None, name=None, version=None, summary=None, date=None):
    """Use `package_data` to create the whole config contents.
    Return contents.
    """
    contents = {}

    pypi_name = package_data["info"]["name"]
    contents["pypi_name"] = pypi_name
    contents["python_name"] = get_python_name(pypi_name)
    contents["modules"] = get_module_name(pypi_name)
    version = get_version(version, package_data)
    contents["version"] = version
    contents["summary"] = get_summary(summary, package_data)
    contents["license"] = package_data["info"]["license"]
    contents["url"] = get_project_url(package_data)
    contents["source"] = get_source_url(pypi_name)

    for entry in package_data["releases"][version]:
        if entry["packagetype"] == "sdist":
            contents["archive_name"] = get_archive_name(entry["filename"])

    contents["description"] = description
    contents["release"] = get_release(release)
    contents["changelog_msg"] = changelog_msg(message)
    contents["changelog_head"] = changelog_head(email, name, date)

    return contents


def write_config(contents, output=None):
    """Write config file to a given destination.
    If none is provided, save it to current directory with package name as file name.
    """
    if output:
        dest = output
    else:
        package = contents["python_name"]
        dest = f"./{package}.conf"
    with open(dest, "wb") as f:
        tomli_w.dump(contents, f, multiline_strings=True)
    return dest


@click.command()
@click.argument(
    "package")
@click.option(
    "--output", "-o",
    help="Provide custom output for configuration file",
)
@click.option(
    "--description", "-d",
    help="Provide description for the package",
)
@click.option(
    "--release", "-r",
    help="Provide custom release (corresponds with Release in spec file)",
)
@click.option(
    "--message", "-m",
    help="Provide changelog message for the package",
)
@click.option(
    "--email", "-e",
    help="Provide e-mail for changelog",
)
@click.option(
    "--packagername", "-n",
    help="Provide packager name for changelog",
)
@click.option(
    "--version", "-v",
    help="Provide package version to query PyPI for",
)
@click.option(
    "--summary", "-s",
    help="Provide custom package summary",
)
@click.option(
    "--date",
    help="Provide custom date for changelog",
)
def main(package, output, description, release, message, email, packagername, version, summary, date):
    if not description:
        print("Description wasn't provided. "
        "Rerun the script with package description.")
        sys.exit(1)

    pypi_metadata = get_pypi_metadata(package)

    contents = create_config_contents(
        pypi_metadata, description, release, message, email, packagername, version, summary, date
    )
    write_config(contents, output)


if __name__ == "__main__":
    main()
