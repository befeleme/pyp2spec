from datetime import date
from importlib.resources import open_text
from subprocess import check_output
import json
import sys

import click
import requests
import tomli_w

from pyp2spec.rpmversion import RpmVersion


class PypiPackage:
    """Get and save package data from PyPI."""

    def __init__(self, package, session=None):
        self.package = package
        self.package_data = self.get_package_metadata(session)
        self.sdist_filename = None

    @property
    def pypi_name(self):
        return self.package_data["info"]["name"]

    def get_package_metadata(self, session):
        pkg_index = f"https://pypi.org/pypi/{self.package}/json"
        s = session or requests.Session()
        try:
            response = s.get(pkg_index).json()
        except json.decoder.JSONDecodeError:
            click.secho(f"'{self.package}' was not found on PyPI, did you spell it correctly?", fg="red")
            sys.exit(1)
        else:
            return response

    def python_name(self):
        if self.pypi_name.startswith("python"):
            return self.pypi_name
        else:
            return f"python-{self.pypi_name}"

    def source(self, version):
        """Return valid pypi_source RPM macro.

        %pypi_source takes three optional arguments:
        <name>, <version> and <file_extension>.
        <name> is always passed, it's spelled as the name of the archive file:
        "%{pypi_source foo}".
        <version> is passed if PyPI's and RPM's version strings differ:
        "%{pypi_source foo 1.2-3}". If they're the same and the file extension
        is not zip, version is not passed.
        If archive is a zip file, %{pypi_source} must take all three args:
        "%{pypi_source foo %{version} zip}", "{pypi_source foo 1.2-3 zip}"
        """
        is_zip = self.is_zip_archive(version)
        version_str = self.pypi_version_or_macro(version)

        source_macro_args = self.archive_name(version)

        if is_zip:
            source_macro_args += f" {version_str} zip"
        else:
            if version_str == version:
                source_macro_args += f" {version_str}"

        return "%{pypi_source " + source_macro_args + "}"

    def version(self):
        return self.package_data["info"]["version"]

    def pypi_version_or_macro(self, version):
        """If PyPI and RPM version's strings are the same, there's no need to
        duplicate them across the spec file.
        Return '%{version}' as a reference to the RPM's version string.
        If they are different, both variants of string need to be used.
        In such case return version string as from PyPI.
        """
        rpm_version = convert_version_to_rpm_scheme(version)
        if version == rpm_version:
            return "%{version}"
        return version

    def license(self, compliant=False):
        """Return the license string from package metadata.

        First, check trove classifiers which are the current Python standard:
        https://www.python.org/dev/peps/pep-0301/#distutils-trove-classification
        If argument `compliant` is set to True, perform the approximate compliance
        check of the parsed classifiers with Fedora Good Licenses.
        This isn't a 100% reliable solution and in case of ambiguous results,
        the license is discarded as invalid.
        Only if a package doesn't define the license in the classifiers, the "license"
        keyword is checked. There isn't any check whether that value is compliant
        with Fedora, it is passed to the config file for the user to validate.
        Some packages fill in "license" with the whole license text.
        This is indicated by the multiline value and such is discarded as invalid.

        If the license can't be determined from both classifiers and "license"
        keyword, this fact is logged and the script ended.
        """
        click.secho("Attempting to get license from Classifiers", fg="cyan")
        self.classifiers = self.read_license_classifiers()
        # Process classifiers further if there are some
        if self.classifiers:
            return self.get_license_from_classifiers(compliant)
        else:
            click.secho("License in Classifiers not found, looking for the 'License' keyword", fg="cyan")
            pkg_license = self.package_data["info"]["license"]
            # Check if license isn't empty and is only one line
            if pkg_license and len(pkg_license.split("\n")) == 1:
                return pkg_license
            else:
                click.secho("Invalid license field value length, cannot reliably determine the license", fg="red")

        click.secho("License not found. Specify --license explicitly. Quitting", fg="red")
        sys.exit(1)

    def get_license_from_classifiers(self, compliant):
        license_map = self.read_license_map()
        licenses = []
        for classifier in self.classifiers:
            short_license, fedora_status = license_map[classifier]
            # "OSI Approved" is a top-level category which doesn't bring
            # any valuable information, let's just ignore it when encountered
            if short_license == "OSI Approved":
                continue
            if compliant:
                # "???" are APSL, Artistic, Eiffel - some versions are Fedora OK,
                # some not. On PyPI there are <100 packages with them, rather than
                # adding another layer of decision matrix, just skip them all.
                if fedora_status in ["BAD", "UNKNOWN", "???"]:
                    click.secho(f"License '{short_license}' is or may not be allowed in Fedora, quitting", fg="red")
                    sys.exit(1)
                else:
                    licenses.append(short_license)
            else:
                licenses.append(short_license)
        return " and ".join(licenses)

    def read_license_map(self):
        with open_text("pyp2spec", "classifiers_to_fedora.json") as f:
            license_map = json.load(f)
        return license_map

    def read_license_classifiers(self):
        classifiers = self.package_data["info"]["classifiers"]
        return [c for c in classifiers if c.startswith("License")]

    def summary(self):
        summary = self.package_data["info"]["summary"]
        # summary may not be filled in the upstream data or it can consist of
        # more than one line - in both cases use the autogenerated string
        if not summary or len(summary.split("\n")) > 1:
            summary = "..."
        return summary

    def project_url(self):
        try:
            return self.package_data["info"]["project_urls"]["Homepage"]
        # It may happen that no project_urls nor Homepage are listed with the
        # project - in this case fall back to the safe PyPI URL
        except (KeyError, TypeError):
            return self.package_data["info"]["package_url"]

    def find_and_save_sdist_filename(self, version):
        """Save the given's package version sdist name for further processing.

        Quit the script if not found (bdists can't be processed).
        """
        for entry in self.package_data["releases"][version]:
            if entry["packagetype"] == "sdist":
                self.sdist_filename = entry["filename"]
                return
        # Not found, quit
        click.secho("sdist not found, quitting", fg="red")
        sys.exit(1)

    def is_zip_archive(self, version):
        """Return True if archive is a zip file, False otherwise.

        The archive format encouraged in PEP 517 is tar.gz, zip is discouraged,
        some projects however still use it.
        If so, it has to be explicitly declared as an argument of %{pypi_source}.
        """
        if self.sdist_filename is None:
            self.find_and_save_sdist_filename(version)
        if self.sdist_filename.endswith(".zip"):
            return True
        return False

    def archive_name(self, version):
        """Return the package name as spelled in the archive file.

        According to:
        https://packaging.python.org/en/latest/specifications/source-distribution-format/#source-distribution-file-name
        the `de facto` standard for sdist naming is '{name}-{version}.tar.gz'.
        The format is not standardised, so extract the {name} as defined by upstream.
        Example: "My-package_Archive-1.0.4-12.tar.gz" -> "My-package_Archive"
        """
        if self.sdist_filename is None:
            self.find_and_save_sdist_filename(version)

        edited_sdist_filename = self.sdist_filename
        # First, strip the suffix
        for suffix in (".tar.gz", ".zip"):
            edited_sdist_filename = edited_sdist_filename.removesuffix(suffix)
        # Second, get rid of the version string and the delimiter "-"
        archive_name = edited_sdist_filename.replace("-" + version, "")
        return archive_name


