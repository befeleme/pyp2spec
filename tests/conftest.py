import json

import betamax  # type: ignore
import pytest


config = betamax.Betamax.configure()
config.cassette_library_dir = "tests/fixtures/cassettes"
# only replay recorded cassettes -
# error if an actual HTTP request would be necessary
# this is to prevent packaging issues in the offline environment (like rpm build)
# change to 'once' to enable recording new cassettes when writing new tests
config.default_cassette_options["record_mode"] = "none"


@pytest.fixture(scope="session")
def fake_fedora_licenses():
    with open("tests/fedora_license_data.json", "r", encoding="utf-8") as f:
        return json.load(f)
