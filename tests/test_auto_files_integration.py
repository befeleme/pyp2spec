"""Integration tests for the --auto-files feature.

These tests verify the complete workflow from command-line options
to generated spec file with automatically extracted file lists.

Tests use betamax for recording network requests to avoid online dependencies.
"""

import pytest

from pyp2spec.pyp2conf import create_config_contents
from pyp2spec.conf2spec import ConfigFile, fill_in_template


class TestAutoFilesIntegration:
    """Integration tests for --auto-files feature.

    These tests use betamax cassettes for recorded HTTP interactions.
    """

    def test_config_includes_file_list_when_enabled(self, betamax_session):
        """Test that file_list is included in config when --auto-files is enabled."""
        options = {
            "package": "click",
            "version": "8.1.3",
            "compat": None,
            "path": None,
            "python_alt_version": None,
            "automode": False,
            "fedora_compliant": False,
            "auto_files": True,
        }

        config = create_config_contents(options, session=betamax_session)

        assert "file_list" in config
        assert "click" in config["file_list"]

    def test_config_excludes_file_list_when_disabled(self, betamax_session):
        """Test that file_list is not in config when --auto-files is disabled."""
        options = {
            "package": "click",
            "version": "8.1.3",
            "compat": None,
            "path": None,
            "python_alt_version": None,
            "automode": False,
            "fedora_compliant": False,
            "auto_files": False,
        }

        config = create_config_contents(options, session=betamax_session)

        assert "file_list" not in config

    def test_spec_file_contains_module_names(self, betamax_session):
        """Test that the generated spec file contains actual module names."""
        options = {
            "package": "click",
            "version": "8.1.3",
            "compat": None,
            "path": None,
            "python_alt_version": None,
            "automode": False,
            "fedora_compliant": False,
            "auto_files": True,
        }

        config_contents = create_config_contents(options, session=betamax_session)
        config = ConfigFile(config_contents)
        spec_content = fill_in_template(config, declarative_buildsystem=False)

        # Should contain the module name in pyproject_save_files
        assert "click" in spec_content
        assert "%pyproject_save_files" in spec_content

        # Should have the actual module name, not the placeholder
        assert (
            "%pyproject_save_files click" in spec_content
            or "%pyproject_save_files -l click" in spec_content
        )

    def test_spec_file_uses_placeholder_without_auto_files(self, betamax_session):
        """Test that spec file uses '...' placeholder when --auto-files is not used."""
        options = {
            "package": "click",
            "version": "8.1.3",
            "compat": None,
            "path": None,
            "python_alt_version": None,
            "automode": False,
            "fedora_compliant": False,
            "auto_files": False,
        }

        config_contents = create_config_contents(options, session=betamax_session)
        config = ConfigFile(config_contents)
        spec_content = fill_in_template(config, declarative_buildsystem=False)

        # Should use the placeholder
        assert (
            "%pyproject_save_files ..." in spec_content
            or "%pyproject_save_files -l ..." in spec_content
        )
