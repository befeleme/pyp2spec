from __future__ import annotations

import sys

from importlib.resources import files
from typing import Any

import click

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from jinja2 import Template

from pyp2spec.rpmversion import RpmVersion
from pyp2spec.utils import Pyp2specError, create_compat_name
from pyp2spec.utils import warn, yay


TEMPLATE_FILENAME = "template.spec"
ADDITIONAL_BUILD_REQUIRES_ARCHFUL = ["gcc"]
ADDITIONAL_BUILD_REQUIRES_NOARCH: list[str] = []


class ConfigError(Pyp2specError):
    """Raised when a config value has got a wrong type"""


class ConfigFile:
    """Validate configuration data."""

    def __init__(self, contents: dict) -> None:
        self.contents = contents

    def get_string(self, key: str) -> str:
        """Return a value for given key. Validate the value is a string.
        Raise ConfigError otherwise."""

        return self._get_value(key, str)

    def get_list(self, key: str) -> str:
        """Return a value for given key. Validate the value is a list.
        Raise ConfigError otherwise."""

        return self._get_value(key, list)

    def get_bool(self, key: str) -> str:
        """Return a value for given key. Validate the value is a boolean.
        Raise ConfigError otherwise."""

        return self._get_value(key, bool)

    def _get_value(self, key: str, val_type: type) -> Any:
        val = self.contents.get(key, val_type())
        if not isinstance(val, val_type):
            raise ConfigError(f"{val} must be a {val_type}")
        return val


def load_config_file(filename: str) -> dict:
    """Return loaded TOML configuration file contents."""

    with open(filename, "rb") as configuration_file:
        return tomllib.load(configuration_file)


def list_additional_build_requires(config: ConfigFile) -> list[str]:
    """Returns a list of additionally defined BuildRequires,

    The list differs for packages that are or aren't archful.
    """
    if config.get_bool("archful"):
        return ADDITIONAL_BUILD_REQUIRES_ARCHFUL
    return ADDITIONAL_BUILD_REQUIRES_NOARCH


def python3_pkgversion_or_3(config: ConfigFile) -> str:
    return "%{python3_pkgversion}" if config.get_string("python_alt_version") else "3"


def get_license_string(config: ConfigFile) -> tuple[str, str]:
    none_notice = "# No license information obtained, it's up to the packager to fill it in"
    detected_notice = ("# Check if the automatically generated License and its "
        "spelling is correct for Fedora\n"
        "# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/")
    if (license := config.get_string("license")):
        return (license, detected_notice)
    return ("...", none_notice)


def convert_version_to_rpm_scheme(version: str) -> str:
    """If version follows PEP 440, return its value converted to RPM scheme.

    PEP 440: https://www.python.org/dev/peps/pep-0440/
    If the package uses a different versioning scheme (i.e. LegacyVersion),
    the returned value will be the same as the input one.
    Such value may or may not work with RPM.
    Automatic conversion of the LegacyVersions is not feasible, as stated in:
    https://lists.fedoraproject.org/archives/list/python-devel@lists.fedoraproject.org/message/5MGEHMTKOKR5U7ACIMUDRBKMSP6Y5NQD/
    """
    return str(RpmVersion(version))


def same_as_rpm(pypi_version: str) -> bool:
    return pypi_version == convert_version_to_rpm_scheme(pypi_version)


def archive_basename(config: ConfigFile, pypi_version: str) -> str:
    """Return the archive basename.

    The filename has been standardized in PEP 625, but many projects out there
    use the legacy, pre-standard, custom naming. Extract the basename the same
    way it's spelled in the archive name.

    Example: "My-package_Archive-1.0.4-12.tar.gz" -> "My-package_Archive"
    """
    filename = config.get_string("archive_name")

    # First, strip the suffix
    for suffix in (".tar.gz", ".zip"):
        filename = filename.removesuffix(suffix)
    # Second, split paths and keep only the last part of it
    filename = filename.split("/")[-1]
    # Last, get rid of the version string and the delimiter "-"
    return filename.replace("-" + pypi_version, "")


def is_zip(config: ConfigFile) -> bool:
    """
    The archive format standardized in PEP 625 is tar.gz,
    however some projects still use the legacy zip.
    If so, it has to be explicitly declared as an argument of %{pypi_source}.
    """
    return config.get_string("archive_name").endswith(".zip")


