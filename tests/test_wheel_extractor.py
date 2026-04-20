"""Test the wheel_extractor module functionality.

These tests use mocking for most cases and only a few tests require actual network access.
Run tests with: pytest -v
Skip network tests with: pytest -v -m 'not network'
"""

import os
import tempfile
import pytest
from zipfile import ZipFile

from pyp2spec.wheel_extractor import (
    download_and_extract_files,
    _find_wheel_url,
    _extract_modules_from_wheel,
    _extract_scripts_from_wheel,
    WheelNotFoundError,
)


class TestFindWheelUrl:
    """Test the _find_wheel_url function."""

    def test_finds_pure_python_wheel(self):
        """Test that pure Python wheels are preferred."""
        pypi_data = {
            "urls": [
                {
                    "packagetype": "sdist",
                    "filename": "click-8.1.3.tar.gz",
                    "url": "https://example.com/click-8.1.3.tar.gz",
                },
                {
                    "packagetype": "bdist_wheel",
                    "filename": "click-8.1.3-py3-none-any.whl",
                    "url": "https://example.com/click-8.1.3-py3-none-any.whl",
                },
            ]
        }
        url = _find_wheel_url(pypi_data)
        assert url == "https://example.com/click-8.1.3-py3-none-any.whl"

    def test_prefers_pure_python_over_platform_specific(self):
        """Test that pure Python wheels are preferred over platform-specific ones."""
        pypi_data = {
            "urls": [
                {
                    "packagetype": "bdist_wheel",
                    "filename": "numpy-1.24.0-cp310-cp310-linux_x86_64.whl",
                    "url": "https://example.com/numpy-platform.whl",
                },
                {
                    "packagetype": "bdist_wheel",
                    "filename": "numpy-1.24.0-py3-none-any.whl",
                    "url": "https://example.com/numpy-pure.whl",
                },
            ]
        }
        url = _find_wheel_url(pypi_data)
        assert url == "https://example.com/numpy-pure.whl"

    def test_falls_back_to_platform_specific_wheel(self):
        """Test that platform-specific wheels are used if no pure Python wheel exists."""
        pypi_data = {
            "urls": [
                {
                    "packagetype": "sdist",
                    "filename": "numpy-1.24.0.tar.gz",
                    "url": "https://example.com/numpy.tar.gz",
                },
                {
                    "packagetype": "bdist_wheel",
                    "filename": "numpy-1.24.0-cp310-cp310-linux_x86_64.whl",
                    "url": "https://example.com/numpy-platform.whl",
                },
            ]
        }
        url = _find_wheel_url(pypi_data)
        assert url == "https://example.com/numpy-platform.whl"

    def test_returns_none_if_no_wheel(self):
        """Test that None is returned if no wheel is available."""
        pypi_data = {
            "urls": [
                {
                    "packagetype": "sdist",
                    "filename": "package-1.0.0.tar.gz",
                    "url": "https://example.com/package.tar.gz",
                },
            ]
        }
        url = _find_wheel_url(pypi_data)
        assert url is None


class TestExtractModulesFromWheel:
    """Test _extract_modules_from_wheel with mock wheel files."""

    def _create_test_wheel(self, top_level_content, package_name="test_package"):
        """Helper to create a test wheel file with given top_level.txt content."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.whl', delete=False)
        tmp_file.close()

        with ZipFile(tmp_file.name, 'w') as wheel:
            # Add top_level.txt file
            wheel.writestr(
                f'{package_name}-1.0.0.dist-info/top_level.txt',
                top_level_content
            )

        return tmp_file.name

    def test_extracts_single_module(self):
        """Test extracting a single module from top_level.txt."""
        wheel_path = self._create_test_wheel("click\n")
        try:
            modules = _extract_modules_from_wheel(wheel_path)
            assert modules == ["click"]
        finally:
            os.unlink(wheel_path)

    def test_extracts_multiple_modules(self):
        """Test extracting multiple modules from top_level.txt."""
        wheel_path = self._create_test_wheel("requests\nurllib3\ncharset_normalizer\n")
        try:
            modules = _extract_modules_from_wheel(wheel_path)
            assert set(modules) == {"requests", "urllib3", "charset_normalizer"}
        finally:
            os.unlink(wheel_path)

    def test_handles_empty_lines(self):
        """Test that empty lines in top_level.txt are ignored."""
        wheel_path = self._create_test_wheel("click\n\n\nidna\n")
        try:
            modules = _extract_modules_from_wheel(wheel_path)
            assert set(modules) == {"click", "idna"}
        finally:
            os.unlink(wheel_path)

    def test_fallback_to_record_file(self):
        """Test fallback to RECORD file when top_level.txt is missing."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.whl', delete=False)
        tmp_file.close()

        with ZipFile(tmp_file.name, 'w') as wheel:
            # No top_level.txt, only RECORD
            wheel.writestr(
                'test_package-1.0.0.dist-info/RECORD',
                'click/__init__.py,sha256=xxx,123\n'
                'click/core.py,sha256=yyy,456\n'
                'test_package-1.0.0.dist-info/METADATA,sha256=zzz,789\n'
            )

        try:
            modules = _extract_modules_from_wheel(tmp_file.name)
            assert "click" in modules
        finally:
            os.unlink(tmp_file.name)


