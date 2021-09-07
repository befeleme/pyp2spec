# import config
import pyp2conf

import tomli


def test_config_is_valid():
    package = "aionotion"
    resp = pyp2conf.get_pypi_metadata(package)
    config = pyp2conf.create_config_contents(
        resp,
        description="A asyncio-friendly library for Notion Home Monitoring devices.\n",
        release="4",
        message="Rebuilt for Python 3.10",
        email="package@manager.com",
        name="Package Manager",
        version="2.0.3",
        summary="Python library for Notion Home Monitoring",
        date="Fri Jun 04 2021"
    )

    with open(f"tests/test_configs/pyp2spec_{package}.conf", "rb") as config_file:
        loaded_contents = tomli.load(config_file)

    assert config == loaded_contents
    # assert config.ConfigFile.validate_contents(contents)
