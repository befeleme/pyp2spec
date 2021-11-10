import betamax
import click
import pytest
import tomli

from pyp2spec import pyp2conf


with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'tests/fixtures/cassettes'


@pytest.fixture
def changelog():
    return ("Wed Nov 03 2021", "Packager", "packager@maint.com")


@pytest.mark.parametrize("package, version",
    [
        ("aionotion", "2.0.3"),
        ("aioflo", "0.4.2"),
        ("click", "7.1.2"),
        ("jupyter-packaging", "0.10.4"),
        ("markdown-it-py", "1.1.0"),
    ]
)
def test_automatically_generated_config_is_valid(betamax_parametrized_session, changelog, package, version):
    """Run the config rendering in fully automated mode and compare the results"""
    config = pyp2conf.create_config_contents(
        package=package,
        version=version,
        date=changelog[0],
        name=changelog[1],
        email=changelog[2],
        session=betamax_parametrized_session,
    )

    with open(f"tests/test_configs/default_python-{package}.conf", "rb") as config_file:
        loaded_contents = tomli.load(config_file)

    assert config == loaded_contents


def test_config_with_customization_is_valid(betamax_session):
    """Get the upstream metadata and modify some fields to get the custom config file.
    """
    package = "aionotion"
    config = pyp2conf.create_config_contents(
        package=package,
        description="A asyncio-friendly library for Notion Home Monitoring devices.\n",
        release="4",
        message="Rebuilt for Python 3.10",
        email="package@manager.com",
        name="Package Manager",
        version="2.0.3",
        summary="Python library for Notion Home Monitoring",
        date="Fri Jun 04 2021",
        session=betamax_session,
    )

    with open(f"tests/test_configs/customized_{package}.conf", "rb") as config_file:
        loaded_contents = tomli.load(config_file)

    assert config == loaded_contents


def test_package_without_license_is_not_processed(betamax_session, changelog):
    with pytest.raises(click.exceptions.UsageError):
        pyp2conf.create_config_contents(
            package="tomli",
            version="1.1.0",
            date=changelog[0],
            name=changelog[1],
            email=changelog[2],
            session=betamax_session,
        )
