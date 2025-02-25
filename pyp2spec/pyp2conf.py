from __future__ import annotations
from dataclasses import dataclass, asdict, field
from functools import wraps
import sys

import click
import tomli_w
from packaging.metadata import RawMetadata
from requests import Session

from pyp2spec.license_processor import check_compliance, resolve_license_expression
from pyp2spec.utils import Pyp2specError, normalize_name, get_extras, get_summary_or_placeholder
from pyp2spec.utils import prepend_name_with_python, archive_name
from pyp2spec.utils import is_archful, resolve_url, create_compat_name
from pyp2spec.utils import warn, caution, inform, yay
from pyp2spec.pypi_loaders import load_from_pypi, load_core_metadata_from_pypi, CoreMetadataNotFoundError


@dataclass
class PackageInfo:
    pypi_name: str
    pypi_version: str
    summary: str
    url: str
    extras: list
    license_files_present: bool
    license: str | None = None
    source: str = "PyPI"  # only one default source now
    # These are added later, when the object is already constructed:
    python_name: str = field(init=False)
    archful: bool = field(init=False)
    archive_name: str = field(init=False)
    # These may or may not be ever set
    python_alt_version: str | None = field(default=None)
    automode: bool | None = field(default=None)
    compat: str | None = field(default=None)


def is_package_name(package: str) -> bool:
    """Least-effort check whether `package` is a package name or URL.
    Canonical package names can't contain '/'.
    """

    return "/" not in package


def prepare_package_info(data: RawMetadata | dict) -> PackageInfo:
    if not (project_urls := data.get("project_urls", {})):
        if (homepage := data.get("home_page", "")):
            project_urls["home_page"] = homepage
    return PackageInfo(
        pypi_name=normalize_name(data.get("name", "")),
        pypi_version=data.get("version", ""),
        summary=get_summary_or_placeholder(data.get("summary", "")),
        url=resolve_url(project_urls),
        extras=get_extras(data.get("requires_dist", [])),
        license_files_present=bool(data.get("license_files")),
        license=resolve_license_expression(data)
    )


def add_archive_data(pkg: PackageInfo, pypi_data: dict) -> PackageInfo:
    """We can obtain the archive information from PyPI only."""
    pkg.archful = is_archful(pypi_data["urls"])
    pkg.archive_name = archive_name(pypi_data["urls"])
    return pkg


def gather_package_info(core_metadata: RawMetadata | None, pypi_package_data: dict) -> PackageInfo:
    if core_metadata is not None:
        pkg = prepare_package_info(core_metadata)
    else:
        pkg = prepare_package_info(pypi_package_data["info"])
    pkg = add_archive_data(pkg, pypi_package_data)
    return pkg


def create_package_from_source(
    package: str,
    version: str | None,
    compat: str | None,
    session: Session | None
) -> PackageInfo:
    """Determine the best source for the given package name and create a PackageInfo instance.
    """
    if is_package_name(package):
        # explicit `session` argument is needed for testing
        pypi_pkg_data = load_from_pypi(package, version=version,
        compat=compat, session=session)
        try:
            core_metadata = load_core_metadata_from_pypi(pypi_pkg_data, session=session)
        # if no core metadata found, we will fall back to PyPI API
        except CoreMetadataNotFoundError:
            core_metadata = None
    else:
        raise NotImplementedError("pyp2spec can't currently handle URLs.")
    # The processed package info is the basis for config contents
    return gather_package_info(core_metadata, pypi_pkg_data)


def create_config_contents(
    options: dict[str, Any],
    session: Session | None = None
) -> dict:
    """Use `package` and provided options to create the whole config contents.
    Return pkg_info dictionary.
    """

    package = options.get("package")
    version = options.get("version")
    compat = options.get("compat")
    pkg_info = create_package_from_source(package, version, compat, session)

    python_alt_version = options.get("python_alt_version")
    pkg_info.python_name = prepend_name_with_python(pkg_info.pypi_name, python_alt_version)

    if compat is not None:
        inform(f"Creating a compat package for version: '{compat}'")
        pkg_info.compat = compat

    if version is None:
        inform(f"Assuming the version found on PyPI: '{pkg_info.pypi_version}'")

    if pkg_info.archful:
        caution("Package contains compiled extensions - you may need to specify additional build requirements")

    if pkg_info.license is None:
        warn("WARNING: No valid license found. Inspect the project manually to find the license")
    else:
        if options.get("fedora_compliant"):
            is_compliant, results = check_compliance(pkg_info.license, session=session)
            if not is_compliant:
                warn(f"The license '{pkg_info.license}' is not compliant with Fedora")
            if results["bad"]:
                info_str = "Found identifiers: '{0}' aren't allowed in Fedora."
                warn(info_str.format(", ".join(results["bad"])))
            if results["good"]:
                info_str = "Found identifiers: '{0}' are good for Fedora."
                inform(info_str.format(", ".join(results["good"])))

    # Configuration settings
    if python_alt_version is not None:
        inform(f"Assuming build for Python: {python_alt_version}")
        pkg_info.python_alt_version = python_alt_version

    if options.get("automode"):
        pkg_info.automode = True

    pkg_dict = asdict(pkg_info)
    # sort the dictionary alphabetically for output consistency
    # only keep the values that aren't None - TOML can't handle that
    return {key: pkg_dict[key] for key in sorted(pkg_dict.keys()) if pkg_dict[key] is not None}


def save_config(contents: dict, output: str | None = None) -> str:
    """Write config file to a given destination.
    If none is provided, save it to current directory with package name as file name.
    Return the saved file name.
    """
    if not output:
        package_name = create_compat_name(contents.get("python_name"), contents.get("compat"))
        output = f"{package_name}.conf"
    with open(output, "wb") as f:
        tomli_w.dump(contents, f, multiline_strings=True)
    yay(f"Configuration file was saved successfully to '{output}'")
    return output


def create_config(options: dict) -> str:
    """Create and save config file."""

    contents = create_config_contents(options)
    return save_config(contents, options["config_output"])


def pypconf_args(func):  # noqa
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
    @click.option(
        "--compat",
        help="Create a compat package for a given version",
    )
    @wraps(func)
    def wrapper(*args, **kwargs): # noqa
        return func(*args, **kwargs)
    return wrapper

@click.command()
@pypconf_args
def main(**options):  # noqa
    try:
        create_config(options)
    except (Pyp2specError, NotImplementedError) as exc:
        warn(f"Fatal exception occurred: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
