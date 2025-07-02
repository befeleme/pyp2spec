from __future__ import annotations
from dataclasses import dataclass, asdict, field
from functools import wraps
from typing import Any
import sys

import click
import tomli_w
from packaging.metadata import RawMetadata
from requests import Session

from pyp2spec.license_processor import check_compliance, resolve_license_expression
from pyp2spec.utils import Pyp2specError, normalize_name, get_extras, get_summary_or_placeholder
from pyp2spec.utils import prepend_name_with_python, archive_name
from pyp2spec.utils import has_abi_tag, contains_wheel_with_abi_tag, resolve_url, create_compat_name
from pyp2spec.utils import warn, caution, inform, yay
from pyp2spec.pypi_loaders import load_from_pypi, load_core_metadata_from_pypi, CoreMetadataNotFoundError
from pyp2spec.local_loaders import load_dist_data_from_dir


@dataclass
class PackageInfo:
    name: str
    version: str
    summary: str
    url: str
    extras: list
    license_files_present: bool
    license: str | None = None
    # These are added later, when the object is already constructed:
    source: str = field(init=False)
    python_name: str = field(init=False)
    archful: bool = field(init=False)
    archive_name: str = field(init=False)
    # These may or may not be ever set
    python_alt_version: str | None = field(default=None)
    automode: bool | None = field(default=None)
    compat: str | None = field(default=None)


def prepare_package_info(data: RawMetadata | dict) -> PackageInfo:
    if not (project_urls := data.get("project_urls") or {}):
        if (homepage := data.get("home_page", "")):
            project_urls["home_page"] = homepage
        if (not homepage and (homepage := data.get("project_url", ""))):
            project_urls["home_page"] = homepage
        if (not homepage and (homepage := data.get("package_url", ""))):
            project_urls["home_page"] = homepage
    return PackageInfo(
        name=normalize_name(data.get("name", "")),
        version=data.get("version", ""),
        summary=get_summary_or_placeholder(data.get("summary", "")),
        url=resolve_url(project_urls),
        extras=get_extras(data.get("provides_extra", []), data.get("requires_dist", [])),
        license_files_present=bool(data.get("license_files")),
        license=resolve_license_expression(data)
    )


def gather_package_info(core_metadata: RawMetadata | None, pypi_package_data: dict[str, str] | None) -> PackageInfo:
    if core_metadata is not None:
        pkg = prepare_package_info(core_metadata)
    else:
        pkg = prepare_package_info(pypi_package_data["info"])
    return pkg


def create_package_from_dir(package: str, path: str) -> PackageInfo:
    sdist_name, wheel_name, core_metadata = load_dist_data_from_dir(package, path)
    pkg = gather_package_info(core_metadata, None)
    pkg.archful = has_abi_tag(str(wheel_name))
    pkg.archive_name = sdist_name
    pkg.source = "local"
    return pkg


def create_package_from_pypi(core_metadata: RawMetadata | None, pypi_pkg_data: dict) -> PackageInfo:
    pkg = gather_package_info(core_metadata, pypi_pkg_data)
    pkg.archful = contains_wheel_with_abi_tag(pypi_pkg_data["urls"])
    pkg.archive_name = archive_name(pypi_pkg_data["urls"])
    pkg.source = "PyPI"
    return pkg


def create_package_from_source(
    package: str,
    version: str | None,
    compat: str | None,
    path: str | None,
    session: Session | None
) -> PackageInfo:
    """Determine the best source for the given package name and create a PackageInfo instance.
    """
    if path is not None:
        pkg = create_package_from_dir(package, path)
    else:
        # explicit `session` argument is needed for testing
        pypi_pkg_data = load_from_pypi(package, version=version,
        compat=compat, session=session)
        try:
            core_metadata = load_core_metadata_from_pypi(pypi_pkg_data, session=session)
        # if no core metadata found, we will fall back to PyPI API
        except CoreMetadataNotFoundError:
            core_metadata = None
        pkg = create_package_from_pypi(core_metadata, pypi_pkg_data)
    return pkg


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
    path = options.get("path")
    pkg_info = create_package_from_source(package, version, compat, path, session)

    python_alt_version = options.get("python_alt_version")
    pkg_info.python_name = prepend_name_with_python(pkg_info.name, python_alt_version)

    if compat is not None:
        inform(f"Creating a compat package for version: '{compat}'")
        pkg_info.compat = compat

    if version is None:
        inform(f"No version specified, assuming the version found: '{pkg_info.version}'")

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
        "--path",
        help="Path to a directory where sdist and wheel are stored locally",
    )
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
