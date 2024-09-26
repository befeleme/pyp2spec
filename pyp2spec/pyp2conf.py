from functools import wraps
import re
import sys

import click
import requests
import tomli_w

from packaging.requirements import Requirement

from pyp2spec.rpmversion import RpmVersion
from pyp2spec.license_processor import classifiers_to_spdx_identifiers
from pyp2spec.license_processor import license_keyword_to_spdx_identifiers, good_for_fedora
from pyp2spec.utils import Pyp2specError


class NoLicenseDetectedError(Pyp2specError):
    """Raised when there's no valid license detected"""


class SdistNotFoundError(Pyp2specError):
    """Raised when there's no sdist file in the PyPI metadata"""


class PackageNotFoundError(Pyp2specError):
    """Raised when there's no such package name on PyPI"""


class PypiPackage:
    """Store and process the package data obtained from PyPI.

    It's possible to create the object these ways:
    - providing a package name.
    A request is made to PyPI general project API to find the latest available version.
    Another request is made to the PyPI package version API to obtain all
    package data related to that particular distribution.
    - providing a package name and a version.
    A request is made to the PyPI package version API to obtain all
    package data related to that particuler distribution.
    - providing a package name, version and custom package metadata
    (dictionary with the same structure as PyPI package version API).
    No requests to PyPI are made, the package metadata serve as the source
    to create a PypiPackage object.
    This is only relevant for testing.
    """

    def __init__(self, package_name, *, version=None, package_metadata=None, session=None):
        self.package_name = package_name
        self._session = session or requests.Session()
        self.version = version or self._get_version_from_package_metadata()
        # package_metadata - custom dictionary with package metadata - used for testing
        # in the typical app run it's not set,
        # meaning we jump to the other sources package metadata data (eg. PyPI)
        self.package_data = package_metadata or self._get_package_version_metadata()
        self.sdist_filename = None

    @property
    def pypi_name(self):
        """Return normalized PyPI package name (as defined in PEP 503).
        The resulting string better conforms with Fedora's Packaging Guidelines.
        """

        return self.normalize(self.package_data["info"]["name"])

    def normalize(self, package_name):
        """Normalize given package name as defined in PEP 503"""

        return re.sub(r"[-_.]+", "-", package_name).lower()

    def _get_from_url(self, url, error_str):
        response = self._session.get(url)
        if not response.ok:
            raise PackageNotFoundError(error_str)
        return response.json()

    def _get_package_project_metadata(self):
        pkg_index = f"https://pypi.org/pypi/{self.package_name}/json"
        error_str = f"Package `{self.package_name}` was not found on PyPI"
        return self._get_from_url(pkg_index, error_str)

    def _get_version_from_package_metadata(self):
        package_metadata = self._get_package_project_metadata()
        return package_metadata["info"]["version"]

    def _get_package_version_metadata(self):
        pkg_index = f"https://pypi.org/pypi/{self.package_name}/{self.version}/json"
        error_str = f"Package `{self.package_name}` or version `{self.version}` was not found on PyPI"
        return self._get_from_url(pkg_index, error_str)

    def python_name(self, *, python_alt_version=None):
        """Create a component name for the specfile.

        Prepend the name with 'python' (unless it already starts with it).
        Add the Python alternative version, if it's defined.

        Valid outcomes:
        package name: foo, python_alt_version: 3.11
        -> python3.11-foo

        package name: foo, python_alt_version: None
        -> python-foo

        package name: python-foo, python_alt_version: 3.12
        -> python3.12-foo

        package name: python-foo, python_alt_version: None
        -> python-foo
        """

        alt_version = "" if python_alt_version is None else python_alt_version
        if self.pypi_name.startswith("python"):
            return self.pypi_name.replace("python", f"python{alt_version}")
        return f"python{alt_version}-{self.pypi_name}"

    def source(self):
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
        is_zip = self.is_zip_archive()
        version_str = self.pypi_version_or_macro()

        source_macro_args = self.archive_name()

        if is_zip:
            source_macro_args += f" {version_str} zip"
        else:
            if version_str == self.version:
                source_macro_args += f" {version_str}"

        return "%{pypi_source " + source_macro_args + "}"

    def pypi_version_or_macro(self):
        """If PyPI and RPM version's strings are the same, there's no need to
        duplicate them across the spec file.
        Return '%{version}' as a reference to the RPM's version string.
        If they are different, both variants of string need to be used.
        In such case return version string as from PyPI.
        """
        rpm_version = convert_version_to_rpm_scheme(self.version)
        if self.version == rpm_version:
            return "%{version}"
        return self.version

    def filter_license_classifiers(self):
        """Return the list of license classifiers defined for the package.

        Filter out the parent categories `OSI-/DFSG Approved` which don't have any meaning.
        """

        return  [
            c for c in self.package_data["info"]["classifiers"]
            if (
                c.startswith("License")
                and c not in ("License :: OSI Approved", "License :: DFSG approved")
            )
        ]

    def transform_to_spdx(self):
        """Return SPDX identifiers and expression based on the found
        package license metadata (classifiers or license keyword).
        
        If multiple identifiers are found, create an expression that's the safest option (with AND as joining operator).
        """

        if (license_classifiers := self.filter_license_classifiers()):
            identifiers = classifiers_to_spdx_identifiers(license_classifiers)
            if identifiers:
                expression = " AND ".join(identifiers)
                return (identifiers, expression)

        license_keyword = self.package_data["info"]["license"]
        identifiers = license_keyword_to_spdx_identifiers(license_keyword)

        return (identifiers, license_keyword)

    def license(self, *, check_compliance=False, licenses_dict=None):
        """Return the license string from package metadata.

        If `check_compliance` is set to True, check each of the found
        SPDX identifiers against the Fedora allowed licenses.
        This isn't a 100% reliable solution and in case of ambiguous results,
        the license is discarded as invalid.
        """

        identifiers, expression = self.transform_to_spdx()
        if not identifiers:
            inspect_notice = "Inspect the project manually to find the license."
            if expression:
                err_string = f"WARNING: The found license `{expression}` is not a valid SPDX expression. " + inspect_notice
                click.secho(err_string, fg="red")
            else:
                err_string = "WARNING: No license found. " + inspect_notice
                click.secho(err_string, fg="red")
            return None
        if check_compliance:
            is_compliant, checked_identifiers = good_for_fedora(
                    identifiers,
                    session=self._session,
                    licenses_dict=licenses_dict
            )
            if checked_identifiers["bad"]:
                err_string = "Found identifiers: `{0}` aren't allowed in Fedora."
                click.secho(err_string.format(", ".join(checked_identifiers["bad"])), fg="red")
            if checked_identifiers["good"]:
                err_string = "Found identifiers: `{0}` are good for Fedora."
                click.secho(err_string.format(", ".join(checked_identifiers["good"])), fg="green")
            if not is_compliant:
                return None
        return expression

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

    def is_archful(self):
        """Determine if package is archful by checking the wheel filenames.

        Wheel name consists of defined fields, one of them being an abi tag.
        Example abi tags:
        - click-0.2-py2.py3-none-any.whl -> "none"
        - cryptography-2.2-cp34-abi3-manylinux1_x86_64.whl -> "abi3"
        If the value is "none", wheel was not built for a specific architecture,
        probably containing pure Python modules.
        Other values indicate build for an architechture, which can mean
        the presence of compiled extensions.
        Packages can publish multiple wheels, the pure-Python alongside the compiled ones.
        For our purposes, if we find at least one wheel with an abi tag different that "none",
        we consider the package archful.
        The compiled extensions bring optimizations and in Fedora,
        it is generally encouraged to bring in the optional features of the packages.
        """

        for entry in self.package_data["urls"]:
            if entry["packagetype"] == "bdist_wheel":
                abi_tag = entry["filename"].split("-")[-2]
                if abi_tag != "none":
                    return True
        # all of the found wheel names had 'none' as abi_tag
        return False

    def find_and_save_sdist_filename(self):
        """Save the given's package version sdist name for further processing.

        Quit the script if not found (bdists can't be processed).
        """
        for entry in self.package_data["urls"]:
            if entry["packagetype"] == "sdist":
                self.sdist_filename = entry["filename"]
                return
        raise SdistNotFoundError("sdist not found.")

    def is_zip_archive(self):
        """Return True if archive is a zip file, False otherwise.

        The archive format encouraged in PEP 517 is tar.gz, zip is discouraged,
        some projects however still use it.
        If so, it has to be explicitly declared as an argument of %{pypi_source}.
        """
        if self.sdist_filename is None:
            self.find_and_save_sdist_filename()
        if self.sdist_filename.endswith(".zip"):
            return True
        return False

    def archive_name(self):
        """Return the package name as spelled in the archive file.

        According to:
        https://packaging.python.org/en/latest/specifications/source-distribution-format/#source-distribution-file-name
        the `de facto` standard for sdist naming is '{name}-{version}.tar.gz'.
        The format is not standardised, so extract the {name} as defined by upstream.
        Example: "My-package_Archive-1.0.4-12.tar.gz" -> "My-package_Archive"
        """
        if self.sdist_filename is None:
            self.find_and_save_sdist_filename()

        edited_sdist_filename = self.sdist_filename
        # First, strip the suffix
        for suffix in (".tar.gz", ".zip"):
            edited_sdist_filename = edited_sdist_filename.removesuffix(suffix)
        # Second, get rid of the version string and the delimiter "-"
        archive_name = edited_sdist_filename.replace("-" + self.version, "")
        return archive_name

    def extras(self):
        """Return the sorted list of the found extras names.

        Packages define extras explicitly via `Provides-Extra` and
        indirectly via `Requires-Dist` metadata.
        PyPI metadata doesn't provide the first one, but it is possible to
        derive extras names from the `requires_dist` key.
        Example value of `requires_dist`:
        ["sphinxcontrib-websupport ; extra == 'docs'", "flake8>=3.5.0 ; extra == 'lint'"]
        If package defines an extra with no requirements, we can't detect that.
        """
        extra_from_req = re.compile(r'''\bextra\s+==\s+["']([^"']+)["']''')
        extras = set()
        requires_dist = self.package_data["info"]["requires_dist"]
        if requires_dist is not None:
            for required_dist in requires_dist:
                # packaging.Requirement can parse the markers, but it
                # doesn't provide their string representations,
                # hence we need to use regex to pick them out
                req = Requirement(required_dist)
                if found := re.search(extra_from_req, str(req.marker)):
                    extras.add(found.group(1))
        return sorted(extras)


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
    """Least-effort check whether `package` is a package name or URL.
    Canonical package names can't contain '/'.
    """

    return not "/" in package


