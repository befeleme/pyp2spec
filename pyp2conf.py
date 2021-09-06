import click
import tomli_w


def write_config(contents, output=None):
    """Write config file to a given destination.
    If none is provided, save it to current directory with package name as file name.
    """
    if output:
        dest = output
    else:
        # TODO: name must reflect the package
        dest = "./pyp2spec_test.conf"
    with open(dest, "wb") as f:
        tomli_w.dump(contents, f)
    return dest


@click.command()
@click.option(
    "--output", "-o",
    help="Provide custom output for configuration file",
)
def main(output):
    contents = {"test": [1, 2, 4]}
    write_config(contents, output)


if __name__ == "__main__":
    main()