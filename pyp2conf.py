from datetime import date
from subprocess import check_output

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


def is_package_name(package):
    """Check whether the string given as package contains `/`.
    Return True if not, False otherwise."""

    if "/" in package:
        # It's probably URL
        return False
    return True


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

    # a package name was given as the `package`, look for it on PyPI
    if is_package_name(package):
        pkg = PypiPackage(package, session)
    # a URL was given as the `package`
    else:
        raise NotImplementedError

    # If the arguments weren't provided via CLI,
    # get them from the stored package object data or the default values
    if message is None:
        message = changelog_msg()

    if description is None:
        description = get_description(package)

    if summary is None:
        summary = pkg.summary()

    if version is None:
        version = pkg.version()

    if license is None:
        license = pkg.license()

    if release is None:
        release = "1"

    contents["changelog_msg"] = message
    contents["changelog_head"] = changelog_head(email, name, date)
    contents["description"] = description
    contents["summary"] = summary
    contents["version"] = version
    contents["license"] = license
    contents["release"] = release
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
        description=description,
        release=release,
        message=message,
        email=email,
        name=packagername,
        version=version,
        summary=summary,
        date=date,
        license=license,
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