def create_config_contents(
    package,
    version=None,
    session=None,
    compliant=False,
    python_alt_version=None,
    automode=False,
):
    """Use `package` and provided kwargs to create the whole config contents.
    Return contents dictionary.
    """
    contents = {}

    # a package name was given as the `package`, look for it on PyPI
    if is_package_name(package):
        click.secho(f"Assuming '{package}' is a package name", fg="yellow")
        pkg = PypiPackage(package, version=version, session=session)
        click.secho(f"Querying PyPI for package '{package}'", fg="cyan")
    # a URL was given as the `package`
    else:
        raise NotImplementedError("pyp2spec can't currently handle URLs.")

    if version is None:
        click.secho(f"Assuming PyPI --version={pkg.version}", fg="yellow")

    if (license := pkg.license(check_compliance=compliant)) is not None:
        contents["license"] = license

    if automode:
        contents["automode"] = True

    if archful := pkg.is_archful():
        click.secho("Package is archful - you may need to specify additional build requirements", fg="magenta")

    if python_alt_version is not None:
        click.secho(f"Assuming build for Python: {python_alt_version}", fg="yellow")
        contents["python_alt_version"] = python_alt_version

    contents["archful"] = archful
    contents["description"] = get_description(package)
    contents["summary"] = pkg.summary()
    contents["version"] = convert_version_to_rpm_scheme(pkg.version)
    contents["pypi_version"] = pkg.pypi_version_or_macro()
    contents["pypi_name"] = pkg.pypi_name
    contents["python_name"] = pkg.python_name(python_alt_version=python_alt_version)
    contents["url"] = pkg.project_url()
    contents["source"] = pkg.source()
    contents["archive_name"] = pkg.archive_name()
    contents["extras"] = pkg.extras()

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
        version=options["version"],
        compliant=options["fedora_compliant"],
        python_alt_version=options["python_alt_version"],
        automode=options["automode"]
    )
    return save_config(contents, options["config_output"])


def pypconf_args(func):
    @click.argument("package")
    @click.option(
        "--config-output", "-c",
        help="Provide custom output for configuration file",
    )
    @click.option(
        "--version", "-v",
        help="Provide package version to query PyPI for, default: latest",
    )
    @click.option(
        "--fedora-compliant", is_flag=True,
        help="Check whether license is compliant with Fedora",
    )
    @click.option(
        "--automode", "-a", is_flag=True,
        help="Enable buildability of the generated spec in automated environments",
    )
    @click.option(
        "--python-alt-version", "-p",
        help="Provide specific Python version to build for, e.g 3.11",
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@click.command()
@pypconf_args
def main(**options):
    try:
        create_config(options)
    except (Pyp2specError, NotImplementedError) as exc:
        click.secho(f"Fatal exception occurred: {exc}", fg="red")
        sys.exit(1)

if __name__ == "__main__":
    main()
