import pytest
from pathlib import Path

from pyp2spec.local_loaders import _resolve_and_check_if_dir_exists, _look_up_file_in_dir
from pyp2spec.local_loaders import DirectoryMissingError, FileMissingError
from pyp2spec.local_loaders import load_core_metadata_from_file, load_dist_data_from_dir


def test_resolve_and_check_if_dir_exists_valid_path(tmp_path):
    valid_path = tmp_path
    assert _resolve_and_check_if_dir_exists(valid_path) == Path(valid_path).resolve()
    assert _resolve_and_check_if_dir_exists(valid_path).is_dir()


def test_resolve_and_check_if_dir_exists_cwd():
    valid_path = "."
    assert _resolve_and_check_if_dir_exists(valid_path) == Path.cwd()
    assert _resolve_and_check_if_dir_exists(valid_path).is_dir()


def test_resolve_and_check_if_dir_exists_non_existing_path():
    with pytest.raises(DirectoryMissingError, match="The specified path doesn't exist"):
        _resolve_and_check_if_dir_exists("non/existing/path")


def test_resolve_and_check_if_dir_exists_file_path(tmp_path):
    file_path = tmp_path / "testfile.txt"
    file_path.touch()
    with pytest.raises(DirectoryMissingError, match="The specified path must be a directory"):
        _resolve_and_check_if_dir_exists(file_path)


def test_look_up_file_in_dir_single_match(tmp_path):
    (tmp_path / "package-1.whl").touch()
    (tmp_path / "package-1.tar.gz").touch()
    result = _look_up_file_in_dir("package", tmp_path, "whl")
    assert result == tmp_path / "package-1.whl"


def test_look_up_file_in_dir_no_match(tmp_path):
    (tmp_path / "package-1.whl").touch()
    (tmp_path / "package-2.whl").touch()
    with pytest.raises(FileMissingError, match="Either none or too many files"):
        _look_up_file_in_dir("package", tmp_path, "tar.gz")


def test_look_up_file_in_dir_multiple_matches(tmp_path):
    (tmp_path / "package-1.whl").touch()
    (tmp_path / "package-2.whl").touch()
    with pytest.raises(FileMissingError, match="Either none or too many files"):
        _look_up_file_in_dir("package", tmp_path, "whl")


def test_load_core_metadata_from_file():
    metadata = load_core_metadata_from_file("tests/local/local_test-0.12.2-py3-none-any.whl")
    assert metadata["version"] == "0.12.2"


def test_load_dist_data_from_dir():
    test_dir = "tests/local"
    sdist, wheel, data = load_dist_data_from_dir("local_test", test_dir)
    # Keep just the latest parts of the full file paths
    sdist = sdist.split("/")[-3:]
    assert sdist == ["tests", "local", "local_test-0.12.2.tar.gz"]
    wheel = wheel.split("/")[-1]
    assert wheel == "local_test-0.12.2-py3-none-any.whl"
    assert data["version"] == "0.12.2"
