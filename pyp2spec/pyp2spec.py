import sys

import click

from pyp2spec.pyp2conf import create_config, pypconf_args
from pyp2spec.conf2spec import create_spec_file
from pyp2spec.utils import Pyp2specError
from pyp2spec.utils import warn


@click.command()
@pypconf_args
@click.option(
    "--spec-output", "-o",
    help="Provide custom output where spec file will be saved",
)
@click.option(
    "--declarative-buildsystem", is_flag=True, default=False,
    help="Create a spec file with pyproject declarative buildsystem (experimental)",
)
def main(**options):  # noqa
    try:
        if options["automode"] and options["declarative_buildsystem"]:
            raise Pyp2specError("Declarative buildsystem doesn't work with automode")
        config_file = create_config(options)
        create_spec_file(config_file, options)
    except (Pyp2specError, NotImplementedError) as exc:
        warn(f"Fatal exception occurred: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
