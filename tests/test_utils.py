import pytest

from pyp2spec.utils import filter_license_classifiers, prepend_name_with_python
from pyp2spec.utils import normalize_name, get_extras, is_archful
from pyp2spec.utils import normalize_as_wheel_name, archive_name
from pyp2spec.utils import resolve_url, SdistNotFoundError, MissingPackageNameError
from pyp2spec.utils import create_compat_name


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
    assert prepend_name_with_python(normalize_name(pypi_name), alt_version) == expected


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

    assert get_extras([], requires_dist) == ["dev", "docs", "lint", "test"]


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
    assert is_archful(urls) is archful


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
    assert not is_archful(urls)


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
    assert is_archful(urls)



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
    assert is_archful(urls)


@pytest.mark.parametrize(
    ("name", "expected"), [
        ("my-package-foo", "my_package_foo"),
        ("my.package", "my_package"),
        ("my_package-", "my_package_"),
        ("noweirdchars", "noweirdchars"),
    ]
)
def test_normalize_as_wheel_name(name, expected):
    assert normalize_as_wheel_name(name) == expected


def test_empty_package_name_results_in_exception():
    with pytest.raises(MissingPackageNameError):
        normalize_as_wheel_name("")


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