def source(config: ConfigFile) -> str:
    """Return valid pypi_source RPM macro.

    %pypi_source takes three optional arguments:
    <name>, <version> and <file_extension>.
    <name> is always passed: "%{pypi_source foo}".
    <version> is passed if PyPI's and RPM's version strings differ:
    "%{pypi_source foo 1.2-3}". If they're the same and the file extension
    is not zip, version is not passed.
    If archive is a zip file, %{pypi_source} must take all three args:
    "%{pypi_source foo %{version} zip}", "{pypi_source foo 1.2-3 zip}"
    """
    detected_source = config.get_string("source")
    if detected_source == "PyPI":
        pypi_version = config.get_string("pypi_version")
        version_str = pypi_version_or_macro(pypi_version)
        basename = archive_basename(config, pypi_version)
        source_macro_args = basename

        if is_zip(config):
            source_macro_args += f" {version_str} zip"
        else:
            if version_str == pypi_version:
                source_macro_args += f" {version_str}"
        return "%{pypi_source " + source_macro_args + "}"
    elif detected_source == "local":
        return config.get_string("archive_name")
    else:
        raise NotImplementedError("pyp2spec can deal with `PyPI` and `local` sources")


def pypi_version_or_macro(pypi_version: str) -> str:
    if same_as_rpm(pypi_version):
        return "%{version}"
    return pypi_version


def fill_in_template(config: ConfigFile, declarative_buildsystem: bool) -> str:
    """Return template rendered with data from config file."""

    with (files("pyp2spec") / TEMPLATE_FILENAME).open("r", encoding="utf-8") as f:
        spec_template = Template(f.read())

    license, license_notice = get_license_string(config)

    pypi_version = config.get_string("pypi_version")

    result = spec_template.render(
        additional_build_requires=list_additional_build_requires(config),
        archful=config.get_bool("archful"),
        archive_name=archive_basename(config, pypi_version),
        automode=config.get_bool("automode"),
        compat=config.get_string("compat"),
        compat_name=create_compat_name(config.get_string("pypi_name"), config.get_string("compat")),
        declarative_buildsystem=declarative_buildsystem,
        extras=",".join(config.get_list("extras")),
        license=license,
        license_notice=license_notice,
        mandate_license=config.get_bool("license_files_present"),
        name=config.get_string("pypi_name"),
        python_compat_name=create_compat_name(config.get_string("python_name"), config.get_string("compat")),
        pypi_version=pypi_version_or_macro(pypi_version),
        python_alt_version=config.get_string("python_alt_version"),
        source=source(config),
        summary=config.get_string("summary"),
        test_top_level=config.get_bool("test_top_level"),
        python3_pkgversion=python3_pkgversion_or_3(config),
        url=config.get_string("url"),
        version=convert_version_to_rpm_scheme(pypi_version),
    )

    return result


def save_spec_file(config: ConfigFile, options: dict[str, Any]) -> str:
    """Save the spec file in the current directory if custom output is not set.
    Return the saved file name."""

    declarative_buildsystem = options.get("declarative_buildsystem", False)
    result = fill_in_template(config, declarative_buildsystem)
    output = options.get("spec_output")
    if output is None:
        output = create_compat_name(config.get_string("python_name"), config.get_string("compat"))
        output += ".spec"
    with open(output, "w", encoding="utf-8") as spec_file:
        spec_file.write(result)
    yay(f"Spec file was saved successfully to '{output}'")
    return output


def create_spec_file(config_file: str, options: dict[str, Any]) -> str | None:
    """Create and save the generate spec file."""
    config = ConfigFile(load_config_file(config_file))
    return save_spec_file(config, options)


@click.command()
@click.argument("config")
@click.option(
    "--spec-output",
    "-o",
    help="Provide custom output for spec file",
)
@click.option(
    "--declarative-buildsystem", is_flag=True, default=False,
    help="Create a spec file with pyproject declarative buildsystem (experimental)",
)
def main(config: str, **options: dict[str, Any]) -> None:
    try:
        create_spec_file(config, options)
    except (Pyp2specError, NotImplementedError) as exc:
        warn(f"Fatal exception occurred: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
