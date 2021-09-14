from pyp2conf import create_config
from conf2spec import create_spec_file
import click


@click.command()
@click.argument("package")
@click.option(
    "--conf-output",
    "-o",
    help="Provide custom output for configuration file",
)
@click.option(
    "--description",
    "-d",
    help="Provide description for the package",
)
@click.option(
    "--release",
    "-r",
    help="Provide custom release (corresponds with Release in spec file)",
)
@click.option(
    "--message",
    "-m",
    help="Provide changelog message for the package",
)
@click.option(
    "--email",
    "-e",
    help="Provide e-mail for changelog",
)
@click.option(
    "--packagername",
    "-n",
    help="Provide packager name for changelog",
)
@click.option(
    "--version",
    "-v",
    help="Provide package version to query PyPI for",
)
@click.option(
    "--summary",
    "-s",
    help="Provide custom package summary",
)
@click.option(
    "--date",
    help="Provide custom date for changelog",
)
@click.option(
    "--spec-output",
    "-s",
    help="Provide custom output where spec file will be saved",
)
def main(
    package,
    conf_output,
    description,
    release,
    message,
    email,
    packagername,
    version,
    summary,
    date,
    spec_output,
):
    config_file = create_config(
        package,
        conf_output,
        description,
        release,
        message,
        email,
        packagername,
        version,
        summary,
        date,
    )
    create_spec_file(config_file, spec_output)


if __name__ == "__main__":
    main()
