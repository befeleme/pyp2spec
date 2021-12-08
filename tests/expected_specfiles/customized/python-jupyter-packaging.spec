Name:           python-jupyter-packaging
Version:        0.10.4
Release:        2%{?dist}
Summary:        Tools to help build and install Jupyter Python packages

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        BSD
URL:            https://github.com/jupyter/jupyter-packaging
Source0:        %{pypi_source jupyter_packaging}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
This package contains utilities for making Python packages with and without
accompanying JavaScript packages.}


%description %_description

%package -n     python3-jupyter-packaging
Summary:        %{summary}

%description -n python3-jupyter-packaging %_description


%prep
%autosetup -p1 -n jupyter_packaging-%{version}


%generate_buildrequires
%pyproject_buildrequires -x test


%build
%pyproject_wheel


%install
%pyproject_install
# For official Fedora packages, including files with '*' +auto is not allowed
# Replace it with a list of relevant Python modules/globs and list extra files in %%files
%pyproject_save_files '*' +auto


%check
%pyproject_check_import
%pytest -k "not test_build_package and \
not test_create_cmdclass and \
not test_deprecated_metadata and \
not test_develop and \
not test_install and \
not test_install_hybrid and \
not test_run"


%files -n python3-jupyter-packaging -f %{pyproject_files}
%doc README.md
%license LICENSE


%changelog
* Fri Jul 23 2021 Package Maintainer <package@maintainer.com> - 0.10.4-2
- Initial package