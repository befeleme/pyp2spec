from packaging.metadata import parse_email, RawMetadata
import tarfile
import tempfile
import tomllib
import os.path
from pyp2spec.utils import Pyp2specError

class PyProjectNotFound(Pyp2specError):
    """Raised when there's no pyproject.toml file in the extracted package"""

def load_core_metadata_from_tar(package: str) -> RawMetadata:
    with tempfile.TemporaryDirectory(delete=False) as tmpdirname:
        print(f"Extracting {package} in {tmpdirname}")
        tar = tarfile.open(name=package)
        tar.extractall(path=tmpdirname, filter="data")
        # Check if pyproject.toml exists.
        pyproject_path = f"{tmpdirname}/pyproject.toml"
        if not os.path.exists(pyproject_path):
            raise PyProjectNotFound(f"No pyproject.toml file found in {package}")
        # Parse pyproject.toml to get metadata.
        print(f"Attempting to load {pyproject_path}")
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
            return pyproject['project']