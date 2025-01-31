from functools import wraps
import sys

import click
import tomli_w

from pyp2spec.license_processor import check_compliance, resolve_license_expression
from pyp2spec.utils import Pyp2specError, normalize_name, get_extras, get_summary_or_placeholder
from pyp2spec.utils import prepend_name_with_python, archive_name
from pyp2spec.utils import is_archful, resolve_url
from pyp2spec.utils import warn, caution, inform, yay
from pyp2spec.pypi_loaders import load_from_pypi, load_core_metadata_from_pypi, CoreMetadataNotFoundError


def is_package_name(package):
    """Least-effort check whether `package` is a package name or URL.
    Canonical package names can't contain '/'.
    """

    return "/" not in package


def prepare_package_info(data):
    if not (project_urls := data.get("project_urls", {})):
        if (homepage := data.get("home_page", "")):
            project_urls["home_page"] = homepage
    return {
        "pypi_name": normalize_name(data.get("name")),
        "pypi_version": data.get("version"),
        "summary": get_summary_or_placeholder(data.get("summary")),
        "url": resolve_url(project_urls),
        "extras": get_extras(data.get("requires_dist", [])),
        "license_files_present": bool(data.get("license_files")),
        "license": resolve_license_expression(data),
    }


def add_archive_data(pkg, pypi_data):
    """We can obtain the archive information from PyPI only."""
    pkg["archful"] = is_archful(pypi_data["urls"])
    pkg["archive_name"] = archive_name(pypi_data["urls"])
    return pkg


def gather_package_info(core_metadata, pypi_package_data):
    if core_metadata is not None:
        pkg = prepare_package_info(core_metadata)
    else:
        pkg = prepare_package_info(pypi_package_data["info"])
    pkg = add_archive_data(pkg, pypi_package_data)
    return pkg


def create_config_contents(
    package,
    version=None,
    session=None,
    compliant=False,
    python_alt_version=None,
    automode=False,
):
    """Use `package` and provided kwargs to create the whole config contents.
    Return pkg_info dictionary.
    """
    if is_package_name(package):
        # explicit `session` argument is needed for testing
        pypi_pkg_data = load_from_pypi(package, version=version, session=session)
        try:
            core_metadata = load_core_metadata_from_pypi(pypi_pkg_data, session=session)
        # if no core metadata found, we will fall back to PyPI API
        except CoreMetadataNotFoundError:
            core_metadata = None
    else:
        raise NotImplementedError("pyp2spec can't currently handle URLs.")

    # The processed package info is the basis for config contents
    pkg_info = gather_package_info(core_metadata, pypi_pkg_data)

    pkg_info["python_name"] = prepend_name_with_python(pkg_info["pypi_name"], python_alt_version)

    if python_alt_version is not None:
        inform(f"Assuming build for Python: {python_alt_version}")
        pkg_info["python_alt_version"] = python_alt_version

    if version is None:
        ver = pkg_info["pypi_version"]
        inform(f"Assuming the latest version found on PyPI: '{ver}'")

    if pkg_info["archful"]:
        caution("Package contains compiled extensions - you may need to specify additional build requirements")

    if pkg_info["license"] is None:
        warn("WARNING: No valid license found. Inspect the project manually to find the license")
        # TOML can't handle None value; we don't need this key explicitly
        del pkg_info["license"]
    else:
        if compliant:
            is_compliant, results = check_compliance(pkg_info["license"], session=session)
            if not is_compliant:
                warn(f"The license '{pkg_info['license']}' is not compliant with Fedora")
            if results["bad"]:
                info_str = "Found identifiers: '{0}' aren't allowed in Fedora."
                warn(info_str.format(", ".join(results["bad"])))
            if results["good"]:
                info_str = "Found identifiers: '{0}' are good for Fedora."
                inform(info_str.format(", ".join(results["good"])))

    if automode:
        pkg_info["automode"] = True

    # The default source of archives pyp2spec can process
    pkg_info["source"] = "PyPI"

    # sort the dictionary alphabetically for output consistency
    return {key: pkg_info[key] for key in sorted(pkg_info.keys())}


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
    yay(f"Configuration file was saved successfully to '{output}'")
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
        warn(f"Fatal exception occurred: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
