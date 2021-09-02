import tomli


VALID_FIELD_TYPES = {
    "archive_name": str,
    "binary_files": list,
    "changelog_head": str,
    "changelog_msg": str,
    "description": str,
    "doc_files": list,
    "extra_build_requires": list,
    "extra_test_env": list,
    "license_files": list,
    "license": str,
    "manual_build_requires": list,
    "module_name": str,
    "pypi_name": str,
    "python_name": str,
    "release": str,
    "source": str,
    "summary": str,
    "test_method": str,
    "unwanted_tests": list,
    "url": str,
    "version": str,
}

MANDATORY_FIELDS = [
    "archive_name",
    "changelog_head",
    "changelog_msg",
    "description",
    "doc_files",
    "license_files",
    "license",
    "module_name",
    "pypi_name",
    "python_name",
    "release",
    "source",
    "summary",
    "url",
    "version",
]

class ConfigFile:
    """Load and validate configuration file."""

    def __init__(self, filename):
        self.filename = filename
        self.contents = self.load_configuration

    @property
    def load_configuration(self):
        """Load TOML configuration file.
        Return validated contents."""

        with open(self.filename, "rb") as configuration_file:
            loaded_contents = tomli.load(configuration_file)

        return self.validate_contents(loaded_contents)

    def validate_contents(self, contents):
        """Validate configuration file.
        Checks if all mandatory fields are present.
        Checks all filled in field types are correct."""

        for field in MANDATORY_FIELDS:
            if field not in contents:
                raise ValueError(f"Mandatory field '{field}' is missing.")

        for k, v in contents.items():
            if not isinstance(v, VALID_FIELD_TYPES[k]):
                raise TypeError(f"{k} must be instance of {VALID_FIELD_TYPES[k]}")

        return contents

    def get_value(self, key):
        return self.contents.get(key, "")
