"""
Module for downloading and extracting file information from Python wheels.
"""
from __future__ import annotations

import configparser
import tempfile
from pathlib import Path
from zipfile import ZipFile
from typing import Any

from requests import Session

from pyp2spec.utils import Pyp2specError, inform, sanitize_input


class WheelNotFoundError(Pyp2specError):
    """Raised when there's no wheel file available for the package"""


def _find_wheel_url(pypi_pkg_data: dict[Any, Any]) -> str | None:
    """Find the URL of a wheel file from PyPI package data.

    Prefer pure Python wheels (py3-none-any) over platform-specific ones.
    """
    pure_python_wheels = []
    other_wheels = []

    for entry in pypi_pkg_data["urls"]:
        if entry["packagetype"] == "bdist_wheel":
            filename = entry["filename"]
            if "py3-none-any" in filename:
                pure_python_wheels.append(entry["url"])
            else:
                other_wheels.append(entry["url"])

    # Prefer pure Python wheels
    if pure_python_wheels:
        return pure_python_wheels[0]
    elif other_wheels:
        return other_wheels[0]
    else:
        return None


def _extract_modules_from_wheel(wheel_path: str) -> list[str]:
    """Extract top-level module/package names from a wheel file.

    Returns a sorted list of unique module names.
    """
    modules = set()

    with ZipFile(wheel_path, 'r') as wheel:
        # Look for top_level.txt in the dist-info directory
        for name in wheel.namelist():
            if name.endswith('.dist-info/top_level.txt'):
                content = wheel.read(name).decode('utf-8')
                for line in content.strip().split('\n'):
                    # Wheel contents are untrusted input
                    line = sanitize_input(line.strip())
                    if line:
                        modules.add(line)
                break
        else:
            # Fallback: extract from RECORD file if top_level.txt not found
            for name in wheel.namelist():
                if name.endswith('.dist-info/RECORD'):
                    content = wheel.read(name).decode('utf-8')
                    for line in content.strip().split('\n'):
                        if not line or 'dist-info' in line or '.data/' in line:
                            continue
                        # Get the top-level directory/file name
                        parts = line.split(',')[0].split('/')
                        if parts[0]:
                            # Remove .py extension if it's a single file
                            module_name = parts[0].replace('.py', '')
                            if module_name and not module_name.startswith('__pycache__'):
                                module_name = sanitize_input(module_name)
                                if module_name:
                                    modules.add(module_name)
                    break

    return sorted(modules)


def _extract_scripts_from_wheel(wheel_path: str) -> list[str]:
    """Extract console script names from a wheel file's entry_points.txt.

    Returns a sorted list of unique script names.
    """
    scripts = set()

    with ZipFile(wheel_path, 'r') as wheel:
        # Look for entry_points.txt in the dist-info directory
        for name in wheel.namelist():
            if name.endswith('.dist-info/entry_points.txt'):
                content = wheel.read(name).decode('utf-8')

                # Parse the INI-style entry_points.txt
                config = configparser.ConfigParser()
                config.read_string(content)

                # Extract console_scripts section
                if 'console_scripts' in config:
                    for script_name in config['console_scripts']:
                        script_name = sanitize_input(script_name)
                        if script_name:
                            scripts.add(script_name)
                break

    return sorted(scripts)


def extract_files_from_wheel(wheel_path: str | Path) -> dict[str, list[str]]:
    """Extract modules and scripts from a local wheel file.

    Args:
        wheel_path: Path to a wheel file (local or downloaded)

    Returns:
        Dictionary with 'modules' and 'scripts' keys, each containing a list of names

    Raises:
        WheelNotFoundError: If wheel file doesn't exist or can't be read
    """
    wheel_path = Path(wheel_path)
    if not wheel_path.exists():
        raise WheelNotFoundError(f"Wheel file not found: {wheel_path}")

    modules = _extract_modules_from_wheel(str(wheel_path))
    scripts = _extract_scripts_from_wheel(str(wheel_path))
    inform(f"Extracted {len(modules)} top-level modules and {len(scripts)} scripts from wheel")
    return {"modules": modules, "scripts": scripts}


def download_and_extract_files(
    pypi_pkg_data: dict[Any, Any],
    session: Session | None = None
) -> dict[str, list[str]]:
    """Download a wheel from PyPI and extract modules and scripts.

    Args:
        pypi_pkg_data: PyPI package data dictionary
        session: Optional requests Session for making HTTP requests

    Returns:
        Dictionary with 'modules' and 'scripts' keys, each containing a list of names

    Raises:
        WheelNotFoundError: If no wheel file is available
    """
    wheel_url = _find_wheel_url(pypi_pkg_data)
    if not wheel_url:
        raise WheelNotFoundError(
            f"No wheel file found for package {pypi_pkg_data['info']['name']}"
        )

    _session = session or Session()
    package_name = pypi_pkg_data["info"]["name"]
    version = pypi_pkg_data["info"]["version"]

    inform(f"Downloading wheel for {package_name} {version}...")

    # Download the wheel to a temporary file
    response = _session.get(wheel_url, stream=True)
    if not response.ok:
        raise WheelNotFoundError(
            f"Failed to download wheel from {wheel_url}: {response.status_code}"
        )

    # Save to temporary file using iter_content to handle encoding properly
    with tempfile.NamedTemporaryFile(suffix='.whl', delete=False) as tmp_file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                tmp_file.write(chunk)
        tmp_path = tmp_file.name

    try:
        return extract_files_from_wheel(tmp_path)
    finally:
        # Clean up temporary file
        tmp_path_obj = Path(tmp_path)
        if tmp_path_obj.exists():
            tmp_path_obj.unlink()