class TestExtractScriptsFromWheel:
    """Test _extract_scripts_from_wheel with mock wheel files."""

    def _create_test_wheel_with_scripts(self, entry_points_content, package_name="test_package"):
        """Helper to create a test wheel file with given entry_points.txt content."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.whl', delete=False)
        tmp_file.close()

        with ZipFile(tmp_file.name, 'w') as wheel:
            # Add entry_points.txt file
            wheel.writestr(
                f'{package_name}-1.0.0.dist-info/entry_points.txt',
                entry_points_content
            )

        return tmp_file.name

    def test_extracts_single_script(self):
        """Test extracting a single console script."""
        entry_points = "[console_scripts]\npyp2spec = pyp2spec.cli:main\n"
        wheel_path = self._create_test_wheel_with_scripts(entry_points)
        try:
            scripts = _extract_scripts_from_wheel(wheel_path)
            assert scripts == ["pyp2spec"]
        finally:
            os.unlink(wheel_path)

    def test_extracts_multiple_scripts(self):
        """Test extracting multiple console scripts."""
        entry_points = "[console_scripts]\nfoo = foo.cli:main\nbar = bar.cli:run\nbaz = baz:entry\n"
        wheel_path = self._create_test_wheel_with_scripts(entry_points)
        try:
            scripts = _extract_scripts_from_wheel(wheel_path)
            assert set(scripts) == {"foo", "bar", "baz"}
        finally:
            os.unlink(wheel_path)

    def test_no_scripts(self):
        """Test wheel with no console scripts."""
        entry_points = "[gui_scripts]\napp = app.gui:main\n"
        wheel_path = self._create_test_wheel_with_scripts(entry_points)
        try:
            scripts = _extract_scripts_from_wheel(wheel_path)
            assert scripts == []
        finally:
            os.unlink(wheel_path)

    def test_no_entry_points(self):
        """Test wheel with no entry_points.txt file."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.whl', delete=False)
        tmp_file.close()

        with ZipFile(tmp_file.name, 'w') as wheel:
            # Create a minimal wheel without entry_points.txt
            wheel.writestr('test_package-1.0.0.dist-info/METADATA', 'Name: test\n')

        try:
            scripts = _extract_scripts_from_wheel(tmp_file.name)
            assert scripts == []
        finally:
            os.unlink(tmp_file.name)


class TestDownloadAndExtractFiles:
    """Integration tests for download_and_extract_files.

    These tests use betamax cassettes for recorded HTTP interactions.
    """

    def test_download_click(self, betamax_session):
        """Test download of click package and extraction of modules and scripts."""
        pypi_data = {
            "info": {
                "name": "click",
                "version": "8.1.3",
            },
            "urls": [
                {
                    "packagetype": "bdist_wheel",
                    "filename": "click-8.1.3-py3-none-any.whl",
                    "url": "https://files.pythonhosted.org/packages/c2/f1/df59e28c642d583f7dacffb1e0965d0e00b218e0186d7858ac5233dce840/click-8.1.3-py3-none-any.whl",
                }
            ],
        }

        result = download_and_extract_files(pypi_data, session=betamax_session)
        assert result["modules"] == ["click"]
        assert "scripts" in result
