import betamax
import tomli

import pyp2conf


with betamax.Betamax.configure() as config:
    config.cassette_library_dir = 'tests/fixtures/cassettes'


def test_config_is_valid(betamax_session):
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

    with open(f"tests/test_configs/pyp2spec_{package}.conf", "rb") as config_file:
        loaded_contents = tomli.load(config_file)

    assert config == loaded_contents