def changelog_head(email, name, changelog_date):
    """Return f'{date} {name} <{email}>'"""

    # Date is set for the tests
    if not changelog_date:
        changelog_date = (date.today()).strftime("%a %b %d %Y")

    if email or name:
        return f"{changelog_date} {name} <{email}>"

    try:
        result = check_output(["rpmdev-packager"])
        result = result.decode().strip()
    except FileNotFoundError:
        # Set a dummy value not to fail on missing changelog data
        result = "mockbuilder"

    return f"{changelog_date} {result}"


def changelog_msg():
    """Return a default changelog message."""

    return "Package generated with pyp2spec"


def get_description(package):
    """Return a default package description."""

    return f"This is package '{package}' generated automatically by pyp2spec."


def convert_version_to_rpm_scheme(version):
    """If version follows PEP 440, return its value converted to RPM scheme.

    PEP 440: https://www.python.org/dev/peps/pep-0440/
    If the package uses a different versioning scheme (i.e. LegacyVersion),
    the returned value will be the same as the input one.
    Such value may or may not work with RPM.
    Automatic conversion of the LegacyVersions is not feasible, as stated in:
    https://lists.fedoraproject.org/archives/list/python-devel@lists.fedoraproject.org/message/5MGEHMTKOKR5U7ACIMUDRBKMSP6Y5NQD/
    """
    return str(RpmVersion(version))


