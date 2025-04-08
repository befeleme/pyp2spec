from pathlib import Path
from zipfile import ZipFile

from packaging.metadata import RawMetadata

from pyp2spec.utils import Pyp2specError, CoreMetadataNotFoundError
from pyp2spec.utils import parse_core_metadata, normalize_as_wheel_name


class DirectoryMissingError(Pyp2specError):
    """Raised when a directory cannot be determined"""


class FileMissingError(Pyp2specError):
    """Raised when a file cannot be determined"""


def _resolve_and_check_if_dir_exists(path: str) -> Path:
    resolved_path = Path(path).resolve()
    if not resolved_path.exists():
        raise DirectoryMissingError("The specified path doesn't exist")
    if not resolved_path.is_dir():
        raise DirectoryMissingError("The specified path must be a directory")
    return resolved_path


def _look_up_file_in_dir(package: str, path: Path, suffix: str) -> Path:
    pattern = f"{package}-*.{suffix}"
    filelist = sorted(path.glob(pattern))
    if len(filelist) != 1:
        raise FileMissingError(f"Either none or too many files with pattern `{pattern}` were found in `{path}`")
    return filelist[0]


def load_core_metadata_from_file(wheel_name: str) -> RawMetadata:
    """
    Load core metadata from a wheel file.
    Read the METADATA file from a wheel archive and parse its content.
    Return a `RawMetadata` object, containing the parsed metadata.
    Raise a `CoreMetadataNotFoundError` if the METADATA file cannot be found in the wheel.
    """
    with ZipFile(wheel_name, "r") as wheel_file:
        for entry in wheel_file.namelist():
            if entry.endswith("dist-info/METADATA"):
                with wheel_file.open(entry) as metadata_file:
                    metadata = metadata_file.read()
                    break
        else:
            raise CoreMetadataNotFoundError("METADATA file was not found in the wheel")
    return parse_core_metadata(metadata)


def load_dist_data_from_dir(package: str, path: str) -> tuple[str, str, RawMetadata]:
    """
    Load distribution data from a given directory.
    Return a tuple of sdist name, wheel name, and metadata.
    If there's no sdist on the given path, a "not found" string is returned.
    Raise a FileMissingError if the wheel file cannot be found in the directory.
    """
    source_path = _resolve_and_check_if_dir_exists(path)
    pkgname = normalize_as_wheel_name(package)
    # sdist name is only needed as a source in specfile
    # if not present, we can still generate a good-enough file
    try:
        sdist_name = str(_look_up_file_in_dir(pkgname, source_path, "tar.gz"))
    except FileMissingError:
        sdist_name = "..."
    wheel_name = str(_look_up_file_in_dir(pkgname, source_path, "whl"))
    metadata = load_core_metadata_from_file(wheel_name)
    return sdist_name, wheel_name, metadata
