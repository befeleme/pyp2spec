import sys

from importlib.resources import files

import click

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from jinja2 import Template

from pyp2spec.rpmversion import RpmVersion
from pyp2spec.utils import Pyp2specError


TEMPLATE_FILENAME = "template.spec"
ADDITIONAL_BUILD_REQUIRES_ARCHFUL = ["gcc"]
ADDITIONAL_BUILD_REQUIRES_NOARCH = []


class ConfigError(Pyp2specError):
    """Raised when a config value has got a wrong type"""


class ConfigFile:
    """Validate configuration data."""

    def __init__(self, contents):
        self.contents = contents

    def get_string(self, key):
        """Return a value for given key. Validate the value is a string.
        Raise ConfigError otherwise."""

        return self._get_value(key, str)

    def get_list(self, key):
        """Return a value for given key. Validate the value is a list.
        Raise ConfigError otherwise."""

        return self._get_value(key, list)

    def get_bool(self, key):
        """Return a value for given key. Validate the value is a boolean.
        Raise ConfigError otherwise."""

        return self._get_value(key, bool)

    def _get_value(self, key, val_type):
        val = self.contents.get(key, val_type())
        if not isinstance(val, val_type):
            raise ConfigError(f"{val} must be a {val_type}")
        return val


def load_config_file(filename):
    """Return loaded TOML configuration file contents."""

    with open(filename, "rb") as configuration_file:
        return tomllib.load(configuration_file)


def list_additional_build_requires(config):
    """Returns a list of additionally defined BuildRequires,

    The list differs for packages that are or aren't archful.
    """
    if config.get_bool("archful"):
        return ADDITIONAL_BUILD_REQUIRES_ARCHFUL
    return ADDITIONAL_BUILD_REQUIRES_NOARCH


def python3_pkgversion_or_3(config):
    return "%{python3_pkgversion}" if config.get_string("python_alt_version") else "3"


def get_license_string(config):
    none_notice = "# No license information obtained, it's up to the packager to fill it in"
    detected_notice = ("# Check if the automatically generated License and its "
        "spelling is correct for Fedora\n"
        "# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/")
    if (license := config.get_string("license")):
        return (license, detected_notice)
    return ("...", none_notice)


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


def same_as_rpm(pypi_version):
    return pypi_version == convert_version_to_rpm_scheme(pypi_version)


def archive_name(config):
    """
    PEP 625 specifies the sdist name to be normalized according to the wheel spec:
    https://packaging.python.org/en/latest/specifications/binary-distribution-format/#escaping-and-unicode
    """
    return config.get_string("pypi_name").replace("-", "_")


def source(config, pypi_version):
    """Return valid pypi_source RPM macro.

    %pypi_source takes three optional arguments:
    <name>, <version> and <file_extension>.
    <name> is always passed: "%{pypi_source foo}".
    <version> is passed if PyPI's and RPM's version strings differ:
    "%{pypi_source foo 1.2-3}". If they're the same, version is not passed.
    Since PEP 625, the required file extension for sdists is `tar.gz`,
    which is the default <file_extension> accepted by the macro, hence
    we don't have to define it here.
    """
    if config.get_string("source") == "PyPI":
        source_macro_args = archive_name(config)

        if not same_as_rpm(pypi_version):
            source_macro_args +=  f" {pypi_version}"
        return "%{pypi_source " + source_macro_args + "}"


def pypi_version_or_macro(pypi_version):
    if same_as_rpm(pypi_version):
        return "%{version}"
    return pypi_version


def fill_in_template(config):
    """Return template rendered with data from config file."""

    with (files("pyp2spec") / TEMPLATE_FILENAME).open("r", encoding="utf-8") as f:
        spec_template = Template(f.read())

    license, license_notice = get_license_string(config)

    pypi_version = config.get_string("pypi_version")

    result = spec_template.render(
        additional_build_requires=list_additional_build_requires(config),
        archful=config.get_bool("archful"),
        archive_name=archive_name(config),
        automode=config.get_bool("automode"),
        extras=",".join(config.get_list("extras")),
        license=license,
        license_notice=license_notice,
        mandate_license=config.get_bool("license_files_present"),
        name=config.get_string("pypi_name"),
        python_name=config.get_string("python_name"),
        pypi_version=pypi_version_or_macro(pypi_version),
        python_alt_version=config.get_string("python_alt_version"),
        source=source(config, pypi_version),
        summary=config.get_string("summary"),
        test_top_level=config.get_bool("test_top_level"),
        python3_pkgversion=python3_pkgversion_or_3(config),
        url=config.get_string("url"),
        version=convert_version_to_rpm_scheme(pypi_version),
    )

    return result


def save_spec_file(config, output):
    """Save the spec file in the current directory if custom output is not set.
    Return the saved file name."""

    result = fill_in_template(config)
    if output is None:
        output = config.get_string("python_name") + ".spec"
    with open(output, "w", encoding="utf-8") as spec_file:
        spec_file.write(result)
    click.secho(f"Spec file was saved successfully to '{output}'")
    return output


def create_spec_file(config_file, spec_output=None):
    """Create and save the generate spec file."""
    config = ConfigFile(load_config_file(config_file))
    return save_spec_file(config, spec_output)


@click.command()
@click.argument("config")
@click.option(
    "--spec-output",
    "-o",
    help="Provide custom output for spec file",
)
def main(config, spec_output):
    try:
        create_spec_file(config, spec_output)
    except (Pyp2specError, NotImplementedError) as exc:
        click.secho(f"Fatal exception occurred: {exc}", fg="red")
        sys.exit(1)

if __name__ == "__main__":
    main()