def is_package_name(package):
    """Check whether the string given as package contains `/`.
    Return True if not, False otherwise."""

    if "/" in package:
        # It's probably URL
        click.secho(f"Assuming '{package}' is a URL", fg="yellow")
        return False
    click.secho(f"Assuming '{package}' is a package name", fg="yellow")
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
    compliant=False,
    top_level=False,
    archful=False,
):
    """Use `package` and provided kwargs to create the whole config contents.
    Return contents dictionary.
    """
    contents = {}

    # a package name was given as the `package`, look for it on PyPI
    if is_package_name(package):
        pkg = PypiPackage(package, session)
        click.secho(f"Querying PyPI for package '{package}'", fg="cyan")
    # a URL was given as the `package`
    else:
        raise NotImplementedError

    # If the arguments weren't provided via CLI,
    # get them from the stored package object data or the default values
    if message is None:
        message = changelog_msg()
        click.secho(f"Assuming changelog --message={message}", fg="yellow")

    if description is None:
        description = get_description(package)
        click.secho(f"Assuming --description={description}", fg="yellow")

    if summary is None:
        summary = pkg.summary()
        click.secho(f"Assuming --summary={summary}", fg="yellow")

    if version is None:
        version = pkg.version()
        click.secho(f"Assuming PyPI --version={version}", fg="yellow")

    if license is None:
        license = pkg.license(compliant)
        click.secho(f"Assuming --license={license}", fg="yellow")

    if release is None:
        release = "1"
        click.secho(f"Assuming --release={release}", fg="yellow")

    if top_level:
        click.secho("Only top-level modules will be checked", fg="yellow")
        contents["test_top_level"] = True

    if archful:
        click.secho("Package is set to --archful", fg="magenta")
        click.secho("You may need to specify manual_build_requires in the config file", fg="magenta")
        contents["archful"] = archful

    contents["changelog_msg"] = message
    contents["changelog_head"] = changelog_head(email, name, date)
    contents["description"] = description
    contents["summary"] = summary
    contents["version"] = convert_version_to_rpm_scheme(version)
    contents["pypi_version"] = pkg.pypi_version_or_macro(version)
    contents["license"] = license
    contents["release"] = release
    contents["pypi_name"] = pkg.pypi_name
    contents["python_name"] = pkg.python_name()
    contents["url"] = pkg.project_url()
    contents["source"] = pkg.source(version)
    contents["archive_name"] = pkg.archive_name(version)

    return contents


def save_config(contents, output=None):
    """Write config file to a given destination.
    If none is provided, save it to current directory with package name as file name.
    Return the saved file name.
    """
    if not output:
        package = contents["python_name"]
        output = f"./{package}.conf"
    with open(output, "wb") as f:
        click.secho(f"Saving configuration file to '{output}'", fg="yellow")
        tomli_w.dump(contents, f, multiline_strings=True)
    click.secho("Configuration file was saved successfully", fg="green")
    return output


def create_config(options):
    """Create and save config file."""

    contents = create_config_contents(
        options["package"],
        description=options["description"],
        release=options["release"],
        message=options["message"],
        email=options["email"],
        name=options["packager"],
        version=options["version"],
        summary=options["summary"],
        license=options["license"],
        compliant=options["fedora_compliant"],
        top_level=options["top_level"],
        archful=options["archful"],
    )
    return save_config(contents, options["config_output"])


@click.command()
@click.argument("package")
@click.option(
    "--config-output", "-c",
    help="Provide custom output for configuration file",
)
@click.option(
    "--description", "-d",
    help="Provide description for the package",
)
@click.option(
    "--release", "-r",
    help="Provide Fedora release, default: 1",
)
@click.option(
    "--message", "-m",
    help="Provide custom changelog message for the package",
)
@click.option(
    "--email", "-e",
    help="Provide e-mail for changelog, default: output of `rpmdev-packager`",
)
@click.option(
    "--packager", "-p",
    help="Provide packager name for changelog, default: output of `rpmdev-packager`",
)
@click.option(
    "--version", "-v",
    help="Provide package version to query PyPI for, default: latest",
)
@click.option(
    "--summary", "-s",
    help="Provide custom package summary",
)
@click.option(
    "--license", "-l",
    help="Provide license name",
)
@click.option(
    "--fedora-compliant", is_flag=True,
    help="Check whether license is compliant with Fedora",
)
@click.option(
    "--top-level", "-t", is_flag=True,
    help="Test only top-level modules in %check",
)
@click.option(
    "--archful", "-a", is_flag=True,
    help="Set if the resulting RPM should be arched",
)
def main(**options):
    create_config(options)


if __name__ == "__main__":
    main()
