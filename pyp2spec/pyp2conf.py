from functools import wraps
import email.parser
import re
import sys

import click
import requests
import tomli_w

from packaging.requirements import Requirement

from pyp2spec.rpmversion import RpmVersion
from pyp2spec.license_processor import classifiers_to_spdx_identifiers
from pyp2spec.license_processor import license_keyword_to_spdx_identifiers, good_for_fedora
from pyp2spec.utils import Pyp2specError, normalize


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

    def __init__(self, package_name, *, version=None, pypi_package_data=None, core_metadata=None, session=None):
        self.package_name = package_name
        self._session = session or requests.Session()
        self.version = version or self._get_version_from_pypi_package_data()
        # package_metadata - custom dictionary with package metadata - used for testing
        # in the typical app run it's not set,
        # meaning we jump to the other sources package metadata data (eg. PyPI)
        self.pypi_package_data = pypi_package_data or self._get_pypi_package_version_data()
        self.core_metadata = core_metadata or self.parse_core_metadata()
        self.sdist_filename = None

    @property
    def pypi_name(self):
        """Return normalized PyPI package name (as defined in PEP 503).
        The resulting string better conforms with Fedora's Packaging Guidelines.
        """

        return normalize(self.pypi_package_data["info"]["name"])

    def _get_from_url(self, url, error_str):
        response = self._session.get(url)
        if not response.ok:
            raise PackageNotFoundError(error_str)
        return response.json()

    def _get_pypi_package_project_data(self):
        pkg_index = f"https://pypi.org/pypi/{self.package_name}/json"
        error_str = f"Package `{self.package_name}` was not found on PyPI"
        return self._get_from_url(pkg_index, error_str)

    def _get_version_from_pypi_package_data(self):
        package_metadata = self._get_pypi_package_project_data()
        return package_metadata["info"]["version"]

    def _get_pypi_package_version_data(self):
        pkg_index = f"https://pypi.org/pypi/{self.package_name}/{self.version}/json"
        error_str = f"Package `{self.package_name}` or version `{self.version}` was not found on PyPI"
        return self._get_from_url(pkg_index, error_str)

    def _get_metadata_file(self):
        for entry in self.pypi_package_data["urls"]:
            if entry["packagetype"] == "bdist_wheel":
                response = self._session.get(entry["url"] + ".metadata")
                if not response.ok:
                    click.secho("The metadata file could not be located", fg="red")
                    response.text = None
                return response.text

    def parse_core_metadata(self):
        metadata = self._get_metadata_file()
        parser = email.parser.Parser()
        return parser.parsestr(metadata)

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

    def filter_license_classifiers(self):
        """Return the list of license classifiers defined for the package.

        Filter out the parent categories `OSI-/DFSG Approved` which don't have any meaning.
        """

        return  [
            c for c in self.pypi_package_data["info"]["classifiers"]
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

        license_keyword = self.pypi_package_data["info"]["license"]
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
            inspect_notice = "Inspect the project manually to find the license"
            if expression:
                err_string = (f"WARNING: The found license expression '{expression}' "
                    "is not a valid SPDX expression. " + inspect_notice)
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
                err_string = "Found identifiers: '{0}' aren't allowed in Fedora."
                click.secho(err_string.format(", ".join(checked_identifiers["bad"])), fg="red")
            if checked_identifiers["good"]:
                err_string = "Found identifiers: '{0}' are good for Fedora."
                click.secho(err_string.format(", ".join(checked_identifiers["good"])), fg="yellow")
            if not is_compliant:
                return None
        return expression

    def summary(self):
        summary = self.pypi_package_data["info"]["summary"]
        # summary may not be filled in the upstream data or it can consist of
        # more than one line - in both cases use the autogenerated string
        if not summary or len(summary.split("\n")) > 1:
            summary = "..."
        return summary

    def project_url(self):
        try:
            return self.pypi_package_data["info"]["project_urls"]["Homepage"]
        # It may happen that no project_urls nor Homepage are listed with the
        # project - in this case fall back to the safe PyPI URL
        except (KeyError, TypeError):
            return self.pypi_package_data["info"]["package_url"]

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

        for entry in self.pypi_package_data["urls"]:
            if entry["packagetype"] == "bdist_wheel":
                abi_tag = entry["filename"].split("-")[-2]
                if abi_tag != "none":
                    return True
        # all of the found wheel names had 'none' as abi_tag
        return False

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
        requires_dist = self.pypi_package_data["info"]["requires_dist"]
        if requires_dist is not None:
            for required_dist in requires_dist:
                # packaging.Requirement can parse the markers, but it
                # doesn't provide their string representations,
                # hence we need to use regex to pick them out
                req = Requirement(required_dist)
                if found := re.search(extra_from_req, str(req.marker)):
                    extras.add(found.group(1))
        return sorted(extras)

    def are_license_files_included(self):
        return bool(self.core_metadata.get_all("License-File"))


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
        click.secho(f"Querying PyPI for package '{package}'", fg="yellow")
        pkg = PypiPackage(package, version=version, session=session)
    # a URL was given as the `package`
    else:
        raise NotImplementedError("pyp2spec can't currently handle URLs.")

    if version is None:
        click.secho(f"Assuming the latest version found on PyPI: '{pkg.version}'", fg="yellow")

    if (license := pkg.license(check_compliance=compliant)) is not None:
        contents["license"] = license

    if automode:
        contents["automode"] = True

    if archful := pkg.is_archful():
        click.secho("Package contains compiled extensions - you may need to specify additional build requirements", fg="magenta")

    if python_alt_version is not None:
        click.secho(f"Assuming build for Python: {python_alt_version}", fg="yellow")
        contents["python_alt_version"] = python_alt_version

    contents["archful"] = archful
    contents["summary"] = pkg.summary()
    contents["pypi_version"] = pkg.version
    contents["pypi_name"] = pkg.pypi_name
    contents["python_name"] = pkg.python_name(python_alt_version=python_alt_version)
    contents["url"] = pkg.project_url()
    contents["source"] = "PyPI"
    contents["extras"] = pkg.extras()
    contents["license_files_present"] = pkg.are_license_files_included()

    return contents


def save_config(contents, output=None):
    """Write config file to a given destination.
    If none is provided, save it to current directory with package name as file name.
    Return the saved file name.
    """
    if not output:
        package = contents["python_name"]
        output = f"{package}.conf"
    with open(output, "wb") as f:
        tomli_w.dump(contents, f, multiline_strings=True)
    click.secho(f"Configuration file was saved successfully to '{output}'")
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
