import sys

import click

from pyp2spec.pyp2conf import create_config, pypconf_args
from pyp2spec.conf2spec import create_spec_file
from pyp2spec.utils import Pyp2specError


@click.command()
@pypconf_args
@click.option(
    "--spec-output", "-o",
    help="Provide custom output where spec file will be saved",
)
@click.option(
    "--python-version",
    "-p",
    help="Specify specific python version to build for, e.g 3.11",
)
def main(**options):
    click.secho("Generating configuration file", fg="cyan")
    try:
        config_file = create_config(options)
        click.secho("Generating spec file", fg="cyan")
        create_spec_file(config_file, options["spec_output"],options["python_version"])
    except (Pyp2specError, NotImplementedError) as exc:
        click.secho(f"Fatal exception occurred: {exc}", fg="red")
        sys.exit(1)
    click.secho("Done", fg="green")


if __name__ == "__main__":
    main()
