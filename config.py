import tomli


class ConfigFile:
    """Load configuration file and return its validated values."""

    def __init__(self, filename):
        self.filename = filename
        self.contents = self.load_configuration

    @property
    def load_configuration(self):
        """Return loaded TOML configuration file contents."""

        with open(self.filename, "rb") as configuration_file:
            loaded_contents = tomli.load(configuration_file)

        return loaded_contents

    def get_string(self, key):
        """Return a value for given key. Validate the value is a string.
        Raise TypeError otherwise."""

        return self._get_value(key, str)

    def get_list(self, key):
        """Return a value for given key. Validate the value is a list.
        Raise TypeError otherwise."""

        return self._get_value(key, list)

    def _get_value(self, key, val_type):
        val = self.contents.get(key, val_type())
        if not isinstance(val, val_type):
            raise TypeError(f"{val} must be a {val_type}")
        return val
