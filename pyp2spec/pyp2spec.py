from pyp2spec.pyp2conf import create_config
from pyp2spec.conf2spec import create_spec_file
import click


@click.command()
@click.argument("package")
@click.option(
    "--config-output", "-c",
    help="Provide custom output for configuration file",
)
@click.option(
    "--description", "-d",
    help="Provide description for the package",
)
@click.option(
    "--release", "-r",
    help="Provide Fedora release, default: 1",
)
@click.option(
    "--message", "-m",
    help="Provide custom changelog message for the package",
)
@click.option(
    "--email", "-e",
    help="Provide e-mail for changelog, default: output of `rpmdev-packager`",
)
@click.option(
    "--packager", "-p",
    help="Provide packager name for changelog, default: output of `rpmdev-packager`",
)
@click.option(
    "--version", "-v",
    help="Provide package version to query PyPI for, default: latest",
)
@click.option(
    "--summary", "-s",
    help="Provide custom package summary",
)
@click.option(
    "--license", "-l",
    help="Provide license name",
)
@click.option(
    "--spec-output", "-s",
    help="Provide custom output where spec file will be saved",
)
@click.option(
    "--fedora-compliant", is_flag=True,
    help="Check whether license is compliant with Fedora",
)
@click.option(
    "--top-level", "-t", is_flag=True,
    help="Test only top-level modules in %check",
)
def main(**options):
    click.secho("Generating configuration file", fg="cyan")
    config_file = create_config(options)
    click.secho("Generating spec file", fg="cyan")
    create_spec_file(config_file, options["spec_output"])
    click.secho("Done", fg="green")


if __name__ == "__main__":
    main()
