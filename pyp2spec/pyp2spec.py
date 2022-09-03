import click

from pyp2spec.pyp2conf import create_config, pypconf_args
from pyp2spec.conf2spec import create_spec_file


@click.command()
@pypconf_args
@click.option(
    "--spec-output", "-o",
    help="Provide custom output where spec file will be saved",
)
def main(**options):
    click.secho("Generating configuration file", fg="cyan")
    config_file = create_config(options)
    click.secho("Generating spec file", fg="cyan")
    create_spec_file(config_file, options["spec_output"])
    click.secho("Done", fg="green")


if __name__ == "__main__":
    main()
