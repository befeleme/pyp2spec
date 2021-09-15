from datetime import date
from subprocess import check_output
from urllib.parse import urlparse

import click
import requests
import tomli_w


class PypiPackage:
    """Get and save package data from PyPI."""

    def __init__(self, package, session=None):
        self.package = package
        self.package_data = self.get_package_metadata(session)

    @property
    def pypi_name(self):
        return self.package_data["info"]["name"]

    def get_package_metadata(self, session):
        pkg_index = f"https://pypi.org/pypi/{self.package}/json"
        s = session or requests.Session()
        response = s.get(pkg_index)
        return response.json()

    def python_name(self):
        if self.pypi_name.startswith("python"):
            return self.pypi_name
        else:
            return f"python-{self.pypi_name}"

    def modules(self):
        """A naive way to get probable module name: replace any occurrence
        of '-' in package PyPI name with '_' and return the result."""

        return [self.pypi_name.replace("-", "_")]

    def source_url(self, version):
        return "%{pypi_source " + self.archive_name(version) + "}"

    def version(self):
        return self.package_data["info"]["version"]

    def license(self):
        pkg_license = self.package_data["info"]["license"]
        if pkg_license:
            return pkg_license
        else:
            raise click.UsageError(
                "Could not get license from PyPI. " +
                "Specify --license explicitly."
            )

    def summary(self):
        return self.package_data["info"]["summary"]

    def project_url(self):
        try:
            return self.package_data["info"]["project_urls"]["Homepage"]
        # It may happen that no Homepage is listed with the project
        # In this case fall back to the safe PyPI URL
        except KeyError:
            return self.package_data["info"]["package_url"]

    def archive_name(self, version):
        for entry in self.package_data["releases"][version]:
            if entry["packagetype"] == "sdist":
                return "-".join(entry["filename"].split("-")[:-1])


def changelog_head(email, name, changelog_date):
    """Return f'{date} {name} <{email}>'"""
    if not changelog_date:
        changelog_date = (date.today()).strftime("%a %b %d %Y")

    if email or name:
        return f"{changelog_date} {name} <{email}>"

    result = check_output(["rpmdev-packager"])
    result = result.decode().strip()
    return f"{changelog_date} {result}"


def changelog_msg():
    """Return a default changelog message."""

    return "Package generated with pyp2spec"


def get_description(package):
    """Return a default package description."""

    return f"This is package '{package}' generated automatically by pyp2spec."


def is_url(package):
    """Return True if string given as 'package' is valid URL, otherwise False."""
    parsed = urlparse(package)
    if all((parsed.scheme, parsed.netloc)):
        return True
    return False


def create_config_contents(
    package,
    description=None,
    release=None,
    message=None,
    email=None,
    name=None,
    version=None,
    summary=None,
    date=None,
    session=None,
    license=None,
):
    """Use `package` and provided kwargs to create the whole config contents.
    Return contents dictionary.
    """
    contents = {}

    # `package` is not a URL -> it's a package name, look for it on PyPI
    if not is_url(package):
        pkg = PypiPackage(package, session)

    # If the arguments weren't provided via CLI,
    # get them from the stored package object data or the default values
    if not message:
        message = changelog_msg()
    if not description:
        description = get_description(package)
    if not summary:
        summary = pkg.summary()
    if not version:
        version = pkg.version()
    if not license:
        license = pkg.license()


    # These items don't depend on information gathered from the package source
    contents["changelog_msg"] = message
    contents["changelog_head"] = changelog_head(email, name, date)
    contents["release"] = release or "1"
    contents["description"] = description

    # There items may be either set via CLI or gotten from package object
    contents["summary"] = summary
    contents["version"] = version
    contents["license"] = license

    # Set the values from the package object
    contents["pypi_name"] = pkg.pypi_name
    contents["python_name"] = pkg.python_name()
    contents["modules"] = pkg.modules()
    contents["url"] = pkg.project_url()
    contents["source"] = pkg.source_url(version)
    contents["archive_name"] = pkg.archive_name(version)

    return contents


def save_config(contents, output=None):
    """Write config file to a given destination.
    If none is provided, save it to current directory with package name as file name.
    """
    if not output:
        package = contents["python_name"]
        output = f"./{package}.conf"
    with open(output, "wb") as f:
        tomli_w.dump(contents, f, multiline_strings=True)
    return output


def create_config(
    package,
    conf_output,
    description,
    release,
    message,
    email,
    packagername,
    version,
    summary,
    date,
    license,
):

    contents = create_config_contents(
        package,
        conf_output,
        description,
        release,
        message,
        email,
        packagername,
        version,
        summary,
        date,
        license,
    )
    return save_config(contents, conf_output)


@click.command()
@click.argument("package")
@click.option(
    "--conf-output",
    "-o",
    help="Provide custom output for configuration file",
)
@click.option(
    "--description",
    "-d",
    help="Provide description for the package",
)
@click.option(
    "--release",
    "-r",
    help="Provide custom release (corresponds with Release in spec file)",
)
@click.option(
    "--message",
    "-m",
    help="Provide changelog message for the package",
)
@click.option(
    "--email",
    "-e",
    help="Provide e-mail for changelog",
)
@click.option(
    "--packagername",
    "-n",
    help="Provide packager name for changelog",
)
@click.option(
    "--version",
    "-v",
    help="Provide package version to query the backend for",
)
@click.option(
    "--summary",
    "-s",
    help="Provide custom package summary",
)
@click.option(
    "--date",
    help="Provide custom date for changelog",
)
@click.option(
    "--license",
    "-l",
    help="Provide license",
)
def main(
    package,
    conf_output,
    description,
    release,
    message,
    email,
    packagername,
    version,
    summary,
    date,
    license,
):

    create_config(
        package,
        conf_output,
        description,
        release,
        message,
        email,
        packagername,
        version,
        summary,
        date,
        license,
    )


if __name__ == "__main__":
    main()
